import { useEffect, useMemo, useRef, useState } from "react";
import { getBackend } from "../lib/backend";
import { allSections, DEFAULT_SUBJECT, EXAM_PRESETS, sectionTitle } from "../lib/content";
import { randomSeed, useAttempts, useData } from "../lib/hooks";
import { useApp } from "../lib/store";
import type { CheckResult, ExamConfig, ExamQuestion, ExamSession, Step } from "../lib/types";
import { MathInput } from "../components/MathInput";
import { MathBlock, Tex } from "../components/Tex";
import { Badge, Bar, Button, Card, ErrorBox, Spinner } from "../components/ui";

export default function Exam() {
  const route = useApp((s) => s.route);
  const exams = useData((be) => be.db<ExamSession[]>({ op: "list_exams" }));
  const [active, setActive] = useState<ExamSession | null>(null);
  const [view, setView] = useState<"config" | "run" | "review">("config");

  // resume an unfinished exam (autosaved) if the timer has not expired
  useEffect(() => {
    const open = exams.data?.find((e) => !e.submittedAt);
    if (open && !active) { setActive(open); setView("run"); }
  }, [exams.data, active]);

  if (exams.loading && !exams.data) return <div className="p-6"><Spinner /></div>;
  if (view === "run" && active) return <Runner exam={active} onSubmitted={(e) => { setActive(e); setView("review"); }} />;
  if (view === "review" && active) return <Review exam={active} onRetake={() => { setActive(null); setView("config"); }} />;
  return <Config initialSection={route.section} history={exams.data ?? []} onStart={(e) => { setActive(e); setView("run"); }} onOpen={(e) => { setActive(e); setView("review"); }} />;
}

