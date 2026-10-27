import { recommend, sectionMastery, weaknessCategories } from "@assess/mastery";
import { allSections, DEFAULT_SUBJECT, prerequisiteMap, sectionTitle } from "../lib/content";
import { useAttempts, useData } from "../lib/hooks";
import { useApp } from "../lib/store";
import type { ExamSession } from "../lib/types";
import { Bar, Button, Card, Spinner } from "../components/ui";

const ERR: Record<string, string> = { sign_error: "เครื่องหมายผิด", coefficient_error: "สัมประสิทธิ์ผิด", constant_offset: "ค่าคงที่คลาดเคลื่อน", differentiated_instead: "หาอนุพันธ์แทนอินทิกรัล" };

export default function Progress() {
  const go = useApp((s) => s.go);
  const attempts = useAttempts();
  const exams = useData((be) => be.db<ExamSession[]>({ op: "list_exams" }));
  const sessions = useData((be) => be.db<{ startedAt: number; endedAt: number; activity: string }[]>({ op: "list_sessions" }));
  if (attempts.loading && !attempts.data) return <div className="p-6"><Spinner /></div>;
  const att = attempts.data ?? [];
  const secs = allSections(DEFAULT_SUBJECT);
  const recs = recommend(secs, att, prerequisiteMap(DEFAULT_SUBJECT)).slice(0, 6);
  const weak = weaknessCategories(att);
  const totalMin = Math.round((sessions.data ?? []).reduce((s, x) => s + Math.max(0, x.endedAt - x.startedAt), 0) / 60000);
  const avgTime = att.length ? Math.round(att.reduce((s, a) => s + a.timeMs, 0) / att.length / 1000) : 0;
  const hints = att.reduce((s, a) => s + a.hintsUsed, 0);
  const revealed = att.filter((a) => a.solutionRevealed).length;
  const days: Record<string, number> = {};
  for (const a of att) { const d = new Date(a.at).toLocaleDateString("th-TH"); days[d] = (days[d] ?? 0) + 1; }

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">ความก้าวหน้าในการเรียน</h1>
      <div className="grid gap-4 md:grid-cols-5">
        <Card title="โจทย์ทั้งหมด"><div className="text-2xl font-bold">{att.length}</div></Card>
        <Card title="ตอบถูก"><div className="text-2xl font-bold">{att.length ? Math.round((att.filter((a) => a.correct).length / att.length) * 100) : 0}%</div></Card>
        <Card title="เวลาเฉลี่ยต่อข้อ"><div className="text-2xl font-bold">{avgTime} วิ</div></Card>
        <Card title="ใช้คำใบ้ / ดูเฉลย"><div className="text-2xl font-bold">{hints} / {revealed}</div></Card>
        <Card title="เวลาเรียนรวม"><div className="text-2xl font-bold">{totalMin} นาที</div></Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="ความเชี่ยวชาญรายหัวข้อ">
          <div className="space-y-1">{secs.map((s) => { const list = att.filter((a) => a.section === s); return (
            <div key={s} className="flex items-center gap-2 text-sm"><span className="w-60 truncate">{sectionTitle(DEFAULT_SUBJECT, s)}</span><div className="flex-1"><Bar value={sectionMastery(list)} /></div><span className="w-10 text-right text-xs text-muted">{list.length}</span></div>); })}</div>
          <details className="mt-3 text-xs text-muted"><summary>แบบจำลองความเชี่ยวชาญคำนวณอย่างไร?</summary>
            <p className="mt-1">คะแนนแต่ละครั้ง = ถูก/ผิด × น้ำหนักความยาก (0.7/1.0/1.2) × ตัวลดเมื่อใช้คำใบ้ (−15% ต่อคำใบ้) หรือดูเฉลย (−50%) ถ่วงน้ำหนักให้ครั้งล่าสุดมากกว่า (0.85 ต่อครั้ง) และลดลงตามเวลา (ครึ่งชีวิตประมาณ 3 สัปดาห์) แล้วปรับลดเมื่อทำน้อยกว่า ~3 ข้อ เป็นค่าประมาณเชิงฮิวริสติก ไม่ใช่การวัดที่ผ่านการรับรองทางสถิติ</p></details>
        </Card>
        <div className="space-y-4">
          <Card title="แนะนำให้ฝึกต่อ">{recs.map((r) => <div key={r.section} className="mb-1 flex items-center justify-between text-sm"><span>{sectionTitle(DEFAULT_SUBJECT, r.section)} <span className="text-xs text-muted">— {r.reason}</span></span><Button onClick={() => go({ page: "practice", subject: DEFAULT_SUBJECT, section: r.section, mode: "free" })}>ฝึก</Button></div>)}</Card>
          <Card title="ประเภทข้อผิดพลาดที่พบบ่อย">{weak.length ? weak.map((w) => <div key={w.errorType} className="flex justify-between text-sm"><span>{ERR[w.errorType] ?? w.errorType}</span><span>{w.count} ครั้ง</span></div>) : <p className="text-sm text-muted">ยังไม่มีข้อมูล</p>}</Card>
          <Card title="ผลสอบ">{(exams.data ?? []).filter((e) => e.submittedAt).map((e) => <div key={e.id} className="flex justify-between text-sm"><span>{new Date(e.startedAt).toLocaleDateString("th-TH")} {e.title}</span><span>{Math.round((e.score ?? 0) * 100)}%</span></div>)}</Card>
          <Card title="กิจกรรมรายวัน">{Object.entries(days).slice(-10).map(([d, c]) => <div key={d} className="flex items-center gap-2 text-sm"><span className="w-28">{d}</span><div className="h-2 rounded bg-accent" style={{ width: Math.min(300, c * 12) }} /><span>{c}</span></div>)}</Card>
        </div>
      </div>
    </div>
  );
}
