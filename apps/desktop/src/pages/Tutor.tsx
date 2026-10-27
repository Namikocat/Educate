import { useEffect, useState } from "react";
import { validateSpec } from "@viz/spec";
import { AI_LABEL } from "../App";
import { getBackend } from "../lib/backend";
import { sectionTitle, subjectById } from "../lib/content";
import { useApp } from "../lib/store";
import type { ClaudeStatus, TutorRequest, TutorResponse } from "../lib/types";
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
const STYLES = [["simpler", "ง่ายขึ้น"], ["detailed", "ละเอียดขึ้น"], ["formal", "เชิงรูปนัย"], ["analogy", "เปรียบเทียบกับชีวิตจริง"], ["visual", "เชิงภาพ"]] as const;

export default function Tutor() {
  const { tutor, settings, setSettings, go } = useApp();
  const [status, setStatus] = useState<ClaudeStatus | null>(null);
  const [mode, setMode] = useState<TutorRequest["mode"]>(tutor?.selectedStep ? "explain_step" : "explain_differently");
  const [style, setStyle] = useState<TutorRequest["style"]>("simpler");
  const [question, setQuestion] = useState("");
  const [send, setSend] = useState({ problem: true, solution: true, attempt: true, step: true });
  const [busy, setBusy] = useState(false);
  const [resp, setResp] = useState<TutorResponse | null>(null);

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
  const context: Record<string, unknown> = {
    subject: tutor?.subject, section: tutor ? sectionTitle(tutor.subject, tutor.section) : undefined,
    objectives: lesson?.objectives.map((o) => o.text).slice(0, 4),
    sourceRef: lesson?.source?.verified ? `Thomas' Calculus 14e §${lesson.section} pp. ${lesson.source.printedPages.join("-")}` : undefined,
    depth: settings.level,
    ...(send.problem && p ? { problem: `${p.statement}\n${p.display}` } : {}),
    ...(send.solution && p ? { verifiedAnswer: p.answerTex, verifiedSteps: p.steps?.map((s) => `${s.explain} ${s.after ?? ""}`) } : {}),
    ...(send.attempt && tutor?.attempt ? { studentAttempt: tutor.attempt } : {}),
    ...(send.step && tutor?.selectedStep ? { selectedStep: `ขั้นที่ ${tutor.selectedStep.index + 1}: ${tutor.selectedStep.step.explain} ${tutor.selectedStep.step.after ?? ""}` } : {}),
  };
  const ask = async () => {
    setBusy(true); setResp(null);
    try { setResp(await (await getBackend()).claudeAsk({ mode, style: mode === "explain_differently" ? style : undefined, context, question: question.slice(0, 2000) })); }
    catch (e) { setResp({ ok: false, error: String(e) }); } finally { setBusy(false); }
  };
  const cancel = async () => { await (await getBackend()).claudeCancel(); setBusy(false); };
  const vizSpec = (() => {
    if (!resp?.ok || mode !== "visualization" || !resp.text) return null;
    const m = /```(?:json)?\s*([\s\S]+?)```/.exec(resp.text) ?? /(\{[\s\S]*\})/.exec(resp.text);
    if (!m) return { error: "ไม่พบสเปกกราฟในคำตอบ" };
    try { const v = validateSpec(JSON.parse(m[1])); return v.ok ? { spec: v.spec } : { error: v.error }; } catch { return { error: "สเปกกราฟไม่ใช่ JSON ที่ถูกต้อง" }; }
  })();

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">AI Tutor</h1>
        <div className="flex items-center gap-2 text-sm">{status ? <Badge tone={status.state === "available" ? "good" : "bad"}>{AI_LABEL[status.state]}{status.version ? ` · ${status.version}` : ""}</Badge> : <Spinner label="ตรวจสอบ Claude CLI…" />}
          <Button variant="ghost" onClick={() => refresh(true)}>ตรวจใหม่</Button></div>
      </div>
      {status && status.state !== "available" && <ErrorBox error={`${AI_LABEL[status.state]}${status.message ? ` — ${status.message}` : ""}. การเรียนส่วนอื่นยังใช้งานได้ตามปกติ`} />}
      <Card title="บริบทที่จะส่ง">
        {tutor ? <p className="mb-2 text-sm">หัวข้อ: {sectionTitle(tutor.subject, tutor.section)}{p && <> · โจทย์: <Tex text={p.statement} /></>}</p> : <p className="text-sm text-muted">ยังไม่มีบริบท เปิดบทเรียนหรือโจทย์ก่อน <Button variant="ghost" onClick={() => go({ page: "practice" })}>ไปฝึกทำโจทย์</Button></p>}
        {p && <div className="flex flex-wrap gap-4 text-sm">
          {(["problem", "solution", "attempt", "step"] as const).map((k) => <label key={k} className="flex items-center gap-1"><input type="checkbox" checked={send[k]} onChange={(e) => setSend({ ...send, [k]: e.target.checked })} />
            {{ problem: "โจทย์", solution: "เฉลยที่ตรวจแล้ว", attempt: "คำตอบของฉัน", step: "ขั้นที่เลือก" }[k]}</label>)}
        </div>}
        {tutor?.selectedStep && send.step && <div className="mt-2 rounded bg-bg p-2 text-sm">ขั้นที่ {tutor.selectedStep.index + 1}: <Tex text={tutor.selectedStep.step.explain} />{tutor.selectedStep.step.after && <MathBlock tex={tutor.selectedStep.step.after} />}</div>}
        <details className="mt-2 text-xs text-muted"><summary>ดูข้อมูลทั้งหมดที่จะส่ง (ความเป็นส่วนตัว)</summary><pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-bg p-2">{JSON.stringify(context, null, 2)}</pre></details>
      </Card>
      <Card title="คำขอ">
        <div className="mb-2 flex flex-wrap gap-1">{MODES.map((m) => <button key={m.id} onClick={() => setMode(m.id)} className={`rounded-md px-3 py-1 text-sm ${mode === m.id ? "bg-accent text-white" : "border border-line"}`}>{m.label}</button>)}</div>
        <p className="mb-2 text-xs text-muted">{MODES.find((m) => m.id === mode)?.hint}</p>
        {mode === "explain_differently" && <div className="mb-2 flex flex-wrap gap-1">{STYLES.map(([id, l]) => <button key={id} onClick={() => setStyle(id)} className={`rounded px-2 py-0.5 text-xs ${style === id ? "bg-accent/20" : "border border-line"}`}>{l}</button>)}</div>}
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} placeholder="คำถามเพิ่มเติม (ไม่บังคับ)" className="w-full rounded border border-line bg-bg p-2 text-sm" aria-label="คำถาม" />
        <div className="mt-2 flex gap-2"><Button variant="primary" onClick={ask} disabled={busy || status?.state !== "available"}>{busy ? "กำลังถาม Claude…" : "ส่งคำถาม"}</Button>{busy && <Button onClick={cancel}>ยกเลิก</Button>}</div>
      </Card>
      {resp && (
        <Card title="คำตอบจาก AI">
          {resp.ok ? <>
            <div className="mb-2 rounded border border-accent/40 bg-accent/5 p-2 text-xs">⚠ คำอธิบายนี้สร้างโดย AI ใช้เป็นข้อมูลเสริมเท่านั้น คำตอบและวิธีทำที่ระบบตรวจสอบแล้วคือฉบับที่อยู่ในหน้าฝึกทำโจทย์ ระบบไม่ได้ตรวจสอบความถูกต้องของข้อความนี้</div>
            <div className="whitespace-pre-wrap text-sm leading-7"><Tex text={resp.text ?? ""} /></div>
            {vizSpec && ("spec" in vizSpec ? <div className="mt-3"><VizView spec={vizSpec.spec} /></div> : <p className="mt-2 text-sm text-bad">ไม่แสดงกราฟ: {vizSpec.error}</p>)}
            {resp.durationMs && <p className="mt-2 text-xs text-muted">ใช้เวลา {(resp.durationMs / 1000).toFixed(1)} วินาที</p>}
          </> : <ErrorBox error={resp.error ?? "คำขอล้มเหลว"} />}
        </Card>
      )}
    </div>
  );
}