function Config({ initialSection, history, onStart, onOpen }: { initialSection?: string; history: ExamSession[]; onStart: (e: ExamSession) => void; onOpen: (e: ExamSession) => void }) {
  const attempts = useAttempts();
  const [cfg, setCfg] = useState<ExamConfig>({ sections: initialSection ? [initialSection] : EXAM_PRESETS[4].sections, count: initialSection ? 5 : 20, difficulty: null,
    minutes: initialSection ? 20 : 120, seed: randomSeed(), immediateFeedback: false, includeChoice: true, preset: initialSection ? "topic" : "final" });
  const [err, setErr] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const secs = allSections(DEFAULT_SUBJECT);
  const toggle = (s: string) => setCfg((c) => ({ ...c, preset: "custom", sections: c.sections.includes(s) ? c.sections.filter((x) => x !== s) : [...c.sections, s].sort() }));
  const start = async () => {
    setBusy(true); setErr(null);
    try {
      if (!cfg.sections.length) throw new Error("เลือกอย่างน้อยหนึ่งหัวข้อ");
      const be = await getBackend();
      const recent = (attempts.data ?? []).slice(-300).map((a: any) => a.canonical).filter(Boolean);
      const qs = await be.math<ExamQuestion[]>("exam", { sections: cfg.sections, count: cfg.count, difficulty: cfg.difficulty, seed: cfg.seed, includeChoice: cfg.includeChoice, excludeCanonical: recent });
      const now = Date.now();
      const title = EXAM_PRESETS.find((p) => p.id === cfg.preset)?.label ?? `แบบทดสอบ ${cfg.sections.join(", ")}`;
      const exam: ExamSession = { id: `exam-${now}`, title, config: cfg, questions: qs, startedAt: now, endsAt: now + cfg.minutes * 60_000 };
      await be.db({ op: "save_exam", exam });
      onStart(exam);
    } catch (e) { setErr(e); } finally { setBusy(false); }
  };
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">ศูนย์สอบ (Exam Simulation)</h1>
      <Card title="ชุดข้อสอบสำเร็จรูป">
        <div className="flex flex-wrap gap-2">{EXAM_PRESETS.map((p) => <Button key={p.id} variant={cfg.preset === p.id ? "primary" : "default"}
          onClick={() => setCfg({ ...cfg, preset: p.id, sections: p.sections, count: p.id === "final" ? 20 : 10, minutes: p.id === "final" ? 120 : 60 })}>{p.label}</Button>)}</div>
        <p className="mt-2 text-xs text-muted">ข้อสอบปลายภาคเลือกโจทย์จาก 20 หัวข้อสอบเท่านั้น</p>
      </Card>
      <Card title="กำหนดเอง">
        <div className="mb-3 grid grid-cols-2 gap-1 md:grid-cols-4">{secs.map((s) => <label key={s} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={cfg.sections.includes(s)} onChange={() => toggle(s)} />{sectionTitle(DEFAULT_SUBJECT, s)}</label>)}</div>
        <div className="grid gap-3 md:grid-cols-3">
          <Num label="จำนวนข้อ" value={cfg.count} min={1} max={60} onChange={(v) => setCfg({ ...cfg, count: v })} />
          <Num label="เวลา (นาที)" value={cfg.minutes} min={5} max={300} onChange={(v) => setCfg({ ...cfg, minutes: v })} />
          <Num label="Random seed" value={cfg.seed} min={0} max={999999999} onChange={(v) => setCfg({ ...cfg, seed: v })} />
          <label className="flex flex-col gap-1 text-sm"><span className="text-muted">ความยาก</span>
            <select className="rounded-md border border-line bg-surface px-2 py-1.5" value={cfg.difficulty ?? 0} onChange={(e) => setCfg({ ...cfg, difficulty: Number(e.target.value) || null })}>
              <option value={0}>คละระดับ</option><option value={1}>ง่าย</option><option value={2}>ปานกลาง</option><option value={3}>ยาก</option></select></label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={cfg.immediateFeedback} onChange={(e) => setCfg({ ...cfg, immediateFeedback: e.target.checked })} />แสดงผลทันทีหลังตอบแต่ละข้อ</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={cfg.includeChoice} onChange={(e) => setCfg({ ...cfg, includeChoice: e.target.checked })} />รวมข้อปรนัย</label>
        </div>
        <ErrorBox error={err} />
        <Button variant="primary" className="mt-3" onClick={start} disabled={busy}>{busy ? "กำลังสร้างข้อสอบ…" : "เริ่มสอบ"}</Button>
      </Card>
      <Card title="ประวัติการสอบ">
        {history.filter((h) => h.submittedAt).length === 0 ? <p className="text-sm text-muted">ยังไม่มี</p> :
          <ul className="space-y-1">{history.filter((h) => h.submittedAt).sort((a, b) => b.startedAt - a.startedAt).map((h) =>
            <li key={h.id} className="flex items-center justify-between text-sm"><span>{new Date(h.startedAt).toLocaleString("th-TH")} · {h.title} · {h.questions.length} ข้อ</span>
              <span className="flex items-center gap-2"><Badge tone={(h.score ?? 0) >= 0.5 ? "good" : "bad"}>{Math.round((h.score ?? 0) * 100)}%</Badge><Button onClick={() => onOpen(h)}>ดูผล</Button></span></li>)}</ul>}
      </Card>
    </div>
  );
}

function Num({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (v: number) => void }) {
  return <label className="flex flex-col gap-1 text-sm"><span className="text-muted">{label}</span><input type="number" min={min} max={max} value={value} onChange={(e) => onChange(Math.max(min, Math.min(max, Number(e.target.value) || min)))} className="rounded-md border border-line bg-surface px-2 py-1.5" /></label>;
}

