//! UniLearn Studio desktop shell: typed IPC commands over SQLite, the math sidecar, the optional
//! Claude adapter and safe file export. The webview gets no shell/fs/http capabilities.
mod claude;
mod db;
mod sidecar;

use serde_json::{json, Value};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tauri::{Manager, State};

struct AppState {
    db: Mutex<db::Db>,
    math: Mutex<sidecar::Sidecar>,
    claude: Mutex<claude::ClaudeState>,
    exports: PathBuf,
}

#[tauri::command]
async fn math_call(state: State<'_, Arc<AppState>>, method: String, params: Value) -> Result<Value, String> {
    let st = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || st.math.lock().map_err(|_| "engine lock poisoned".to_string()).map(|mut m| m.call(&method, params)))
        .await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn db(state: State<'_, Arc<AppState>>, op: db::DbOp) -> Result<Value, String> {
    let st = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || { let mut d = st.db.lock().map_err(|_| "db lock poisoned".to_string())?; db::exec(&mut d, op) })
        .await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn claude_status(state: State<'_, Arc<AppState>>, refresh: bool) -> Result<Value, String> {
    let st = state.inner().clone();
    if !refresh { if let Some(s) = st.claude.lock().unwrap().status.clone() { return Ok(s); } }
    let s = tauri::async_runtime::spawn_blocking(claude::status).await.map_err(|e| e.to_string())?;
    st.claude.lock().unwrap().status = Some(s.clone());
    Ok(s)
}

#[tauri::command]
async fn claude_ask(state: State<'_, Arc<AppState>>, req: claude::TutorRequest) -> Result<Value, String> {
    let st = state.inner().clone();
    if st.claude.lock().unwrap().running.is_some() { return Ok(json!({"ok": false, "state": "busy", "error": "มีคำขออื่นกำลังทำงาน"})); }
    let slot = Arc::new(Mutex::new(None));
    let st2 = st.clone();
    let res = tauri::async_runtime::spawn_blocking(move || claude::ask(&req, slot, |s| st2.claude.lock().unwrap().running = Some(s)))
        .await.map_err(|e| e.to_string())?;
    let mut cs = st.claude.lock().unwrap();
    cs.running = None;
    if let Some(state_name) = res["state"].as_str() {
        if state_name != "available" { cs.status = Some(json!({"state": state_name, "message": res["error"]})); }
    }
    Ok(res)
}

#[tauri::command]
fn claude_cancel(state: State<'_, Arc<AppState>>) {
    if let Some(slot) = state.claude.lock().unwrap().running.clone() {
        if let Some(mut c) = slot.lock().unwrap().take() { let _ = c.kill(); let _ = c.wait(); }
    }
}

fn b64decode(s: &str) -> Result<Vec<u8>, String> {
    let mut out = Vec::with_capacity(s.len() * 3 / 4);
    let (mut buf, mut bits) = (0u32, 0u32);
    for ch in s.bytes().filter(|c| !c.is_ascii_whitespace() && *c != b'=') {
        let v = match ch { b'A'..=b'Z' => ch - b'A', b'a'..=b'z' => ch - b'a' + 26, b'0'..=b'9' => ch - b'0' + 52, b'+' => 62, b'/' => 63, _ => return Err("bad base64".into()) } as u32;
        buf = (buf << 6) | v; bits += 6;
        if bits >= 8 { bits -= 8; out.push((buf >> bits) as u8); }
    }
    Ok(out)
}

/// Save an exported file into the user's Downloads/UniLearn Studio folder. Names are sanitized
/// (no path separators, fixed extension allowlist) so the webview cannot write elsewhere.
#[tauri::command]
fn save_export(state: State<'_, Arc<AppState>>, name: String, content: String, base64: bool) -> Result<String, String> {
    let ext = name.rsplit('.').next().unwrap_or("").to_lowercase();
    if !["png", "json"].contains(&ext.as_str()) { return Err("unsupported file type".into()); }
    let stem: String = name.chars().filter(|c| c.is_ascii_alphanumeric() || matches!(c, '-' | '_' | '.')).take(80).collect();
    if stem.starts_with('.') || stem.contains("..") || stem.is_empty() { return Err("bad file name".into()); }
    let bytes = if base64 { b64decode(content.split(',').last().unwrap_or(""))? } else { content.into_bytes() };
    if bytes.len() > 50_000_000 { return Err("file too large".into()); }
    std::fs::create_dir_all(&state.exports).map_err(|e| e.to_string())?;
    let path = state.exports.join(stem);
    std::fs::write(&path, bytes).map_err(|e| e.to_string())?;
    Ok(path.display().to_string())
}

fn engine_launch(app: &tauri::App) -> sidecar::Launch {
    if let Ok(res) = app.path().resource_dir() {
        let exe = res.join("math-engine").join("unilearn-math.exe");
        if exe.is_file() { return sidecar::Launch { program: exe, args: vec![], cwd: Some(res.join("math-engine")) }; }
    }
    // development fallback: the repository virtualenv
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../services/math-engine");
    let py = std::env::var_os("UNILEARN_PYTHON").map(PathBuf::from).unwrap_or_else(|| root.join(".venv/Scripts/python.exe"));
    sidecar::Launch { program: py, args: vec!["-X".into(), "utf8".into(), "-m".into(), "unilearn_math.server".into()], cwd: Some(root) }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
            let database = db::Db::open(&data)?;
            let exports = app.path().download_dir().unwrap_or_else(|_| data.clone()).join("UniLearn Studio");
            let launch = engine_launch(app);
            let state = Arc::new(AppState { db: Mutex::new(database), math: Mutex::new(sidecar::Sidecar::new(launch)), claude: Mutex::new(Default::default()), exports });
            // warm the engine in the background so the first problem appears quickly
            let warm = state.clone();
            std::thread::spawn(move || { let _ = warm.math.lock().map(|mut m| m.call("ping", json!({}))); });
            app.manage(state);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![math_call, db, claude_status, claude_ask, claude_cancel, save_export])
        .run(tauri::generate_context!())
        .expect("error while running UniLearn Studio");
}

#[cfg(test)]
mod tests {
    #[test]
    fn base64_roundtrip() {
        assert_eq!(super::b64decode("aGVsbG8=").unwrap(), b"hello");
        assert!(super::b64decode("@@").is_err());
    }
}
