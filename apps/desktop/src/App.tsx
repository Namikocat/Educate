import { useEffect, useState } from "react";
import { getBackend } from "./lib/backend";
import { searchLessons, SUBJECTS } from "./lib/content";
import { useApp, type Page } from "./lib/store";
import type { ClaudeStatus, Profile } from "./lib/types";
import { Button, Card, ErrorBox, Spinner } from "./components/ui";
import Dashboard from "./pages/Dashboard";
import Subjects from "./pages/Subjects";
import Lessons from "./pages/Lessons";
import Practice from "./pages/Practice";
import Exam from "./pages/Exam";
import Visualizations from "./pages/Visualizations";
import Progress from "./pages/Progress";
import Notes from "./pages/Notes";
import Tutor from "./pages/Tutor";
import Settings from "./pages/Settings";

const NAV: { page: Page; label: string; key?: string }[] = [
  { page: "dashboard", label: "แดชบอร์ด", key: "1" },
  { page: "subjects", label: "วิชาทั้งหมด", key: "2" },
  { page: "courses", label: "คอร์สของฉัน", key: "3" },
  { page: "lessons", label: "บทเรียน", key: "4" },
  { page: "practice", label: "ฝึกทำโจทย์", key: "5" },
  { page: "exam", label: "ศูนย์สอบ", key: "6" },
  { page: "viz", label: "ภาพจำลอง", key: "7" },
  { page: "progress", label: "ความก้าวหน้า", key: "8" },
  { page: "notes", label: "บันทึก", key: "9" },
  { page: "tutor", label: "AI Tutor" },
  { page: "settings", label: "ตั้งค่า" },
];

