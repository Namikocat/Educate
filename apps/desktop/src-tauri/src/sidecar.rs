//! Math-engine sidecar: one long-lived child process speaking JSON lines over stdio.
//! Each request has a timeout; on timeout or crash the process is killed and restarted, so a
//! pathological expression can never block the UI.
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::mpsc::{channel, Receiver, RecvTimeoutError};
use std::time::Duration;

#[cfg(windows)]
use std::os::windows::process::CommandExt;
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

pub struct Launch {
    pub program: PathBuf,
    pub args: Vec<String>,
    pub cwd: Option<PathBuf>,
}

struct Proc {
    child: Child,
    stdin: ChildStdin,
    rx: Receiver<String>,
}

pub struct Sidecar {
    launch: Launch,
    proc_: Option<Proc>,
    next_id: u64,
    pub restarts: u32,
}

const ALLOWED: &[&str] = &["ping", "list_templates", "generate", "generate_for_section", "check", "reveal", "preview", "exam", "coverage"];

fn timeout_for(method: &str) -> Duration {
    Duration::from_secs(match method { "exam" => 90, "generate" | "generate_for_section" | "reveal" => 30, "ping" => 60, _ => 15 })
}

impl Sidecar {
    pub fn new(launch: Launch) -> Self {
        Sidecar { launch, proc_: None, next_id: 1, restarts: 0 }
    }

    fn spawn(&mut self) -> Result<(), String> {
        let mut cmd = Command::new(&self.launch.program);
        cmd.args(&self.launch.args).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
        cmd.env("PYTHONIOENCODING", "utf-8").env("PYTHONUTF8", "1");
        if let Some(d) = &self.launch.cwd { cmd.current_dir(d); }
        #[cfg(windows)]
        cmd.creation_flags(CREATE_NO_WINDOW);
        let mut child = cmd.spawn().map_err(|e| format!("cannot start math engine ({}): {e}", self.launch.program.display()))?;
        let stdin = child.stdin.take().ok_or("no stdin")?;
        let stdout = child.stdout.take().ok_or("no stdout")?;
        let (tx, rx) = channel();
        std::thread::spawn(move || {
            for line in BufReader::new(stdout).lines() {
                match line { Ok(l) => { if tx.send(l).is_err() { break; } } Err(_) => break }
            }
        });
        // wait for the ready banner (first start may unpack/import SymPy)
        match rx.recv_timeout(Duration::from_secs(90)) {
            Ok(l) if l.contains("\"ready\"") => {}
            Ok(l) => return Err(format!("unexpected engine banner: {l}")),
            Err(_) => { let _ = child.kill(); return Err("math engine did not start in time".into()); }
        }
        self.proc_ = Some(Proc { child, stdin, rx });
        Ok(())
    }

    fn kill(&mut self) {
        if let Some(mut p) = self.proc_.take() { let _ = p.child.kill(); let _ = p.child.wait(); }
    }

    pub fn call(&mut self, method: &str, params: Value) -> Value {
        if !ALLOWED.contains(&method) {
            return json!({"ok": false, "error": {"code": "unknown_method", "message": method}});
        }
        match self.try_call(method, &params) {
            Ok(v) => v,
            Err(msg) => json!({"ok": false, "error": {"code": "engine", "message": msg}}),
        }
    }

    fn try_call(&mut self, method: &str, params: &Value) -> Result<Value, String> {
        for attempt in 0..2 {
            if self.proc_.is_none() { self.spawn()?; }
            let id = self.next_id; self.next_id += 1;
            let line = json!({"id": id, "method": method, "params": params}).to_string();
            if line.len() > 60_000 { return Err("request too large".into()); }
            let p = self.proc_.as_mut().unwrap();
            if writeln!(p.stdin, "{line}").and_then(|_| p.stdin.flush()).is_err() {
                self.kill(); self.restarts += 1; continue;
            }
            let deadline = std::time::Instant::now() + timeout_for(method);
            loop {
                let left = deadline.saturating_duration_since(std::time::Instant::now());
                match self.proc_.as_ref().unwrap().rx.recv_timeout(left) {
                    Ok(resp) => {
                        let v: Value = serde_json::from_str(&resp).map_err(|_| "engine sent invalid JSON".to_string())?;
                        if v["id"].as_u64() == Some(id) { return Ok(v); }
                        // stale reply from a request that already timed out: ignore
                    }
                    Err(RecvTimeoutError::Timeout) => {
                        self.kill(); self.restarts += 1;
                        return Err(format!("การคำนวณใช้เวลานานเกินกำหนด ({}) จึงถูกยกเลิก", method));
                    }
                    Err(RecvTimeoutError::Disconnected) => { self.kill(); self.restarts += 1; break; }
                }
            }
            if attempt == 1 { break; }
        }
        Err("math engine stopped unexpectedly".into())
    }
}

impl Drop for Sidecar {
    fn drop(&mut self) { self.kill(); }
}
