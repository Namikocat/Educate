import { SUBJECTS } from "../lib/content";
import { useAttempts } from "../lib/hooks";
import { useApp } from "../lib/store";
import { Badge, Button, Card } from "../components/ui";

export default function Subjects() {
  const { go, route } = useApp();
  const attempts = useAttempts();
  const mine = route.page === "courses";
  const practiced = new Set((attempts.data ?? []).map((a) => (a as { section: string }).section));
  const list = mine ? SUBJECTS.filter((s) => s.manifest.chapters.some((c) => c.sections.some((x) => practiced.has(x))) || s.manifest.id === "calculus") : SUBJECTS;
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">{mine ? "คอร์สของฉัน" : "วิชาทั้งหมด"}</h1>
      <p className="text-sm text-muted">แต่ละวิชาเป็นแพ็กเกจเนื้อหาที่ตรวจสอบโครงสร้าง เวอร์ชัน และความเข้ากันได้ก่อนโหลด</p>
      {list.map((s) => {
        const m = s.manifest;
        const nLessons = Object.keys(s.lessons).length;
        return (
          <Card key={m.id} title={<span>{m.name} <span className="text-sm font-normal text-muted">({m.nameEn})</span></span>}
            actions={<div className="flex gap-2">{m.completeness === "example" ? <Badge tone="accent">ตัวอย่าง — ไม่ใช่รายวิชาสมบูรณ์</Badge> : <Badge tone="good">รายวิชาหลัก</Badge>}<Badge>v{m.version}</Badge></div>}>
            <p className="mb-2 text-sm">{m.description}</p>
            {m.book && <p className="mb-2 text-xs text-muted">อ้างอิงตำรา: {m.book.title} {m.book.edition} ed. — {m.book.authors.join(", ")} (ใช้เพื่ออ้างอิงหัวข้อและหน้าเท่านั้น)</p>}
            <div className="mb-3 text-sm">บทเรียน {nLessons} บท · {m.chapters.length} บท · ความสามารถ: {m.capabilities.join(", ")}</div>
            {s.errors.length > 0 && <div className="mb-2 rounded border border-bad/40 bg-bad/10 p-2 text-xs text-bad">พบปัญหาในแพ็กเกจ: {s.errors.slice(0, 5).join("; ")}</div>}
            <div className="flex flex-wrap gap-2">
              {m.chapters.map((c) => <Button key={c.id} onClick={() => go({ page: "lessons", subject: m.id, section: c.sections[0] })}>บท {c.id}: {c.title}</Button>)}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
