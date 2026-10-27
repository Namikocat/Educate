//! Local SQLite store: migrations, typed operations, backups, export/import, corruption handling.
use rusqlite::{params, Connection, OptionalExtension};
use serde::Deserialize;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

const MIGRATIONS: &[(&str, &str)] = &[
    ("001_initial", r#"
CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 60), created_at INTEGER NOT NULL);
CREATE TABLE settings (profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE, data TEXT NOT NULL, PRIMARY KEY(profile_id));
CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE content_versions (subject TEXT PRIMARY KEY, version TEXT NOT NULL, loaded_at INTEGER NOT NULL);
CREATE TABLE lesson_progress (profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE, section TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('started','completed')), updated_at INTEGER NOT NULL, PRIMARY KEY(profile_id, section));
CREATE TABLE notes (id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE, section TEXT NOT NULL,
  body TEXT NOT NULL CHECK(length(body) <= 20000), created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
CREATE INDEX notes_section ON notes(profile_id, section);
CREATE TABLE bookmarks (profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE, section TEXT NOT NULL, created_at INTEGER NOT NULL,
  PRIMARY KEY(profile_id, section));
-- reproducible generation metadata only; problems are regenerated from template+version+seed+difficulty
CREATE TABLE problem_instances (id TEXT PRIMARY KEY, template_id TEXT NOT NULL, template_version TEXT NOT NULL, seed INTEGER NOT NULL,
  difficulty INTEGER NOT NULL, canonical TEXT NOT NULL, section TEXT NOT NULL);
CREATE TABLE attempts (id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  problem_id TEXT NOT NULL REFERENCES problem_instances(id), section TEXT NOT NULL, template_id TEXT NOT NULL, difficulty INTEGER NOT NULL,
  correct INTEGER NOT NULL, hints_used INTEGER NOT NULL DEFAULT 0, solution_revealed INTEGER NOT NULL DEFAULT 0, error_type TEXT,
  time_ms INTEGER NOT NULL DEFAULT 0, answer TEXT, at INTEGER NOT NULL);
CREATE INDEX attempts_section ON attempts(profile_id, section, at);
CREATE INDEX attempts_at ON attempts(profile_id, at);
CREATE TABLE exams (id TEXT PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE, title TEXT NOT NULL,
  data TEXT NOT NULL, started_at INTEGER NOT NULL, submitted_at INTEGER, score REAL);
CREATE TABLE mastery_history (id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  section TEXT NOT NULL, mastery REAL NOT NULL, at INTEGER NOT NULL);
CREATE TABLE study_sessions (id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  started_at INTEGER NOT NULL, ended_at INTEGER NOT NULL, activity TEXT NOT NULL);
CREATE TABLE ai_conversations (id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_at INTEGER NOT NULL, request TEXT NOT NULL, response TEXT NOT NULL);
"#),
];

pub fn now_ms() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_millis() as i64).unwrap_or(0)
}

pub struct Db {
    pub conn: Connection,
    pub path: PathBuf,
    pub notice: Option<String>,
}

fn configure(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=3000;")
}

fn migrate(conn: &mut Connection) -> rusqlite::Result<()> {
    conn.execute_batch("CREATE TABLE IF NOT EXISTS schema_migrations (id TEXT PRIMARY KEY, applied_at INTEGER NOT NULL);")?;
    for (id, sql) in MIGRATIONS {
        let done: Option<String> = conn.query_row("SELECT id FROM schema_migrations WHERE id=?1", [id], |r| r.get(0)).optional()?;
        if done.is_none() {
            let tx = conn.transaction()?;
            tx.execute_batch(sql)?;
            tx.execute("INSERT INTO schema_migrations(id, applied_at) VALUES(?1, ?2)", params![id, now_ms()])?;
            tx.commit()?;
        }
    }
    Ok(())
}