async function gradeAll(exam: ExamSession): Promise<ExamSession> {
  const be = await getBackend();
  const qs: ExamQuestion[] = [];
  for (const q of exam.questions) {
    const r = q.answer ? await be.math<CheckResult>("check", { templateId: q.templateId, seed: q.seed, difficulty: q.difficulty, answer: q.answer })
      : { correct: false, method: "blank", feedback: "ไม่ได้ตอบ" };
    qs.push({ ...q, result: r });
    await be.db({ op: "record_attempt", attempt: { section: q.section, templateId: q.templateId, difficulty: q.difficulty, correct: r.correct, hintsUsed: 0, solutionRevealed: false,
      errorType: r.errorType ?? null, timeMs: 0, at: Date.now(), problemId: q.id, canonical: q.canonical, answer: (q.answer ?? "").slice(0, 400) } });
  }
  const score = qs.filter((q) => q.result?.correct).length / Math.max(1, qs.length);
  const done = { ...exam, questions: qs, submittedAt: Date.now(), score };
  await be.db({ op: "save_exam", exam: done });
  return done;
}

function Runner({ exam: initial, onSubmitted }: { exam: ExamSession; onSubmitted: (e: ExamSession) => void }) {
  const touch = useApp((s) => s.touch);
  const [exam, setExam] = useState(initial);
  const [i, setI] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Record<number, CheckResult>>({});
  const saveT = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(t); }, []);
  const left = Math.max(0, exam.endsAt - now);
  const submit = async () => { setBusy(true); const done = await gradeAll(exam); touch(); onSubmitted(done); };
  useEffect(() => { if (left === 0 && !busy) submit(); /* auto-submit when time runs out */ // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [left]);
  const setAnswer = (v: string) => {
    const qs = exam.questions.map((q, k) => (k === i ? { ...q, answer: v } : q));
    const next = { ...exam, questions: qs };
    setExam(next);
    clearTimeout(saveT.current);
    saveT.current = setTimeout(() => getBackend().then((be) => be.db({ op: "save_exam", exam: next })), 500); // autosave
  };
  const checkNow = async () => {
    const q = exam.questions[i]; if (!q.answer) return;
    const r = await (await getBackend()).math<CheckResult>("check", { templateId: q.templateId, seed: q.seed, difficulty: q.difficulty, answer: q.answer });
    setFeedback({ ...feedback, [i]: r });
  };
  const q = exam.questions[i];
  const mm = Math.floor(left / 60000), ss = Math.floor((left % 60000) / 1000);
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{exam.title}</h1>
        <div className={`rounded-md px-3 py-1 font-mono text-lg ${left < 5 * 60000 ? "bg-bad/10 text-bad" : "bg-bg"}`} aria-live="polite">⏱ {mm}:{String(ss).padStart(2, "0")}</div>
      </div>
      <nav className="flex flex-wrap gap-1" aria-label="ข้อสอบ">{exam.questions.map((qq, k) => <button key={k} onClick={() => setI(k)} className={`h-8 w-8 rounded text-sm ${k === i ? "bg-accent text-white" : qq.answer ? "bg-accent/15" : "border border-line"}`}>{k + 1}</button>)}</nav>
      <Card title={<span>ข้อ {i + 1} / {exam.questions.length} <span className="text-sm font-normal text-muted">· {sectionTitle(DEFAULT_SUBJECT, q.section)}</span></span>}>
        <p className="mb-2"><Tex text={q.statement} /></p>
        <MathBlock tex={q.display} className="my-3 text-lg" />
        {q.answerType === "choice" ? <div className="flex gap-2">{q.choices!.map((c) => <Button key={c.id} variant={q.answer === c.id ? "primary" : "default"} onClick={() => setAnswer(c.id)}>{c.label}</Button>)}</div>
          : <MathInput id={`exam-${i}`} value={q.answer ?? ""} onChange={setAnswer} allowDiverges={q.answerType === "improper"} />}
        {exam.config.immediateFeedback && <div className="mt-2"><Button onClick={checkNow}>ตรวจข้อนี้</Button>
          {feedback[i] && <span className={`ml-2 text-sm ${feedback[i].correct ? "text-good" : "text-bad"}`}>{feedback[i].parseError ?? (feedback[i].correct ? "ถูกต้อง" : "ยังไม่ถูกต้อง")}</span>}</div>}
        <div className="mt-4 flex justify-between">
          <Button onClick={() => setI(Math.max(0, i - 1))} disabled={i === 0}>← ก่อนหน้า</Button>
          <Button onClick={() => setI(Math.min(exam.questions.length - 1, i + 1))} disabled={i === exam.questions.length - 1}>ถัดไป →</Button>
        </div>
      </Card>
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted">ตอบแล้ว {exam.questions.filter((x) => x.answer).length} / {exam.questions.length} · บันทึกอัตโนมัติ</span>
        <Button variant="primary" disabled={busy} onClick={() => { if (confirm("ยืนยันส่งข้อสอบ?")) submit(); }}>{busy ? "กำลังตรวจ…" : "ส่งข้อสอบ"}</Button>
      </div>
    </div>
  );
}

