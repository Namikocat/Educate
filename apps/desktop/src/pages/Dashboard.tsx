import { recommend, sectionMastery } from "@assess/mastery";
import { allSections, DEFAULT_SUBJECT, prerequisiteMap, sectionTitle, subjectById } from "../lib/content";
import { useAttempts, useData } from "../lib/hooks";
import { useApp, type Route } from "../lib/store";
import type { Bookmark, ExamSession } from "../lib/types";
import { Badge, Bar, Button, Card, Spinner } from "../components/ui";

export default function Dashboard() {
  const go = useApp((s) => s.go);
  const attempts = useAttempts();
  const lessons = useData((be) => be.db<Record<string, { status: string }>>({ op: "lesson_progress" }));
  const exams = useData((be) => be.db<ExamSession[]>({ op: "list_exams" }));
  const bookmarks = useData((be) => be.db<Bookmark[]>({ op: "list_bookmarks" }));
  const last = useData((be) => be.db<string | null>({ op: "get_kv", key: "last_lesson" }));
  if (attempts.loading && !attempts.data) return <div className="p-6"><Spinner /></div>;

  const subj = subjectById(DEFAULT_SUBJECT)!;
  const scope = allSections(DEFAULT_SUBJECT);
  const att = attempts.data ?? [];
  const recs = recommend(scope, att, prerequisiteMap(DEFAULT_SUBJECT)).slice(0, 5);
  const completed = Object.values(lessons.data ?? {}).filter((l) => l.status === "completed").length;
  const overall = scope.reduce((s, sec) => s + sectionMastery(att.filter((a) => a.section === sec)), 0) / scope.length;
  const correct = att.filter((a) => a.correct).length;
  const lastRoute: Route | null = (() => { try { return last.data ? JSON.parse(last.data) : null; } catch { return null; } })();
  const submitted = (exams.data ?? []).filter((e) => e.submittedAt).sort((a, b) => b.submittedAt! - a.submittedAt!).slice(0, 4);

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">แดชบอร์ด</h1>
      <div className="grid gap-4 md:grid-cols-4">
        <Card title="บทเรียนที่จบแล้ว"><div className="text-3xl font-bold">{completed}<span className="text-base text-muted"> / {scope.length}</span></div></Card>
        <Card title="โจทย์ที่ทำ"><div className="text-3xl font-bold">{att.length}</div><div className="text-sm text-muted">ถูก {correct} ข้อ</div></Card>
        <Card title="ความเชี่ยวชาญรวม (ประมาณ)"><Bar value={overall} /><p className="mt-2 text-xs text-muted">ค่าประมาณจากแบบจำลองเบื้องต้น ไม่ใช่คะแนนที่ผ่านการรับรอง</p></Card>
        <Card title="เรียนต่อจากครั้งก่อน">
          {lastRoute ? <Button variant="primary" onClick={() => go(lastRoute)}>{sectionTitle(lastRoute.subject ?? DEFAULT_SUBJECT, lastRoute.section ?? "5.1")}</Button>
            : <Button variant="primary" onClick={() => go({ page: "lessons", subject: DEFAULT_SUBJECT, section: "5.1" })}>เริ่มที่ 5.1</Button>}
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="แนะนำให้ฝึก (ปรับตามผลการเรียน)">
          <ul className="space-y-2">
            {recs.map((r) => (
              <li key={r.section} className="flex items-center justify-between gap-2">
                <div><div className="text-sm font-medium">{sectionTitle(DEFAULT_SUBJECT, r.section)}</div><div className="text-xs text-muted">{r.reason} · ระดับ {r.difficulty}</div></div>
                <Button onClick={() => go({ page: "practice", subject: DEFAULT_SUBJECT, section: r.section, mode: "free" })}>ฝึก</Button>
              </li>
            ))}
          </ul>
          <Button className="mt-3" onClick={() => go({ page: "practice", subject: DEFAULT_SUBJECT, mode: "weak" })}>ทบทวนจุดอ่อนอัตโนมัติ</Button>
        </Card>
        <Card title="ผลสอบล่าสุด" actions={<Button onClick={() => go({ page: "exam" })}>ศูนย์สอบ</Button>}>
          {submitted.length ? <ul className="space-y-1 text-sm">{submitted.map((e) => <li key={e.id} className="flex justify-between"><span>{e.title}</span><Badge tone={(e.score ?? 0) >= 0.5 ? "good" : "bad"}>{Math.round((e.score ?? 0) * 100)}%</Badge></li>)}</ul>
            : <p className="text-sm text-muted">ยังไม่มีผลสอบ</p>}
        </Card>
      </div>
      <Card title={`${subj.manifest.name}`}>
        <div className="grid gap-x-6 gap-y-2 md:grid-cols-2">
          {subj.manifest.chapters.flatMap((c) => c.sections).map((sec) => (
            <button key={sec} onClick={() => go({ page: "lessons", subject: DEFAULT_SUBJECT, section: sec })} className="flex items-center gap-3 rounded px-1 py-0.5 text-left hover:bg-bg">
              <span className="w-56 truncate text-sm">{sectionTitle(DEFAULT_SUBJECT, sec)}</span>
              <div className="flex-1"><Bar value={sectionMastery(att.filter((a) => a.section === sec))} /></div>
              {lessons.data?.[sec]?.status === "completed" && <Badge tone="good">อ่านแล้ว</Badge>}
            </button>
          ))}
        </div>
      </Card>
      {!!bookmarks.data?.length && (
        <Card title="บุ๊กมาร์ก">
          <div className="flex flex-wrap gap-2">{bookmarks.data.map((b) => <Button key={b.section} onClick={() => go({ page: "lessons", subject: DEFAULT_SUBJECT, section: b.section })}>{sectionTitle(DEFAULT_SUBJECT, b.section)}</Button>)}</div>
        </Card>
      )}
    </div>
  );
}