impl Db {
    /// Open (or create) the database. A corrupt file is moved aside and a fresh one is created.
    pub fn open(dir: &Path) -> Result<Db, String> {
        std::fs::create_dir_all(dir).map_err(|e| e.to_string())?;
        let path = dir.join("unilearn.db");
        let mut notice = None;
        let healthy = match Connection::open(&path) {
            Ok(c) => c.query_row("PRAGMA integrity_check", [], |r| r.get::<_, String>(0)).map(|s| s == "ok").unwrap_or(false),
            Err(_) => false,
        };
        if !healthy && path.exists() {
            let aside = dir.join(format!("unilearn.corrupt-{}.db", now_ms()));
            let _ = std::fs::rename(&path, &aside);
            notice = Some(format!("พบไฟล์ฐานข้อมูลเสียหาย ย้ายไปที่ {} และสร้างฐานข้อมูลใหม่", aside.display()));
        }
        let mut conn = Connection::open(&path).map_err(|e| e.to_string())?;
        configure(&conn).map_err(|e| e.to_string())?;
        migrate(&mut conn).map_err(|e| format!("migration failed: {e}"))?;
        let db = Db { conn, path, notice };
        db.daily_backup();
        Ok(db)
    }

    fn backup_dir(&self) -> PathBuf {
        self.path.parent().unwrap().join("backups")
    }

    /// Consistent online copy via VACUUM INTO; keeps the 7 newest.
    pub fn backup(&self, tag: &str) -> Result<PathBuf, String> {
        let dir = self.backup_dir();
        std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
        let file = dir.join(format!("unilearn-{tag}-{}.db", now_ms()));
        self.conn.execute("VACUUM INTO ?1", [file.to_string_lossy()]).map_err(|e| e.to_string())?;
        let mut files: Vec<_> = std::fs::read_dir(&dir).map_err(|e| e.to_string())?.filter_map(|e| e.ok()).map(|e| e.path()).collect();
        files.sort();
        while files.len() > 7 {
            let _ = std::fs::remove_file(files.remove(0));
        }
        Ok(file)
    }

    fn daily_backup(&self) {
        let day = now_ms() / 86_400_000;
        let last: Option<String> = self.conn.query_row("SELECT value FROM kv WHERE key='last_backup_day'", [], |r| r.get(0)).optional().ok().flatten();
        if last.as_deref() != Some(&day.to_string()) && self.profile_id().is_some() && self.backup("daily").is_ok() {
            let _ = self.conn.execute("INSERT OR REPLACE INTO kv(key, value) VALUES('last_backup_day', ?1)", [day.to_string()]);
        }
    }

