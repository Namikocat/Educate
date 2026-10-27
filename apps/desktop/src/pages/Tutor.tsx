import { useEffect, useState } from "react";
import { validateSpec } from "@viz/spec";
import { AI_LABEL } from "../App";
import { getBackend } from "../lib/backend";
import { sectionTitle, subjectById } from "../lib/content";
import { useData } from "../lib/hooks";
import { useApp } from "../lib/store";
import type { ClaudeStatus, Conversation, TutorRequest, TutorResponse } from "../lib/types";
import { Markdown } from "../components/Markdown";
import { MathBlock, Tex } from "../components/Tex";
import { Badge, Button, Card, ErrorBox, Spinner } from "../components/ui";
import { VizView } from "../components/VizView";

const MODES: { id: TutorRequest["mode"]; label: string; hint: string }[] = [
  { id: "explain_step", label: "อธิบายขั้นนี้", hint: "เลือกขั้นจากหน้า ฝึกทำโจทย์ แล้วกด 'อธิบายขั้นนี้'" },
  { id: "explain_differently", label: "อธิบายแบบอื่น", hint: "เลือกรูปแบบคำอธิบายด้านล่าง" },
  { id: "explain_mistake", label: "วิเคราะห์ข้อผิดพลาดของฉัน", hint: "ใช้คำตอบล่าสุดที่คุณส่ง" },
  { id: "socratic", label: "ติวแบบถาม-ตอบ (Socratic)", hint: "AI จะถามนำแทนการเฉลย" },
  { id: "formula", label: "อธิบายสูตร", hint: "ถามว่าสูตรใช้เมื่อใดและเพราะอะไร" },
  { id: "visualization", label: "ขอภาพประกอบ", hint: "AI เสนอสเปกกราฟ ระบบตรวจก่อนวาด" },
];
const MODE_LABEL: Record<string, string> = Object.fromEntries(MODES.map((m) => [m.id, m.label]));
const STYLES = [["simpler", "ง่ายขึ้น"], ["detailed", "ละเอียดขึ้น"], ["formal", "เชิงรูปนัย"], ["analogy", "เปรียบเทียบกับชีวิตจริง"], ["visual", "เชิงภาพ"]] as const;

interface Shown { question: string; mode: string; section?: string; text: string; durationMs?: number; createdAt: number }

function extractViz(text: string) {
  const m = /```(?:json)?\s*([\s\S]+?)```/.exec(text) ?? /(\{[\s\S]*\})/.exec(text);
  if (!m) return null;
  try { const v = validateSpec(JSON.parse(m[1])); return v.ok ? { spec: v.spec } : { error: v.error }; } catch { return { error: "สเปกกราฟไม่ใช่ JSON ที่ถูกต้อง" }; }
}

