import { recommend } from "@assess/mastery";
import { useCallback, useEffect, useRef, useState } from "react";
import { getBackend } from "../lib/backend";
import { allSections, DEFAULT_SUBJECT, prerequisiteMap, sectionTitle, SUBJECTS } from "../lib/content";
import { randomSeed, useAttempts, useData } from "../lib/hooks";
import { useApp } from "../lib/store";
import type { AttemptRecord, CheckResult, Problem, TemplateMeta } from "../lib/types";
import { MathInput } from "../components/MathInput";
import { MathBlock, Tex } from "../components/Tex";
import { Badge, Button, Card, ErrorBox, Select, Spinner } from "../components/ui";
import { VizView } from "../components/VizView";

const ERROR_LABEL: Record<string, string> = { sign_error: "เครื่องหมายผิด", coefficient_error: "สัมประสิทธิ์ผิด", constant_offset: "ค่าคงที่คลาดเคลื่อน", differentiated_instead: "หาอนุพันธ์แทนอินทิกรัล" };

export default function Practice() {
  const { route, go, setTutor, touch } = useApp();
  const subject = route.subject ?? DEFAULT_SUBJECT;
  const attempts = useAttempts();
  const [mode, setMode] = useState(route.mode ?? "free");
  const [section, setSection] = useState(route.section ?? "5.5");
  const [difficulty, setDifficulty] = useState(mode === "guided" ? 1 : 2);
  const [family, setFamily] = useState<string>("");
  const families = useData((be) => be.math<TemplateMeta[]>("list_templates", { subject, section }), [subject, section]);

  const [problem, setProblem] = useState<Problem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<CheckResult | null>(null);
  const [hints, setHints] = useState(0);
  const [steps, setSteps] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [showViz, setShowViz] = useState(false);
  const [tries, setTries] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const startedAt = useRef(Date.now());

  // weakness review: pick the highest-priority section deterministically from the mastery model
  useEffect(() => {
    if (mode !== "weak" || !attempts.data) return;
    const r = recommend(allSections(subject), attempts.data, prerequisiteMap(subject))[0];
    if (r) { setSection(r.section); setDifficulty(r.difficulty); }
  }, [mode, attempts.data, subject]);

  const newProblem = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const be = await getBackend();
      const recent = (attempts.data ?? []).slice(-300).map((a) => (a as AttemptRecord & { canonical?: string }).canonical).filter(Boolean);
      const p = await be.math<Problem>("generate_for_section", { subject, section, seed: randomSeed(), difficulty, excludeCanonical: recent, templateIds: family ? [family] : undefined });
      setProblem(p); setAnswer(""); setResult(null); setHints(mode === "guided" ? 1 : 0); setSteps(0); setRevealed(false); setTries(0); setSelected(null);
      setShowViz(mode === "guided" && !!p.viz); startedAt.current = Date.now();
      setTutor({ subject, section, problem: p });
    } catch (e) { setError(e); } finally { setLoading(false); }
  }, [subject, section, difficulty, family, mode, attempts.data, setTutor]);

  useEffect(() => { newProblem(); /* new problem whenever the selection changes */ // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [section, difficulty, family, mode]);

  const check = useCallback(async (override?: string) => {
    if (!problem) return;
    const ans = override ?? answer;
    if (!ans.trim()) return;
    const be = await getBackend();
    const r = await be.math<CheckResult>("check", { templateId: problem.templateId, seed: problem.seed, difficulty: problem.difficulty, answer: ans });
    setResult(r);
    if (r.parseError) return; // input errors are not counted as attempts
    setTries((t) => t + 1);
    await be.db({ op: "record_attempt", attempt: { section: problem.section, templateId: problem.templateId, difficulty: problem.difficulty, correct: r.correct, hintsUsed: hints,
      solutionRevealed: revealed || steps > 0, errorType: r.errorType ?? null, timeMs: Date.now() - startedAt.current, at: Date.now(), problemId: problem.id, canonical: problem.canonical, answer: ans.slice(0, 400) } });
    setTutor({ subject, section, problem, attempt: ans });
    touch();
  }, [problem, answer, hints, revealed, steps, subject, section, setTutor, touch]);

  // keyboard shortcuts within the workspace
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "Enter") { e.preventDefault(); check(); }
      if (e.altKey && e.key.toLowerCase() === "n") { e.preventDefault(); newProblem(); }
      if (e.altKey && e.key.toLowerCase() === "h") { e.preventDefault(); setHints((x) => x + 1); }
      if (e.altKey && e.key.toLowerCase() === "s") { e.preventDefault(); setSteps((x) => x + 1); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [check, newProblem]);

  const allSecs = SUBJECTS.find((s) => s.manifest.id === subject)?.manifest.chapters.flatMap((c) => c.sections) ?? [];
  const totalSteps = problem?.steps?.length ?? 0;
  const askTutor = (stepIdx?: number) => {
    if (!problem) return;
    setTutor({ subject, section, problem, attempt: answer || undefined, selectedStep: stepIdx !== undefined && problem.steps ? { index: stepIdx, step: problem.steps[stepIdx] } : undefined });
    go({ page: "tutor" });
  };

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <div className="flex flex-wrap items-end gap-3">
        <h1 className="mr-4 text-2xl font-bold">ฝึกทำโจทย์</h1>
        <div className="flex gap-1" role="tablist" aria-label="โหมดการฝึก">
          {([["guided", "มีคำแนะนำ"], ["free", "อิสระ"], ["weak", "ทบทวนจุดอ่อน"]] as const).map(([m, l]) =>
            <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)} className={`rounded-md px-3 py-1.5 text-sm ${mode === m ? "bg-accent text-white" : "border border-line"}`}>{l}</button>)}
        </div>
        <Select label="หัวข้อ" value={section} onChange={(v) => { setSection(v); setFamily(""); }} options={allSecs.map((s) => ({ value: s, label: sectionTitle(subject, s) }))} />
        <Select label="ระดับความยาก" value={difficulty} onChange={setDifficulty} options={[{ value: 1, label: "1 ง่าย" }, { value: 2, label: "2 ปานกลาง" }, { value: 3, label: "3 ยาก" }]} />
        <Select label="ชุดโจทย์" value={family} onChange={setFamily} options={[{ value: "", label: `ทุกชุด (${families.data?.length ?? 0})` }, ...(families.data ?? []).map((f) => ({ value: f.id, label: f.title }))]} />
      </div>
      {mode === "weak" && <p className="text-sm text-muted">ระบบเลือกหัวข้อจากแบบจำลองความเชี่ยวชาญ (คะแนนต่ำ ตอบผิดบ่อย หรือไม่ได้ทบทวนนาน)</p>}
      <ErrorBox error={error} />
      {loading && !problem && <Spinner label="กำลังสร้างโจทย์ด้วยเครื่องสร้างโจทย์แบบกำหนดได้…" />}
      {problem && (
        <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
          <div className="space-y-4">
            <Card title={<span>{problem.title} <Badge>ระดับ {problem.difficulty}</Badge></span>}
              actions={<span className="text-xs text-muted" title="สร้างซ้ำได้จาก template + seed">#{problem.templateId.split(".").slice(-1)[0]} · seed {problem.seed}</span>}>
              <p className="mb-2 text-[1.05rem]"><Tex text={problem.statement} /></p>
              <MathBlock tex={problem.display} className="my-3 text-lg" />
              {problem.answerType === "choice" ? (
                <div className="flex flex-wrap gap-2">{problem.choices!.map((c) => <Button key={c.id} variant={result && answer === c.id ? (result.correct ? "primary" : "danger") : "default"} onClick={() => { setAnswer(c.id); check(c.id); }}>{c.label}</Button>)}</div>
              ) : (
                <MathInput value={answer} onChange={setAnswer} onSubmit={() => check()} allowDiverges={problem.answerType === "improper"} />
              )}
              {result && (
                <div role="status" className={`mt-3 rounded-md border p-3 text-sm ${result.parseError ? "border-line" : result.correct ? "border-good/40 bg-good/10" : "border-bad/40 bg-bad/10"}`}>
                  {result.parseError ? <span className="text-bad">อ่านคำตอบไม่ได้: {result.parseError}</span> : result.correct ? <b className="text-good">ถูกต้อง!</b> : <b className="text-bad">ยังไม่ถูกต้อง</b>}
                  {result.feedback && <div className="mt-1">{result.feedback}</div>}
                  {result.errorType && <div className="mt-1 text-xs">ประเภทข้อผิดพลาด: {ERROR_LABEL[result.errorType] ?? result.errorType}</div>}
                  {result.correct && result.method === "numeric" && <div className="mt-1 text-xs text-muted">ตรวจความเท่ากันด้วยการเทียบค่าเชิงตัวเลขความละเอียดสูง</div>}
                </div>
              )}
              <div className="mt-3 flex flex-wrap gap-2">
                {problem.answerType !== "choice" && <Button variant="primary" onClick={() => check()} title="Ctrl+Enter">ตรวจคำตอบ</Button>}
                <Button onClick={() => setHints((h) => h + 1)} disabled={hints >= (problem.hints?.length ?? 0)} title="Alt+H">คำใบ้</Button>
                <Button onClick={() => setSteps((s) => Math.min(totalSteps, s + 1))} disabled={steps >= totalSteps} title="Alt+S">แสดงขั้นถัดไป</Button>
                <Button onClick={() => { setSteps(totalSteps); setRevealed(true); }}>แสดงวิธีทำทั้งหมด</Button>
                <Button onClick={newProblem} disabled={loading} title="Alt+N">{loading ? "กำลังสร้าง…" : "โจทย์ใหม่"}</Button>
                {problem.viz && <Button variant="ghost" onClick={() => setShowViz(!showViz)}>{showViz ? "ซ่อนกราฟ" : "แสดงกราฟ"}</Button>}
                <Button variant="ghost" onClick={() => go({ page: "lessons", subject, section: problem.section })}>บทเรียนที่เกี่ยวข้อง</Button>
                <Button variant="ghost" onClick={() => askTutor()}>ถาม Claude</Button>
              </div>
              {tries > 0 && <p className="mt-2 text-xs text-muted">จำนวนครั้งที่ตอบ: {tries}</p>}
            </Card>
            {hints > 0 && <Card title="คำใบ้"><ol className="list-decimal space-y-1 pl-5">{problem.hints!.slice(0, hints).map((h, i) => <li key={i}><Tex text={h} /></li>)}</ol></Card>}
            {steps > 0 && (
              <Card title="วิธีทำทีละขั้น (ตรวจสอบโดยเครื่องคำนวณสัญลักษณ์)">
                <ol className="space-y-2">
                  {problem.steps!.slice(0, steps).map((s, i) => (
                    <li key={i} className={`rounded-md border p-2 ${selected === i ? "border-accent" : "border-line"}`}>
                      <div className="flex items-start justify-between gap-2">
                        <div className="text-sm"><span className="mr-1 font-semibold">ขั้นที่ {i + 1}.</span><Tex text={s.explain} /></div>
                        <div className="flex shrink-0 items-center gap-1">
                          {s.verified === true && <Badge tone="good">{s.checkMethod === "numeric" ? "ตรวจเชิงตัวเลข" : "ตรวจแล้ว"}</Badge>}
                          <button className="text-xs text-accent underline" onClick={() => { setSelected(i); askTutor(i); }}>อธิบายขั้นนี้</button>
                        </div>
                      </div>
                      {(s.before || s.after) && <div className="mt-1 flex flex-wrap items-center gap-2 overflow-x-auto">{s.before && <MathBlock tex={s.before} />}{s.before && s.after && <span>⟹</span>}{s.after && <MathBlock tex={s.after} />}</div>}
                      {s.assumptions.length > 0 && <div className="text-xs text-muted">เงื่อนไข: {s.assumptions.join("; ")}</div>}
                    </li>
                  ))}
                </ol>
                {steps >= totalSteps && problem.answerTex && (
                  <div className="mt-3 grid gap-2 rounded-md bg-bg p-3 md:grid-cols-2">
                    <div><div className="text-xs text-muted">คำตอบที่ถูกต้อง</div><MathBlock tex={problem.answerTex} /></div>
                    <div><div className="text-xs text-muted">คำตอบของคุณ</div>{answer ? <code className="text-sm">{answer}</code> : <span className="text-sm text-muted">ยังไม่ได้ตอบ</span>}</div>
                  </div>
                )}
              </Card>
            )}
          </div>
          <div className="space-y-4">
            {showViz && problem.viz && <Card title="ภาพประกอบโจทย์"><VizView spec={problem.viz} /></Card>}
            <Card title="เกี่ยวกับโจทย์นี้">
              <ul className="space-y-1 text-sm">
                <li>หัวข้อ: {sectionTitle(subject, problem.section)}</li>
                <li>จุดประสงค์: {problem.objectives.join(", ")}</li>
                <li>การตรวจคำตอบอ้างอิง: {problem.verification.answer === "symbolic" ? "พิสูจน์เชิงสัญลักษณ์" : problem.verification.answer === "numeric" ? "เทียบเชิงตัวเลขความละเอียดสูง" : "ตรงตัว"}</li>
                <li className="text-xs text-muted">โจทย์สร้างโดยอัลกอริทึม (ไม่ใช้ AI) และสร้างซ้ำได้จาก ID: <code>{problem.id}</code></li>
              </ul>
            </Card>
            <Card title="แป้นลัด"><ul className="text-xs text-muted"><li>Ctrl+Enter ตรวจคำตอบ</li><li>Alt+H คำใบ้ · Alt+S ขั้นถัดไป</li><li>Alt+N โจทย์ใหม่</li></ul></Card>
          </div>
        </div>
      )}
    </div>
  );
}