export default function App() {
  const { ready, init, route, go, settings, profile, setSettings } = useApp();
  const [initError, setInitError] = useState<unknown>(null);
  const [engine, setEngine] = useState<"starting" | "ok" | "error">("starting");
  const [ai, setAi] = useState<ClaudeStatus | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => { init().catch(setInitError); }, [init]);
  useEffect(() => {
    getBackend().then((be) => be.math("ping")).then(() => setEngine("ok")).catch(() => setEngine("error"));
  }, []);
  useEffect(() => {
    if (!settings.aiEnabled) { setAi({ state: "disabled" }); return; }
    getBackend().then((be) => be.claudeStatus()).then(setAi).catch(() => setAi({ state: "unavailable" }));
  }, [settings.aiEnabled]);

  // theme + font size
  useEffect(() => {
    const dark = settings.theme === "dark" || (settings.theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.toggle("dark", dark);
    document.documentElement.style.setProperty("--font-scale", String(settings.fontScale));
  }, [settings.theme, settings.fontScale]);

  // study-session logging (local analytics)
  useEffect(() => {
    const started = Date.now();
    return () => { getBackend().then((be) => be.db({ op: "log_session", startedAt: started, endedAt: Date.now(), activity: route.page })); };
  }, [route.page]);

  // global keyboard shortcuts: Alt+1..9 navigation, Ctrl+K search, F11 focus mode
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.altKey && /^[1-9]$/.test(e.key)) { const n = NAV.find((x) => x.key === e.key); if (n) { e.preventDefault(); go({ page: n.page }); } }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); document.getElementById("global-search")?.focus(); }
      if (e.key === "F11") { e.preventDefault(); setSettings({ focusMode: !useApp.getState().settings.focusMode }); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [go, setSettings]);

  if (initError) return <div className="p-8"><ErrorBox error={initError} /></div>;
  if (!ready) return <div className="grid h-screen place-items-center"><Spinner label="กำลังเริ่มต้น UniLearn Studio…" /></div>;
  if (!profile) return <Onboarding />;

  const hits = searchLessons(q);
  const focus = settings.focusMode;
  const Page = { dashboard: Dashboard, subjects: Subjects, courses: Subjects, lessons: Lessons, practice: Practice, exam: Exam, viz: Visualizations, progress: Progress, notes: Notes, tutor: Tutor, settings: Settings }[route.page];

  return (
    <div className="flex h-screen overflow-hidden">
      {!focus && (
        <nav className="flex w-52 shrink-0 flex-col border-r border-line bg-surface" aria-label="เมนูหลัก">
          <div className="px-4 py-4"><div className="text-lg font-bold tracking-tight">UniLearn <span className="text-accent">Studio</span></div><div className="text-xs text-muted">สวัสดี {profile.name}</div></div>
          <ul className="flex-1 space-y-0.5 overflow-y-auto px-2">
            {NAV.map((n) => (
              <li key={n.page}>
                <button onClick={() => go({ page: n.page })} aria-current={route.page === n.page ? "page" : undefined}
                  className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm ${route.page === n.page ? "bg-accent/10 font-semibold text-accent" : "hover:bg-bg"}`}>
                  {n.label}{n.key && <kbd className="text-[10px] text-muted">Alt+{n.key}</kbd>}
                </button>
              </li>
            ))}
          </ul>
          <div className="space-y-1 border-t border-line p-3 text-xs">
            <StatusDot ok={engine === "ok"} warn={engine === "starting"} label={engine === "ok" ? "เครื่องคำนวณพร้อม (ออฟไลน์)" : engine === "starting" ? "กำลังเริ่มเครื่องคำนวณ…" : "เครื่องคำนวณไม่ตอบสนอง"} />
            <StatusDot ok={ai?.state === "available"} warn={ai?.state === "disabled" || ai?.state === "busy"} label={`AI: ${AI_LABEL[ai?.state ?? "unknown"]}`} />
          </div>
        </nav>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-line bg-surface px-4 py-2">
          <div className="relative flex-1 max-w-xl">
            <input id="global-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="ค้นหาบทเรียน หัวข้อ หรือคำศัพท์ (Ctrl+K)" aria-label="ค้นหาบทเรียน"
              className="w-full rounded-md border border-line bg-bg px-3 py-1.5 text-sm" onKeyDown={(e) => { if (e.key === "Escape") setQ(""); }} />
            {hits.length > 0 && (
              <ul className="absolute z-20 mt-1 w-full rounded-md border border-line bg-surface shadow-lg">
                {hits.map((h) => <li key={h.subject + h.section}><button className="w-full px-3 py-2 text-left text-sm hover:bg-bg" onClick={() => { go({ page: "lessons", subject: h.subject, section: h.section }); setQ(""); }}>
                  <span className="font-medium">{h.section}</span> {h.title}</button></li>)}
              </ul>
            )}
          </div>
          <Button variant="ghost" onClick={() => setSettings({ focusMode: !focus })} title="โหมดโฟกัส (F11)">{focus ? "ออกจากโหมดโฟกัส" : "โหมดโฟกัส"}</Button>
        </header>
        <main className="min-h-0 flex-1 overflow-y-auto">
          {engine === "error" && <div className="m-4"><ErrorBox error="ไม่สามารถเชื่อมต่อเครื่องคำนวณคณิตศาสตร์ได้ บทเรียนยังเปิดอ่านได้ แต่การสร้างและตรวจโจทย์จะใช้ไม่ได้ ลองปิดแล้วเปิดโปรแกรมใหม่" /></div>}
          <Page />
        </main>
      </div>
    </div>
  );
}

const AI_LABEL: Record<string, string> = {
  not_installed: "ไม่ได้ติดตั้ง Claude CLI", not_authenticated: "ยังไม่ได้ลงชื่อเข้าใช้", available: "พร้อมใช้งาน", busy: "กำลังทำงาน",
  rate_limited: "ถูกจำกัดการใช้งานชั่วคราว", failed: "คำขอล้มเหลว", unavailable: "ไม่พร้อมใช้งาน", disabled: "ปิดอยู่", unknown: "ไม่ทราบสถานะ",
};
export { AI_LABEL };

function StatusDot({ ok, warn, label }: { ok: boolean; warn?: boolean; label: string }) {
  return <div className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${ok ? "bg-good" : warn ? "bg-muted" : "bg-bad"}`} aria-hidden />{label}</div>;
}

function Onboarding() {
  const [name, setName] = useState("");
  const [err, setErr] = useState<unknown>(null);
  const setProfile = useApp((s) => s.setProfile);
  const submit = async () => {
    try {
      if (!name.trim()) throw new Error("กรุณาใส่ชื่อ");
      const be = await getBackend();
      setProfile(await be.db<Profile>({ op: "create_profile", name: name.trim().slice(0, 60) }));
    } catch (e) { setErr(e); }
  };
  return (
    <div className="grid h-screen place-items-center p-6">
      <Card className="w-full max-w-md" title="ยินดีต้อนรับสู่ UniLearn Studio">
        <p className="mb-4 text-sm text-muted">สร้างโปรไฟล์การเรียนในเครื่องนี้ ข้อมูลทั้งหมดเก็บไว้ในเครื่องของคุณเท่านั้น ใช้งานได้แบบออฟไลน์</p>
        <p className="mb-4 text-sm">วิชาที่พร้อม: {SUBJECTS.map((s) => s.manifest.name).join(", ")}</p>
        <label className="text-sm text-muted" htmlFor="pname">ชื่อที่ใช้แสดง</label>
        <input id="pname" autoFocus value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submit()} className="mb-3 mt-1 w-full rounded-md border border-line bg-bg px-3 py-2" />
        <ErrorBox error={err} />
        <Button variant="primary" className="mt-3 w-full justify-center" onClick={submit}>เริ่มเรียน</Button>
      </Card>
    </div>
  );
}