export default function Tutor() {
  const { tutor, settings, setSettings, go, touch } = useApp();
  const [status, setStatus] = useState<ClaudeStatus | null>(null);
  const [mode, setMode] = useState<TutorRequest["mode"]>(tutor?.selectedStep ? "explain_step" : "explain_differently");
  const [style, setStyle] = useState<TutorRequest["style"]>("simpler");
  const [question, setQuestion] = useState("");
  const [send, setSend] = useState({ problem: true, solution: true, attempt: true, step: true });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shown, setShown] = useState<Shown | null>(null);
  const [followUp, setFollowUp] = useState<Shown | null>(null);
  const [filter, setFilter] = useState("");
  const history = useData((be) => be.db<Conversation[]>({ op: "list_conversations", limit: 300 }));

  const refresh = async (force = false) => { setStatus(null); setStatus(await (await getBackend()).claudeStatus(force)); };
  useEffect(() => { if (settings.aiEnabled) refresh(); }, [settings.aiEnabled]);

  if (!settings.aiEnabled) return (
    <div className="mx-auto max-w-3xl p-6">
      <Card title="AI Tutor (ไม่บังคับ)">
        <p className="mb-2 text-sm">AI Tutor ใช้ Claude Code CLI ที่ติดตั้งในเครื่องของคุณเพื่อให้คำอธิบายเพิ่มเติม ฟีเจอร์การเรียน การสร้างโจทย์ การตรวจคำตอบ และภาพจำลองทั้งหมดทำงานได้โดยไม่ต้องใช้ AI</p>
        <ul className="mb-3 list-disc pl-5 text-sm text-muted">
          <li>ส่งเฉพาะข้อมูลที่คุณเลือก (โจทย์ เฉลยที่ตรวจแล้ว คำตอบของคุณ) ไม่ส่งเนื้อหาตำราทั้งเล่ม</li>
          <li>Claude ทำงานแบบไม่มีเครื่องมือ (ไม่อ่าน/เขียนไฟล์ ไม่รันคำสั่ง) ในโฟลเดอร์ชั่วคราวที่ว่างเปล่า</li>
          <li>ต้องติดตั้งและลงชื่อเข้าใช้ Claude Code CLI เอง และการใช้งานขึ้นกับบัญชีของคุณ</li>
        </ul>
        <Button variant="primary" onClick={() => setSettings({ aiEnabled: true })}>เปิดใช้ AI Tutor</Button>
      </Card>
    </div>
  );

  const p = tutor?.problem;
  const lesson = tutor ? subjectById(tutor.subject)?.lessons[tutor.section] : undefined;
  const sectionLabel = tutor ? sectionTitle(tutor.subject, tutor.section) : undefined;
  const context: Record<string, unknown> = {
    subject: tutor?.subject, section: sectionLabel,
    objectives: lesson?.objectives.map((o) => o.text).slice(0, 4),
    sourceRef: lesson?.source?.verified ? `Thomas' Calculus 14e §${lesson.section} pp. ${lesson.source.printedPages.join("-")}` : undefined,
    depth: settings.level,
    ...(send.problem && p ? { problem: `${p.statement}\n${p.display}` } : {}),
    ...(send.solution && p ? { verifiedAnswer: p.answerTex, verifiedSteps: p.steps?.map((s) => `${s.explain} ${s.after ?? ""}`) } : {}),
    ...(send.attempt && tutor?.attempt ? { studentAttempt: tutor.attempt } : {}),
    ...(send.step && tutor?.selectedStep ? { selectedStep: `ขั้นที่ ${tutor.selectedStep.index + 1}: ${tutor.selectedStep.step.explain} ${tutor.selectedStep.step.after ?? ""}` } : {}),
    ...(followUp ? { previousExchange: { question: followUp.question || MODE_LABEL[followUp.mode], answer: followUp.text.slice(0, 4000) } } : {}),
  };

  const ask = async () => {
    setBusy(true); setError(null);
    try {
      const be = await getBackend();
      const r: TutorResponse = await be.claudeAsk({ mode, style: mode === "explain_differently" ? style : undefined, context, question: question.slice(0, 2000) });
      if (!r.ok || !r.text) { setError(r.error ?? "คำขอล้มเหลว"); return; }
      const item: Shown = { question, mode, section: sectionLabel, text: r.text, durationMs: r.durationMs, createdAt: Date.now() };
      setShown(item); setFollowUp(null); setQuestion("");
      if (settings.saveTutorHistory) {
        await be.db({ op: "save_conversation", request: { mode, style, question, section: sectionLabel, problem: p?.statement }, response: r.text });
        touch();
      }
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  };
  const cancel = async () => { await (await getBackend()).claudeCancel(); setBusy(false); };
  const viz = shown && shown.mode === "visualization" ? extractViz(shown.text) : null;
  const list = (history.data ?? []).filter((c) => !filter || `${c.request.question} ${c.request.section} ${c.response}`.toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className="flex h-full">
      <div className="min-w-0 flex-1 space-y-4 overflow-y-auto p-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">AI Tutor</h1>
          <div className="flex items-center gap-2 text-sm">{status ? <Badge tone={status.state === "available" ? "good" : "bad"}>{AI_LABEL[status.state]}{status.version ? ` · ${status.version}` : ""}</Badge> : <Spinner label="ตรวจสอบ Claude CLI…" />}
            <Button variant="ghost" onClick={() => refresh(true)}>ตรวจใหม่</Button></div>
        </div>
        {status && status.state !== "available" && <ErrorBox error={`${AI_LABEL[status.state]}${status.message ? ` — ${status.message}` : ""}. การเรียนส่วนอื่นยังใช้งานได้ตามปกติ`} />}

        {(shown || busy) && (
          <Card title={shown && !busy ? <span>คำตอบ <span className="text-sm font-normal text-muted">· {MODE_LABEL[shown.mode]}{shown.section ? ` · ${shown.section}` : ""}</span></span> : "กำลังรอคำตอบ"}>
            {busy ? <div className="flex items-center gap-3"><Spinner label="Claude กำลังคิด…" /><Button onClick={cancel}>ยกเลิก</Button></div> : shown && <>
              {shown.question && <div className="mb-3 rounded-md bg-bg px-3 py-2 text-sm"><span className="text-muted">คำถาม: </span>{shown.question}</div>}
              <Markdown text={shown.text} />
              {viz && ("spec" in viz ? <div className="mt-3"><VizView spec={viz.spec} /></div> : <p className="mt-2 text-sm text-bad">ไม่แสดงกราฟ: {viz.error}</p>)}
              <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-line pt-3">
                <Button onClick={() => { setFollowUp(shown); document.getElementById("tutor-q")?.focus(); }}>ถามต่อจากคำตอบนี้</Button>
                <span className="text-xs text-muted">⚠ สร้างโดย AI ใช้เป็นข้อมูลเสริม ระบบไม่ได้ตรวจความถูกต้อง เฉลยที่ตรวจแล้วอยู่ในหน้าฝึกทำโจทย์{shown.durationMs ? ` · ${(shown.durationMs / 1000).toFixed(1)} วินาที` : ""}</span>
              </div>
            </>}
          </Card>
        )}
        {error && <ErrorBox error={error} />}

        <Card title="คำถาม">
          {followUp && <div className="mb-2 flex items-center justify-between rounded-md border border-accent/40 bg-accent/5 px-3 py-2 text-sm">
            <span>กำลังถามต่อจาก: {followUp.question || MODE_LABEL[followUp.mode]}</span><button className="text-xs text-accent underline" onClick={() => setFollowUp(null)}>ยกเลิกการถามต่อ</button></div>}
          <div className="mb-2 flex flex-wrap gap-1">{MODES.map((m) => <button key={m.id} onClick={() => setMode(m.id)} className={`rounded-md px-3 py-1 text-sm ${mode === m.id ? "bg-accent text-white" : "border border-line"}`}>{m.label}</button>)}</div>
          <p className="mb-2 text-xs text-muted">{MODES.find((m) => m.id === mode)?.hint}</p>
          {mode === "explain_differently" && <div className="mb-2 flex flex-wrap gap-1">{STYLES.map(([id, l]) => <button key={id} onClick={() => setStyle(id)} className={`rounded px-2 py-0.5 text-xs ${style === id ? "bg-accent/20" : "border border-line"}`}>{l}</button>)}</div>}
          <textarea id="tutor-q" value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} placeholder="พิมพ์คำถาม (ไม่บังคับ) · Ctrl+Enter เพื่อส่ง" className="w-full rounded border border-line bg-bg p-2 text-sm" aria-label="คำถาม"
            onKeyDown={(e) => { if (e.ctrlKey && e.key === "Enter" && !busy && status?.state === "available") ask(); }} />
          <div className="mt-2 flex items-center gap-3"><Button variant="primary" onClick={ask} disabled={busy || status?.state !== "available"}>{busy ? "กำลังถาม Claude…" : "ส่งคำถาม"}</Button>
            <label className="flex items-center gap-1 text-xs text-muted"><input type="checkbox" checked={settings.saveTutorHistory} onChange={(e) => setSettings({ saveTutorHistory: e.target.checked })} />บันทึกประวัติไว้ในเครื่อง</label></div>
        </Card>

        <Card title="บริบทที่จะส่ง">
          {tutor ? <p className="mb-2 text-sm">หัวข้อ: {sectionLabel}{p && <> · โจทย์: <Tex text={p.statement} /></>}</p> : <p className="text-sm text-muted">ยังไม่มีบริบท เปิดบทเรียนหรือโจทย์ก่อน <Button variant="ghost" onClick={() => go({ page: "practice" })}>ไปฝึกทำโจทย์</Button></p>}
          {p && <div className="flex flex-wrap gap-4 text-sm">
            {(["problem", "solution", "attempt", "step"] as const).map((k) => <label key={k} className="flex items-center gap-1"><input type="checkbox" checked={send[k]} onChange={(e) => setSend({ ...send, [k]: e.target.checked })} />
              {{ problem: "โจทย์", solution: "เฉลยที่ตรวจแล้ว", attempt: "คำตอบของฉัน", step: "ขั้นที่เลือก" }[k]}</label>)}
          </div>}
          {tutor?.selectedStep && send.step && <div className="mt-2 rounded bg-bg p-2 text-sm">ขั้นที่ {tutor.selectedStep.index + 1}: <Tex text={tutor.selectedStep.step.explain} />{tutor.selectedStep.step.after && <MathBlock tex={tutor.selectedStep.step.after} />}</div>}
          <details className="mt-2 text-xs text-muted"><summary>ดูข้อมูลทั้งหมดที่จะส่ง (ความเป็นส่วนตัว)</summary><pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-bg p-2">{JSON.stringify(context, null, 2)}</pre></details>
        </Card>
      </div>

      <aside className="hidden w-80 shrink-0 flex-col border-l border-line bg-surface lg:flex" aria-label="ประวัติการถาม">
        <div className="space-y-2 border-b border-line p-3">
          <div className="flex items-center justify-between"><h2 className="font-semibold">ประวัติการถาม</h2><span className="text-xs text-muted">{history.data?.length ?? 0} รายการ</span></div>
          <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="ค้นหาในประวัติ" className="w-full rounded border border-line bg-bg px-2 py-1 text-sm" aria-label="ค้นหาในประวัติ" />
        </div>
        <ul className="flex-1 overflow-y-auto p-2">
          {!list.length && <li className="p-2 text-sm text-muted">{settings.saveTutorHistory ? "ยังไม่มีประวัติ" : "ปิดการบันทึกประวัติอยู่"}</li>}
          {list.map((c) => (
            <li key={c.id} className="group mb-1">
              <button onClick={() => { setShown({ question: c.request.question, mode: c.request.mode, section: c.request.section, text: c.response, createdAt: c.createdAt }); setError(null); }}
                className={`w-full rounded-md px-2 py-2 text-left hover:bg-bg ${shown?.createdAt === c.createdAt && shown.text === c.response ? "bg-accent/10" : ""}`}>
                <div className="truncate text-sm font-medium">{c.request.question || MODE_LABEL[c.request.mode] || "คำถาม"}</div>
                <div className="truncate text-xs text-muted">{new Date(c.createdAt).toLocaleString("th-TH", { dateStyle: "short", timeStyle: "short" })} · {c.request.section ?? "ไม่มีหัวข้อ"}</div>
              </button>
              <button className="hidden px-2 text-xs text-bad group-hover:inline" onClick={async () => { await (await getBackend()).db({ op: "delete_conversation", id: c.id }); touch(); }}>ลบ</button>
            </li>
          ))}
        </ul>
        {!!history.data?.length && <div className="border-t border-line p-2"><Button variant="ghost" className="w-full justify-center text-bad" onClick={async () => {
          if (confirm("ลบประวัติการถามทั้งหมด?")) { await (await getBackend()).db({ op: "clear_conversations" }); setShown(null); touch(); } }}>ล้างประวัติทั้งหมด</Button></div>}
      </aside>
    </div>
  );
}
