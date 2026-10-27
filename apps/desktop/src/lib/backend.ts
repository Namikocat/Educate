/**
 * Backend adapter. In the desktop app every call goes through typed Tauri commands
 * (Rust owns SQLite, the math sidecar and the Claude CLI). In a plain browser (developer
 * preview only) the same interface is served by the engine's localhost HTTP bridge and
 * localStorage, so UI work can be tested without the native shell.
 */
import type { AttemptRecord, Bookmark, ClaudeStatus, ExamSession, Note, Profile, Settings, TutorRequest, TutorResponse } from "./types";

export type DbOp =
  | { op: "get_profile" }
  | { op: "create_profile"; name: string }
  | { op: "record_attempt"; attempt: AttemptRecord & { problemId: string; canonical: string; answer: string } }
  | { op: "list_attempts"; limit?: number }
  | { op: "set_lesson"; section: string; status: "started" | "completed" }
  | { op: "lesson_progress" }
  | { op: "list_notes" }
  | { op: "save_note"; id?: number; section: string; body: string }
  | { op: "delete_note"; id: number }
  | { op: "list_bookmarks" }
  | { op: "toggle_bookmark"; section: string }
  | { op: "get_settings" }
  | { op: "set_settings"; settings: Settings }
  | { op: "save_exam"; exam: ExamSession }
  | { op: "list_exams" }
  | { op: "set_kv"; key: string; value: string }
  | { op: "get_kv"; key: string }
  | { op: "log_session"; startedAt: number; endedAt: number; activity: string }
  | { op: "list_sessions" }
  | { op: "export" }
  | { op: "import"; data: string }
  | { op: "backup" }
  | { op: "save_conversation"; request: Record<string, unknown>; response: string }
  | { op: "list_conversations"; limit?: number }
  | { op: "delete_conversation"; id: number }
  | { op: "clear_conversations" };

export interface Backend {
  kind: "tauri" | "dev";
  math<T = unknown>(method: string, params?: Record<string, unknown>): Promise<T>;
  db<T = unknown>(op: DbOp): Promise<T>;
  claudeStatus(refresh?: boolean): Promise<ClaudeStatus>;
  claudeAsk(req: TutorRequest): Promise<TutorResponse>;
  claudeCancel(): Promise<void>;
  /** Save an export (PNG data URL or JSON text). Returns where it was saved. */
  saveFile(name: string, content: string, base64: boolean): Promise<string>;
}

const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

class MathError extends Error {
  constructor(public code: string, message: string) { super(message); }
}

async function tauriBackend(): Promise<Backend> {
  const { invoke } = await import("@tauri-apps/api/core");
  return {
    kind: "tauri",
    async math(method, params = {}) {
      const r = await invoke<{ ok: boolean; result?: unknown; error?: { code: string; message: string } }>("math_call", { method, params });
      if (!r.ok) throw new MathError(r.error?.code ?? "error", r.error?.message ?? "math engine error");
      return r.result as never;
    },
    db: (op) => invoke("db", { op }),
    claudeStatus: (refresh = false) => invoke("claude_status", { refresh }),
    claudeAsk: (req) => invoke("claude_ask", { req }),
    claudeCancel: () => invoke("claude_cancel"),
    saveFile: (name, content, base64) => invoke<string>("save_export", { name, content, base64 }),
  };
}

// ---------------------------------------------------------------- browser dev fallback

const LS = "unilearn.dev.";
const load = <T,>(k: string, d: T): T => { try { return JSON.parse(localStorage.getItem(LS + k) ?? "") as T; } catch { return d; } };
const save = (k: string, v: unknown) => localStorage.setItem(LS + k, JSON.stringify(v));