function Review({ exam, onRetake }: { exam: ExamSession; onRetake: () => void }) {
  const go = useApp((s) => s.go);
  const bySec = useMemo(() => {
    const m: Record<string, { n: number; ok: number }> = {};
    for (const q of exam.questions) { m[q.section] ??= { n: 0, ok: 0 }; m[q.section].n++; if (q.result?.correct) m[q.section].ok++; }
    return Object.entries(m).sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }));
  }, [exam]);
  const weak = bySec.filter(([, v]) => v.ok / v.n < 0.6).map(([s]) => s);
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">ผลการสอบ: {exam.title}</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card title="คะแนน"><div className="text-4xl font-bold">{Math.round((exam.score ?? 0) * 100)}%</div><div className="text-sm text-muted">{exam.questions.filter((q) => q.result?.correct).length} / {exam.questions.length} ข้อ</div></Card>
        <Card title="รายหัวข้อ" className="md:col-span-2"><div className="space-y-1">{bySec.map(([s, v]) => <div key={s} className="flex items-center gap-2 text-sm"><span className="w-64 truncate">{sectionTitle(DEFAULT_SUBJECT, s)}</span><div className="flex-1"><Bar value={v.ok / v.n} /></div><span className="w-12 text-right">{v.ok}/{v.n}</span></div>)}</div></Card>
      </div>
      {weak.length > 0 && <Card title="หัวข้อที่ควรทบทวน"><div className="flex flex-wrap gap-2">{weak.map((s) => <Button key={s} onClick={() => go({ page: "practice", subject: DEFAULT_SUBJECT, section: s, mode: "guided" })}>{sectionTitle(DEFAULT_SUBJECT, s)}</Button>)}</div></Card>}
      <div className="flex gap-2"><Button variant="primary" onClick={onRetake}>สอบใหม่ (seed ใหม่)</Button></div>
      {exam.questions.map((q, k) => <ReviewItem key={k} q={q} k={k} />)}
    </div>
  );
}

function ReviewItem({ q, k }: { q: ExamQuestion; k: number }) {
  const [sol, setSol] = useState<{ answerTex: string; steps: Step[] } | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const show = async () => { try { setSol(await (await getBackend()).math("reveal", { templateId: q.templateId, seed: q.seed, difficulty: q.difficulty })); } catch (e) { setErr(e); } };
  return (
    <Card title={<span>ข้อ {k + 1} {q.result?.correct ? <Badge tone="good">ถูก</Badge> : <Badge tone="bad">ผิด</Badge>}</span>}>
      <p><Tex text={q.statement} /></p>
      <MathBlock tex={q.display} />
      <p className="text-sm">คำตอบของคุณ: <code>{q.answer || "—"}</code> {q.result?.feedback && <span className="text-muted">({q.result.feedback})</span>}</p>
      {!sol ? <Button className="mt-2" onClick={show}>ดูเฉลยพร้อมวิธีทำ</Button> : (
        <div className="mt-2 space-y-1 rounded bg-bg p-2 text-sm">
          {sol.steps.map((s, i) => <div key={i}><b>{i + 1}.</b> <Tex text={s.explain} />{s.after && <MathBlock tex={s.after} />}</div>)}
          <div className="font-semibold">คำตอบ: <MathBlock tex={sol.answerTex} /></div>
        </div>
      )}
      <ErrorBox error={err} />
    </Card>
  );
}
