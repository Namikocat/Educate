import { useEffect, useRef, useState } from "react";
import { getBackend } from "../lib/backend";
import { DEFAULT_SUBJECT, subjectById } from "../lib/content";
import { useData } from "../lib/hooks";
import { useApp } from "../lib/store";
import type { Bookmark, Note } from "../lib/types";
import { MathBlock, Tex } from "../components/Tex";
import { Badge, Button, Card } from "../components/ui";
import { VizView } from "../components/VizView";

const LEVELS = [{ id: "beginner", label: "พื้นฐาน" }, { id: "standard", label: "มาตรฐาน" }, { id: "advanced", label: "เชิงลึก" }] as const;

export default function Lessons() {
  const { route, go, settings, setSettings, touch, setTutor } = useApp();
  const subjectId = route.subject ?? DEFAULT_SUBJECT;
  const subject = subjectById(subjectId)!;
  const section = route.section ?? subject.manifest.chapters[0].sections[0];
  const lesson = subject.lessons[section];
  const [level, setLevel] = useState(settings.level);
  const progress = useData((be) => be.db<Record<string, { status: string }>>({ op: "lesson_progress" }));
  const bookmarks = useData((be) => be.db<Bookmark[]>({ op: "list_bookmarks" }));
  const [rightW, setRightW] = useState(340);
  const dragging = useRef(false);

  useEffect(() => {
    getBackend().then(async (be) => {
      await be.db({ op: "set_lesson", section, status: "started" });
      await be.db({ op: "set_kv", key: "last_lesson", value: JSON.stringify({ page: "lessons", subject: subjectId, section }) });
    });
    setTutor({ subject: subjectId, section });
    document.getElementById("lesson-top")?.scrollIntoView();
  }, [section, subjectId, setTutor]);

  useEffect(() => {
    const move = (e: MouseEvent) => { if (dragging.current) setRightW(Math.min(560, Math.max(240, window.innerWidth - e.clientX))); };
    const up = () => (dragging.current = false);
    window.addEventListener("mousemove", move); window.addEventListener("mouseup", up);
    return () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
  }, []);

  const isBookmarked = bookmarks.data?.some((b) => b.section === section);
  const done = progress.data?.[section]?.status === "completed";
  const act = async (fn: () => Promise<unknown>) => { await fn(); touch(); };

  return (
    <div className="flex h-full">
      {settings.leftPanel && !settings.focusMode && (
        <aside className="hidden w-64 shrink-0 overflow-y-auto border-r border-line bg-surface p-3 lg:block" aria-label="สารบัญ">
          <div className="mb-2 text-xs font-semibold uppercase text-muted">{subject.manifest.name}</div>
          {subject.manifest.chapters.map((c) => (
            <div key={c.id} className="mb-3">
              <div className="text-sm font-semibold">บทที่ {c.id} {c.title}</div>
              <div className="text-xs text-muted">{c.titleEn}</div>
              <ul className="mt-1">
                {c.sections.map((s) => {
                  const st = progress.data?.[s]?.status;
                  return (
                    <li key={s}><button onClick={() => go({ page: "lessons", subject: subjectId, section: s })} aria-current={s === section ? "page" : undefined}
                      className={`flex w-full items-center gap-2 rounded px-2 py-1 text-left text-sm ${s === section ? "bg-accent/10 text-accent" : "hover:bg-bg"}`}>
                      <span className={`h-2 w-2 shrink-0 rounded-full ${st === "completed" ? "bg-good" : st === "started" ? "bg-accent/50" : "bg-line"}`} />
                      <span className="truncate">{s} {subject.lessons[s]?.title ?? "(ยังไม่มีบทเรียน)"}</span>
                    </button></li>
                  );
                })}
              </ul>
            </div>
          ))}
        </aside>
      )}
      <article className="min-w-0 flex-1 overflow-y-auto p-6" id="lesson-top">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <Button variant="ghost" onClick={() => setSettings({ leftPanel: !settings.leftPanel })}>{settings.leftPanel ? "ซ่อนสารบัญ" : "แสดงสารบัญ"}</Button>
          <Button variant="ghost" onClick={() => setSettings({ rightPanel: !settings.rightPanel })}>{settings.rightPanel ? "ซ่อนแผงขวา" : "แสดงแผงขวา"}</Button>
        </div>
        {!lesson ? <p>ยังไม่มีบทเรียนสำหรับหัวข้อนี้</p> : (
          <div className="prose-lesson mx-auto max-w-3xl space-y-5">
            <header>
              <div className="flex flex-wrap items-center gap-2 text-sm text-muted">
                <span>หัวข้อ {lesson.section}</span>
                <Badge tone={lesson.status === "machine-validated" ? "good" : "muted"}>{lesson.status === "machine-validated" ? "ตรวจด้วยเครื่องแล้ว · รอผู้เชี่ยวชาญตรวจ" : lesson.status}</Badge>
                {lesson.source?.verified && <span>อ้างอิง: Thomas' Calculus 14e §{lesson.section} หน้า {lesson.source.printedPages[0]}–{lesson.source.printedPages[1]}</span>}
              </div>
              <h1 className="text-2xl font-bold">{lesson.title}</h1>
              <div className="text-muted">{lesson.titleEn}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button variant="primary" onClick={() => go({ page: "practice", subject: subjectId, section, mode: "guided" })}>ฝึกแบบมีคำแนะนำ</Button>
                <Button onClick={() => go({ page: "practice", subject: subjectId, section, mode: "free" })}>ฝึกอิสระ</Button>
                <Button onClick={() => act(async () => (await getBackend()).db({ op: "set_lesson", section, status: "completed" }))} disabled={done}>{done ? "✓ อ่านจบแล้ว" : "ทำเครื่องหมายว่าอ่านจบ"}</Button>
                <Button variant="ghost" onClick={() => act(async () => (await getBackend()).db({ op: "toggle_bookmark", section }))}>{isBookmarked ? "★ บุ๊กมาร์กแล้ว" : "☆ บุ๊กมาร์ก"}</Button>
              </div>
            </header>

            <Card title="จุดประสงค์การเรียนรู้"><ul className="list-disc space-y-1 pl-5">{lesson.objectives.map((o) => <li key={o.id}><Tex text={o.text} /></li>)}</ul>
              {lesson.prerequisites.length > 0 && <p className="mt-2 text-sm text-muted">ความรู้พื้นฐานที่ควรมี: {lesson.prerequisites.map((p) => <button key={p} className="mr-2 text-accent underline" onClick={() => go({ page: "lessons", subject: subjectId, section: p })}>{p}</button>)}</p>}
            </Card>

            <section>
              <div className="mb-2 flex gap-1" role="tablist" aria-label="ระดับคำอธิบาย">
                {LEVELS.map((l) => <button key={l.id} role="tab" aria-selected={level === l.id} onClick={() => setLevel(l.id)} className={`rounded-md px-3 py-1 text-sm ${level === l.id ? "bg-accent text-white" : "border border-line"}`}>{l.label}</button>)}
              </div>
              <p className="text-[1.02rem]"><Tex text={lesson.levels[level]} /></p>
            </section>

            <Card title="นิยาม (Definitions)"><dl className="space-y-2">{lesson.definitions.map((d) => <div key={d.term}><dt className="font-semibold">{d.term} <span className="font-normal text-muted">({d.termEn})</span></dt><dd><Tex text={d.body} /></dd></div>)}</dl></Card>
            <Card title="ทฤษฎีบทและเงื่อนไข">{lesson.theorems.map((t) => <div key={t.name} className="mb-2"><div className="font-semibold">{t.name}</div><Tex text={t.statement} />{t.conditions && <div className="text-sm text-muted">เงื่อนไข: {t.conditions}</div>}</div>)}</Card>
            <Card title="สูตรสำคัญ">{lesson.formulas.map((f) => <div key={f.tex} className="flex flex-wrap items-center gap-3 border-b border-line py-1 last:border-0"><MathBlock tex={f.tex} />{f.note && <span className="text-sm text-muted"><Tex text={f.note} /></span>}</div>)}</Card>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold">ตัวอย่างพร้อมวิธีทำ</h2>
              {lesson.examples.map((ex, i) => <WorkedExample key={i} ex={ex} idx={i} validated={(lesson as any).validation?.examples?.[i]?.verified} />)}
            </section>

            {lesson.visualizations.length > 0 && <Card title="ภาพจำลองเชิงโต้ตอบ">{lesson.visualizations.map((v, i) => <div key={i} className="mb-4"><VizView spec={v} editable /></div>)}</Card>}

            <Card title="ข้อผิดพลาดที่พบบ่อย">{lesson.misconceptions.map((m, i) => <div key={i} className="mb-2 grid gap-1 md:grid-cols-2"><div className="rounded bg-bad/10 p-2 text-sm">✗ <Tex text={m.wrong} /></div><div className="rounded bg-good/10 p-2 text-sm">✓ <Tex text={m.right} /></div></div>)}</Card>
            <Card title="สรุป"><ul className="list-disc space-y-1 pl-5">{lesson.summary.map((s, i) => <li key={i}><Tex text={s} /></li>)}</ul></Card>
            <Card title="คำถามทบทวน">{lesson.review.map((r, i) => <ReviewQ key={i} q={r.q} a={r.a} />)}
              <Button className="mt-2" onClick={() => go({ page: "exam", section })}>แบบทดสอบหัวข้อนี้</Button></Card>
          </div>
        )}
      </article>
      {settings.rightPanel && !settings.focusMode && lesson && (
        <>
          <div className="hidden w-1 cursor-col-resize bg-line hover:bg-accent xl:block" onMouseDown={() => (dragging.current = true)} role="separator" aria-label="ปรับความกว้างแผงขวา" />
          <aside style={{ width: rightW }} className="hidden shrink-0 space-y-3 overflow-y-auto bg-surface p-3 xl:block">
            <NotesPanel section={section} />
            <Card title="อ้างอิงสูตร">{lesson.formulas.slice(0, 4).map((f) => <MathBlock key={f.tex} tex={f.tex} className="text-sm" />)}</Card>
            {lesson.visualizations[0] && <Card title="กราฟประกอบ"><VizView spec={lesson.visualizations[0]} /></Card>}
            <Card title="ถาม AI Tutor"><p className="mb-2 text-sm text-muted">ขอคำอธิบายเพิ่มเติมเกี่ยวกับหัวข้อนี้ (ไม่บังคับ ต้องติดตั้ง Claude CLI)</p><Button onClick={() => go({ page: "tutor" })}>เปิด AI Tutor</Button></Card>
          </aside>
        </>
      )}
    </div>
  );
}

function WorkedExample({ ex, idx, validated }: { ex: { title: string; problem: string; steps: string[]; answer: string }; idx: number; validated?: boolean | null }) {
  const [shown, setShown] = useState(0);
  return (
    <Card title={<span>ตัวอย่างที่ {idx + 1}: {ex.title} {validated && <Badge tone="good">ตรวจคำตอบด้วย SymPy แล้ว</Badge>}</span>}>
      <p className="mb-2"><Tex text={ex.problem} /></p>
      <ol className="list-decimal space-y-1 pl-5">{ex.steps.slice(0, shown).map((s, i) => <li key={i}><Tex text={s} /></li>)}</ol>
      {shown >= ex.steps.length ? <p className="mt-2 font-semibold">คำตอบ: <Tex text={ex.answer} /></p>
        : <div className="mt-2 flex gap-2"><Button onClick={() => setShown(shown + 1)}>แสดงขั้นถัดไป</Button><Button variant="ghost" onClick={() => setShown(ex.steps.length)}>แสดงทั้งหมด</Button></div>}
    </Card>
  );
}

function ReviewQ({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return <div className="mb-2"><Tex text={q} /> <button className="text-sm text-accent underline" onClick={() => setOpen(!open)}>{open ? "ซ่อนคำตอบ" : "ดูคำตอบ"}</button>{open && <div className="mt-1 rounded bg-bg p-2 text-sm"><Tex text={a} /></div>}</div>;
}

function NotesPanel({ section }: { section: string }) {
  const touch = useApp((s) => s.touch);
  const notes = useData((be) => be.db<Note[]>({ op: "list_notes" }), [section]);
  const mine = (notes.data ?? []).filter((n) => n.section === section);
  const [draft, setDraft] = useState("");
  const add = async () => {
    if (!draft.trim()) return;
    await (await getBackend()).db({ op: "save_note", section, body: draft.slice(0, 20000) });
    setDraft(""); touch();
  };
  return (
    <Card title="บันทึกของฉัน">
      <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={3} placeholder="จดบันทึก (รองรับ $LaTeX$)" className="w-full rounded border border-line bg-bg p-2 text-sm" aria-label="บันทึกใหม่" />
      <Button className="mt-1" onClick={add} disabled={!draft.trim()}>บันทึก</Button>
      <ul className="mt-2 space-y-2">{mine.map((n) => <li key={n.id} className="rounded bg-bg p-2 text-sm"><Tex text={n.body} /><div className="text-right"><button className="text-xs text-bad" onClick={async () => { await (await getBackend()).db({ op: "delete_note", id: n.id }); touch(); }}>ลบ</button></div></li>)}</ul>
    </Card>
  );
}