function devBackend(): Backend {
  let rpcId = 0;
  const url = (import.meta.env.VITE_MATH_URL as string) || "http://127.0.0.1:8765/rpc";
  return {
    kind: "dev",
    async math(method, params = {}) {
      const res = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ id: ++rpcId, method, params }) });
      const r = await res.json();
      if (!r.ok) throw new MathError(r.error.code, r.error.message);
      return r.result;
    },
    async db(op: DbOp): Promise<any> {
      const now = Date.now();
      switch (op.op) {
        case "get_profile": return load<Profile | null>("profile", null);
        case "create_profile": { const p = { id: 1, name: op.name, createdAt: now }; save("profile", p); return p; }
        case "record_attempt": { const a = load<unknown[]>("attempts", []); a.push(op.attempt); save("attempts", a); return null; }
        case "list_attempts": return load<AttemptRecord[]>("attempts", []).slice(-(op.limit ?? 5000));
        case "set_lesson": { const l = load<Record<string, unknown>>("lessons", {}); const cur = l[op.section] as { status: string } | undefined;
          if (!(cur?.status === "completed" && op.status === "started")) l[op.section] = { status: op.status, updatedAt: now }; save("lessons", l); return null; }
        case "lesson_progress": return load("lessons", {});
        case "list_notes": return load<Note[]>("notes", []);
        case "save_note": { const n = load<Note[]>("notes", []); if (op.id) { const x = n.find((q) => q.id === op.id); if (x) { x.body = op.body; x.updatedAt = now; } }
          else n.push({ id: now, section: op.section, body: op.body, updatedAt: now }); save("notes", n); return null; }
        case "delete_note": save("notes", load<Note[]>("notes", []).filter((q) => q.id !== op.id)); return null;
        case "list_bookmarks": return load<Bookmark[]>("bookmarks", []);
        case "toggle_bookmark": { const b = load<Bookmark[]>("bookmarks", []); const i = b.findIndex((q) => q.section === op.section);
          if (i >= 0) b.splice(i, 1); else b.push({ section: op.section, createdAt: now }); save("bookmarks", b); return null; }
        case "get_settings": return load("settings", null);
        case "set_settings": save("settings", op.settings); return null;
        case "save_exam": { const e = load<ExamSession[]>("exams", []).filter((q) => q.id !== op.exam.id); e.push(op.exam); save("exams", e); return null; }
        case "list_exams": return load<ExamSession[]>("exams", []);
        case "set_kv": { const kv = load<Record<string, string>>("kv", {}); kv[op.key] = op.value; save("kv", kv); return null; }
        case "get_kv": return load<Record<string, string>>("kv", {})[op.key] ?? null;
        case "log_session": { const s = load<unknown[]>("sessions", []); s.push(op); save("sessions", s); return null; }
        case "list_sessions": return load("sessions", []);
        case "export": { const out: Record<string, unknown> = {}; for (const k of ["profile", "attempts", "lessons", "notes", "bookmarks", "settings", "exams", "kv", "sessions"]) out[k] = load(k, null);
          return JSON.stringify({ format: "unilearn-backup", version: 1, data: out }); }
        case "import": { const d = JSON.parse(op.data); if (d.format !== "unilearn-backup") throw new Error("ไฟล์สำรองไม่ถูกต้อง"); for (const [k, v] of Object.entries(d.data)) save(k, v); return null; }
        case "backup": return "localStorage (dev mode)";
        case "save_conversation": { const c = load<unknown[]>("conversations", []); c.unshift({ id: now, createdAt: now, request: op.request, response: op.response }); save("conversations", c.slice(0, 1000)); return now; }
        case "list_conversations": return load<unknown[]>("conversations", []).slice(0, op.limit ?? 200);
        case "delete_conversation": save("conversations", load<{ id: number }[]>("conversations", []).filter((c) => c.id !== op.id)); return null;
        case "clear_conversations": save("conversations", []); return null;
      }
    },
    claudeStatus: async () => ({ state: "unavailable", message: "AI Tutor ใช้ได้เฉพาะในแอปเดสก์ท็อป" }),
    claudeAsk: async () => ({ ok: false, error: "AI Tutor ใช้ได้เฉพาะในแอปเดสก์ท็อป", state: "unavailable" }),
    claudeCancel: async () => {},
    async saveFile(name, content, base64) {
      const a = document.createElement("a");
      a.href = base64 ? content : URL.createObjectURL(new Blob([content], { type: "application/json" }));
      a.download = name; a.click();
      return `ดาวน์โหลด ${name}`;
    },
  };
}

let backendPromise: Promise<Backend> | null = null;
export function getBackend(): Promise<Backend> {
  backendPromise ??= isTauri ? tauriBackend() : Promise.resolve(devBackend());
  return backendPromise;
}
export { MathError };