    fn profile_id(&self) -> Option<i64> {
        self.conn.query_row("SELECT id FROM profiles ORDER BY id LIMIT 1", [], |r| r.get(0)).optional().ok().flatten()
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Attempt {
    section: String,
    template_id: String,
    difficulty: i64,
    correct: bool,
    hints_used: i64,
    solution_revealed: bool,
    error_type: Option<String>,
    time_ms: i64,
    at: i64,
    problem_id: String,
    canonical: String,
    answer: String,
}

#[derive(Deserialize)]
#[serde(tag = "op", rename_all = "snake_case")]
pub enum DbOp {
    GetProfile,
    CreateProfile { name: String },
    RecordAttempt { attempt: Attempt },
    ListAttempts { limit: Option<i64> },
    SetLesson { section: String, status: String },
    LessonProgress,
    ListNotes,
    SaveNote { id: Option<i64>, section: String, body: String },
    DeleteNote { id: i64 },
    ListBookmarks,
    ToggleBookmark { section: String },
    GetSettings,
    SetSettings { settings: Value },
    SaveExam { exam: Value },
    ListExams,
    SetKv { key: String, value: String },
    GetKv { key: String },
    LogSession { #[serde(rename = "startedAt")] started_at: i64, #[serde(rename = "endedAt")] ended_at: i64, activity: String },
    ListSessions,
    Export,
    Import { data: String },
    Backup,
    SaveConversation { request: Value, response: String },
    ListConversations { limit: Option<i64> },
    DeleteConversation { id: i64 },
    ClearConversations,
}

fn check_section(s: &str) -> Result<(), String> {
    if s.is_empty() || s.len() > 32 || !s.chars().all(|c| c.is_ascii_alphanumeric() || c == '.' || c == '-') {
        return Err("invalid section id".into());
    }
    Ok(())
}

const TABLES: &[&str] = &["profiles", "settings", "kv", "lesson_progress", "notes", "bookmarks", "problem_instances", "attempts", "exams",
    "mastery_history", "study_sessions", "ai_conversations"];

pub fn exec(db: &mut Db, op: DbOp) -> Result<Value, String> {
    let e = |x: rusqlite::Error| x.to_string();
    let pid = db.profile_id();
    let need = || pid.ok_or_else(|| "no profile".to_string());
    let c = &db.conn;
    Ok(match op {
        DbOp::GetProfile => c.query_row("SELECT id, name, created_at FROM profiles ORDER BY id LIMIT 1", [], |r| {
            Ok(json!({"id": r.get::<_, i64>(0)?, "name": r.get::<_, String>(1)?, "createdAt": r.get::<_, i64>(2)?}))
        }).optional().map_err(e)?.unwrap_or(Value::Null),
        DbOp::CreateProfile { name } => {
            let name = name.trim().chars().take(60).collect::<String>();
            if name.is_empty() { return Err("name required".into()); }
            if let Some(id) = pid { return Ok(json!({"id": id, "name": name, "createdAt": now_ms()})); }
            c.execute("INSERT INTO profiles(name, created_at) VALUES(?1, ?2)", params![name, now_ms()]).map_err(e)?;
            json!({"id": c.last_insert_rowid(), "name": name, "createdAt": now_ms()})
        }
        DbOp::RecordAttempt { attempt: a } => {
            let p = need()?;
            check_section(&a.section)?;
            if !(1..=3).contains(&a.difficulty) { return Err("bad difficulty".into()); }
            // problem id format: template@version#seed.difficulty (from the engine)
            let (tid_ver, rest) = a.problem_id.split_once('#').ok_or("bad problem id")?;
            let (_, ver) = tid_ver.split_once('@').ok_or("bad problem id")?;
            let seed: i64 = rest.split('.').next().and_then(|s| s.parse().ok()).ok_or("bad problem id")?;
            let tx = db.conn.transaction().map_err(e)?;
            tx.execute("INSERT OR IGNORE INTO problem_instances(id, template_id, template_version, seed, difficulty, canonical, section) VALUES(?1,?2,?3,?4,?5,?6,?7)",
                params![a.problem_id, a.template_id, ver, seed, a.difficulty, a.canonical, a.section]).map_err(e)?;
            tx.execute("INSERT INTO attempts(profile_id, problem_id, section, template_id, difficulty, correct, hints_used, solution_revealed, error_type, time_ms, answer, at)
                VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12)",
                params![p, a.problem_id, a.section, a.template_id, a.difficulty, a.correct, a.hints_used.clamp(0, 50), a.solution_revealed, a.error_type,
                    a.time_ms.clamp(0, 86_400_000), a.answer.chars().take(400).collect::<String>(), a.at]).map_err(e)?;
            tx.commit().map_err(e)?;
            Value::Null
        }
        DbOp::ListAttempts { limit } => {
            let p = need()?;
            let mut st = c.prepare("SELECT a.section, a.template_id, a.difficulty, a.correct, a.hints_used, a.solution_revealed, a.error_type, a.time_ms, a.at, a.problem_id, p.canonical
                FROM attempts a JOIN problem_instances p ON p.id = a.problem_id WHERE a.profile_id=?1 ORDER BY a.at DESC LIMIT ?2").map_err(e)?;
            let rows = st.query_map(params![p, limit.unwrap_or(5000).clamp(1, 20000)], |r| Ok(json!({
                "section": r.get::<_, String>(0)?, "templateId": r.get::<_, String>(1)?, "difficulty": r.get::<_, i64>(2)?, "correct": r.get::<_, bool>(3)?,
                "hintsUsed": r.get::<_, i64>(4)?, "solutionRevealed": r.get::<_, bool>(5)?, "errorType": r.get::<_, Option<String>>(6)?,
                "timeMs": r.get::<_, i64>(7)?, "at": r.get::<_, i64>(8)?, "problemId": r.get::<_, String>(9)?, "canonical": r.get::<_, String>(10)?})))
                .map_err(e)?.collect::<Result<Vec<_>, _>>().map_err(e)?;
            let mut rows = rows; rows.reverse();
            Value::Array(rows)
        }
        DbOp::SetLesson { section, status } => {
            let p = need()?; check_section(&section)?;
            if status != "started" && status != "completed" { return Err("bad status".into()); }
            c.execute("INSERT INTO lesson_progress(profile_id, section, status, updated_at) VALUES(?1,?2,?3,?4)
                ON CONFLICT(profile_id, section) DO UPDATE SET status = CASE WHEN lesson_progress.status='completed' THEN 'completed' ELSE excluded.status END, updated_at=excluded.updated_at",
                params![p, section, status, now_ms()]).map_err(e)?;
            Value::Null
        }
        DbOp::LessonProgress => {
            let p = need()?;
            let mut st = c.prepare("SELECT section, status, updated_at FROM lesson_progress WHERE profile_id=?1").map_err(e)?;
            let mut m = serde_json::Map::new();
            for r in st.query_map([p], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?, r.get::<_, i64>(2)?))).map_err(e)? {
                let (s, stt, u) = r.map_err(e)?;
                m.insert(s, json!({"status": stt, "updatedAt": u}));
            }
            Value::Object(m)
        }
        DbOp::ListNotes => {
            let p = need()?;
            let mut st = c.prepare("SELECT id, section, body, updated_at FROM notes WHERE profile_id=?1 ORDER BY updated_at DESC").map_err(e)?;
            let v = st.query_map([p], |r| Ok(json!({"id": r.get::<_, i64>(0)?, "section": r.get::<_, String>(1)?, "body": r.get::<_, String>(2)?, "updatedAt": r.get::<_, i64>(3)?})))
                .map_err(e)?.collect::<Result<Vec<_>, _>>().map_err(e)?;
            Value::Array(v)
        }
        DbOp::SaveNote { id, section, body } => {
            let p = need()?; check_section(&section)?;
            let body: String = body.chars().take(20000).collect();
            match id {
                Some(id) => { c.execute("UPDATE notes SET body=?1, updated_at=?2 WHERE id=?3 AND profile_id=?4", params![body, now_ms(), id, p]).map_err(e)?; }
                None => { c.execute("INSERT INTO notes(profile_id, section, body, created_at, updated_at) VALUES(?1,?2,?3,?4,?4)", params![p, section, body, now_ms()]).map_err(e)?; }
            }
            Value::Null
        }
        DbOp::DeleteNote { id } => { let p = need()?; c.execute("DELETE FROM notes WHERE id=?1 AND profile_id=?2", params![id, p]).map_err(e)?; Value::Null }
        DbOp::ListBookmarks => {
            let p = need()?;
            let mut st = c.prepare("SELECT section, created_at FROM bookmarks WHERE profile_id=?1 ORDER BY section").map_err(e)?;
            let v = st.query_map([p], |r| Ok(json!({"section": r.get::<_, String>(0)?, "createdAt": r.get::<_, i64>(1)?}))).map_err(e)?.collect::<Result<Vec<_>, _>>().map_err(e)?;
            Value::Array(v)
        }
        DbOp::ToggleBookmark { section } => {
            let p = need()?; check_section(&section)?;
            if c.execute("DELETE FROM bookmarks WHERE profile_id=?1 AND section=?2", params![p, section]).map_err(e)? == 0 {
                c.execute("INSERT INTO bookmarks(profile_id, section, created_at) VALUES(?1,?2,?3)", params![p, section, now_ms()]).map_err(e)?;
            }
            Value::Null
        }
        DbOp::GetSettings => match pid {
            None => Value::Null,
            Some(p) => c.query_row("SELECT data FROM settings WHERE profile_id=?1", [p], |r| r.get::<_, String>(0)).optional().map_err(e)?
                .and_then(|s| serde_json::from_str(&s).ok()).unwrap_or(Value::Null),
        },
        DbOp::SetSettings { settings } => {
            let p = need()?;
            if !settings.is_object() { return Err("settings must be an object".into()); }
            c.execute("INSERT OR REPLACE INTO settings(profile_id, data) VALUES(?1, ?2)", params![p, settings.to_string()]).map_err(e)?;
            Value::Null
        }
        DbOp::SaveExam { exam } => {
            let p = need()?;
            let id = exam["id"].as_str().ok_or("exam.id")?.to_string();
            let data = exam.to_string();
            if data.len() > 2_000_000 { return Err("exam too large".into()); }
            c.execute("INSERT OR REPLACE INTO exams(id, profile_id, title, data, started_at, submitted_at, score) VALUES(?1,?2,?3,?4,?5,?6,?7)",
                params![id, p, exam["title"].as_str().unwrap_or(""), data, exam["startedAt"].as_i64().unwrap_or(0), exam["submittedAt"].as_i64(), exam["score"].as_f64()]).map_err(e)?;
            Value::Null
        }
        DbOp::ListExams => {
            let p = need()?;
            let mut st = c.prepare("SELECT data FROM exams WHERE profile_id=?1 ORDER BY started_at").map_err(e)?;
            let v = st.query_map([p], |r| r.get::<_, String>(0)).map_err(e)?.filter_map(|r| r.ok()).filter_map(|s| serde_json::from_str::<Value>(&s).ok()).collect();
            Value::Array(v)
        }
        DbOp::SetKv { key, value } => {
            if key.len() > 64 || value.len() > 100_000 { return Err("kv too large".into()); }
            c.execute("INSERT OR REPLACE INTO kv(key, value) VALUES(?1, ?2)", params![key, value]).map_err(e)?;
            Value::Null
        }
        DbOp::GetKv { key } => c.query_row("SELECT value FROM kv WHERE key=?1", [key], |r| r.get::<_, String>(0)).optional().map_err(e)?.map(Value::String).unwrap_or(Value::Null),
        DbOp::LogSession { started_at, ended_at, activity } => {
            if let Some(p) = pid {
                if ended_at - started_at > 2_000 {
                    c.execute("INSERT INTO study_sessions(profile_id, started_at, ended_at, activity) VALUES(?1,?2,?3,?4)",
                        params![p, started_at, ended_at, activity.chars().take(32).collect::<String>()]).map_err(e)?;
                }
            }
            Value::Null
        }
        DbOp::ListSessions => {
            let p = need()?;
            let mut st = c.prepare("SELECT started_at, ended_at, activity FROM study_sessions WHERE profile_id=?1 ORDER BY started_at DESC LIMIT 2000").map_err(e)?;
            let v = st.query_map([p], |r| Ok(json!({"startedAt": r.get::<_, i64>(0)?, "endedAt": r.get::<_, i64>(1)?, "activity": r.get::<_, String>(2)?})))
                .map_err(e)?.collect::<Result<Vec<_>, _>>().map_err(e)?;
            Value::Array(v)
        }
        DbOp::Export => Value::String(export(c)?.to_string()),
        DbOp::Import { data } => {
            if data.len() > 50_000_000 { return Err("import too large".into()); }
            let v: Value = serde_json::from_str(&data).map_err(|_| "ไฟล์สำรองไม่ใช่ JSON".to_string())?;
            if v["format"] != "unilearn-backup" || v["version"] != 1 { return Err("ไฟล์สำรองไม่ถูกต้องหรือไม่รองรับเวอร์ชันนี้".into()); }
            db.backup("pre-import")?;
            import(&mut db.conn, &v["tables"])?;
            Value::Null
        }
        DbOp::Backup => Value::String(db.path.display().to_string()),
        DbOp::SaveConversation { request, response } => {
            let p = need()?;
            let req = request.to_string();
            if req.len() > 50_000 || response.len() > 60_000 { return Err("conversation too large".into()); }
            c.execute("INSERT INTO ai_conversations(profile_id, created_at, request, response) VALUES(?1,?2,?3,?4)", params![p, now_ms(), req, response]).map_err(e)?;
            json!(c.last_insert_rowid())
        }
        DbOp::ListConversations { limit } => {
            let p = need()?;
            let mut st = c.prepare("SELECT id, created_at, request, response FROM ai_conversations WHERE profile_id=?1 ORDER BY created_at DESC, id DESC LIMIT ?2").map_err(e)?;
            let v = st.query_map(params![p, limit.unwrap_or(200).clamp(1, 1000)], |r| Ok(json!({"id": r.get::<_, i64>(0)?, "createdAt": r.get::<_, i64>(1)?,
                "request": serde_json::from_str::<Value>(&r.get::<_, String>(2)?).unwrap_or(Value::Null), "response": r.get::<_, String>(3)?})))
                .map_err(e)?.collect::<Result<Vec<_>, _>>().map_err(e)?;
            Value::Array(v)
        }
        DbOp::DeleteConversation { id } => { let p = need()?; c.execute("DELETE FROM ai_conversations WHERE id=?1 AND profile_id=?2", params![id, p]).map_err(e)?; Value::Null }
        DbOp::ClearConversations => { let p = need()?; c.execute("DELETE FROM ai_conversations WHERE profile_id=?1", [p]).map_err(e)?; Value::Null }
    })
}

fn export(c: &Connection) -> Result<Value, String> {
    let mut tables = serde_json::Map::new();
    for t in TABLES {
        let mut st = c.prepare(&format!("SELECT * FROM {t}")).map_err(|e| e.to_string())?;
        let cols: Vec<String> = st.column_names().iter().map(|s| s.to_string()).collect();
        let rows = st.query_map([], |r| {
            let mut o = serde_json::Map::new();
            for (i, col) in cols.iter().enumerate() {
                let v = match r.get_ref(i)? {
                    rusqlite::types::ValueRef::Null => Value::Null,
                    rusqlite::types::ValueRef::Integer(n) => json!(n),
                    rusqlite::types::ValueRef::Real(f) => json!(f),
                    rusqlite::types::ValueRef::Text(t) => json!(String::from_utf8_lossy(t)),
                    rusqlite::types::ValueRef::Blob(_) => Value::Null,
                };
                o.insert(col.clone(), v);
            }
            Ok(Value::Object(o))
        }).map_err(|e| e.to_string())?.collect::<Result<Vec<_>, _>>().map_err(|e| e.to_string())?;
        tables.insert(t.to_string(), Value::Array(rows));
    }
    Ok(json!({"format": "unilearn-backup", "version": 1, "exportedAt": now_ms(), "tables": tables}))
}

/// Replace all user data inside one transaction; column names are validated against the live schema.
fn import(conn: &mut Connection, tables: &Value) -> Result<(), String> {
    let e = |x: rusqlite::Error| x.to_string();
    let tx = conn.transaction().map_err(e)?;
    for t in TABLES.iter().rev() { tx.execute(&format!("DELETE FROM {t}"), []).map_err(e)?; }
    for t in TABLES {
        let cols: Vec<String> = { let mut st = tx.prepare(&format!("SELECT * FROM {t} LIMIT 0")).map_err(e)?; st.column_names().iter().map(|s| s.to_string()).collect() };
        for row in tables[*t].as_array().cloned().unwrap_or_default() {
            let obj = row.as_object().ok_or("bad row")?;
            let keys: Vec<&String> = obj.keys().filter(|k| cols.contains(k)).collect();
            if keys.is_empty() { continue; }
            let sql = format!("INSERT INTO {t} ({}) VALUES ({})", keys.iter().map(|k| k.as_str()).collect::<Vec<_>>().join(","), (1..=keys.len()).map(|i| format!("?{i}")).collect::<Vec<_>>().join(","));
            let vals: Vec<rusqlite::types::Value> = keys.iter().map(|k| match &obj[*k] {
                Value::Null => rusqlite::types::Value::Null,
                Value::Bool(b) => rusqlite::types::Value::Integer(*b as i64),
                Value::Number(n) => n.as_i64().map(rusqlite::types::Value::Integer).unwrap_or_else(|| rusqlite::types::Value::Real(n.as_f64().unwrap_or(0.0))),
                Value::String(s) => rusqlite::types::Value::Text(s.clone()),
                other => rusqlite::types::Value::Text(other.to_string()),
            }).collect();
            tx.execute(&sql, rusqlite::params_from_iter(vals)).map_err(e)?;
        }
    }
    tx.commit().map_err(e)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp() -> PathBuf {
        static N: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
        let n = N.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        let d = std::env::temp_dir().join(format!("unilearn-test-{}-{}-{n}", std::process::id(), now_ms()));
        std::fs::create_dir_all(&d).unwrap();
        d
    }

    #[test]
    fn migrations_profile_attempts_roundtrip() {
        let dir = tmp();
        let mut db = Db::open(&dir).unwrap();
        exec(&mut db, DbOp::CreateProfile { name: "Test".into() }).unwrap();
        let a: Attempt = serde_json::from_value(json!({"section": "5.5", "templateId": "calc.5.5.x", "difficulty": 2, "correct": true, "hintsUsed": 1,
            "solutionRevealed": false, "errorType": null, "timeMs": 1000, "at": 1, "problemId": "calc.5.5.x@1.0.0#42.2", "canonical": "abc", "answer": "x"})).unwrap();
        exec(&mut db, DbOp::RecordAttempt { attempt: a }).unwrap();
        let list = exec(&mut db, DbOp::ListAttempts { limit: None }).unwrap();
        assert_eq!(list.as_array().unwrap().len(), 1);
        assert_eq!(list[0]["canonical"], "abc");
        exec(&mut db, DbOp::SetLesson { section: "5.5".into(), status: "completed".into() }).unwrap();
        exec(&mut db, DbOp::SetLesson { section: "5.5".into(), status: "started".into() }).unwrap();
        assert_eq!(exec(&mut db, DbOp::LessonProgress).unwrap()["5.5"]["status"], "completed");
        // export -> import restores data
        let dump = exec(&mut db, DbOp::Export).unwrap();
        exec(&mut db, DbOp::ToggleBookmark { section: "6.1".into() }).unwrap();
        exec(&mut db, DbOp::Import { data: dump.as_str().unwrap().to_string() }).unwrap();
        assert_eq!(exec(&mut db, DbOp::ListBookmarks).unwrap().as_array().unwrap().len(), 0);
        assert_eq!(exec(&mut db, DbOp::ListAttempts { limit: None }).unwrap().as_array().unwrap().len(), 1);
        // reopening applies no migration twice
        drop(db);
        let db2 = Db::open(&dir).unwrap();
        let n: i64 = db2.conn.query_row("SELECT count(*) FROM schema_migrations", [], |r| r.get(0)).unwrap();
        assert_eq!(n, 1);
    }

    #[test]
    fn conversation_history() {
        let mut db = Db::open(&tmp()).unwrap();
        exec(&mut db, DbOp::CreateProfile { name: "T".into() }).unwrap();
        let id = exec(&mut db, DbOp::SaveConversation { request: json!({"question": "q1"}), response: "a1".into() }).unwrap().as_i64().unwrap();
        exec(&mut db, DbOp::SaveConversation { request: json!({"question": "q2"}), response: "a2".into() }).unwrap();
        let l = exec(&mut db, DbOp::ListConversations { limit: None }).unwrap();
        assert_eq!(l.as_array().unwrap().len(), 2);
        assert_eq!(l[0]["request"]["question"], "q2");
        exec(&mut db, DbOp::DeleteConversation { id }).unwrap();
        assert_eq!(exec(&mut db, DbOp::ListConversations { limit: None }).unwrap().as_array().unwrap().len(), 1);
        exec(&mut db, DbOp::ClearConversations).unwrap();
        assert_eq!(exec(&mut db, DbOp::ListConversations { limit: None }).unwrap().as_array().unwrap().len(), 0);
    }

    #[test]
    fn rejects_bad_input() {
        let dir = tmp();
        let mut db = Db::open(&dir).unwrap();
        exec(&mut db, DbOp::CreateProfile { name: "T".into() }).unwrap();
        assert!(exec(&mut db, DbOp::SetLesson { section: "../etc".into(), status: "started".into() }).is_err());
        assert!(exec(&mut db, DbOp::Import { data: "{\"format\":\"other\"}".into() }).is_err());
    }

    #[test]
    fn corrupt_database_is_moved_aside() {
        let dir = tmp();
        std::fs::write(dir.join("unilearn.db"), b"this is not a sqlite database at all..................").unwrap();
        let db = Db::open(&dir).unwrap();
        assert!(db.notice.is_some());
    }
}
