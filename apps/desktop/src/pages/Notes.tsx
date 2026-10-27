import { useState } from "react";
import { getBackend } from "../lib/backend";
import { DEFAULT_SUBJECT, sectionTitle } from "../lib/content";
import { useData } from "../lib/hooks";
import { useApp } from "../lib/store";
import type { Bookmark, Note } from "../lib/types";
import { Tex } from "../components/Tex";
import { Button, Card } from "../components/ui";

export default function Notes() {
  const { go, touch } = useApp();
  const notes = useData((be) => be.db<Note[]>({ op: "list_notes" }));
  const bookmarks = useData((be) => be.db<Bookmark[]>({ op: "list_bookmarks" }));
  const [editing, setEditing] = useState<Note | null>(null);
  const [filter, setFilter] = useState("");
  const list = (notes.data ?? []).filter((n) => !filter || n.body.toLowerCase().includes(filter.toLowerCase()) || n.section.startsWith(filter)).sort((a, b) => b.updatedAt - a.updatedAt);
  const save = async () => { if (!editing) return; await (await getBackend()).db({ op: "save_note", id: editing.id, section: editing.section, body: editing.body }); setEditing(null); touch(); };
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">บันทึกและบุ๊กมาร์ก</h1>
      <Card title="บุ๊กมาร์ก">{bookmarks.data?.length ? <div className="flex flex-wrap gap-2">{bookmarks.data.map((b) => <Button key={b.section} onClick={() => go({ page: "lessons", subject: DEFAULT_SUBJECT, section: b.section })}>{sectionTitle(DEFAULT_SUBJECT, b.section)}</Button>)}</div> : <p className="text-sm text-muted">ยังไม่มีบุ๊กมาร์ก (กด ☆ ในหน้าบทเรียน)</p>}</Card>
      <Card title={`บันทึก (${list.length})`} actions={<input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="ค้นหาบันทึก" className="rounded border border-line bg-bg px-2 py-1 text-sm" aria-label="ค้นหาบันทึก" />}>
        {!list.length && <p className="text-sm text-muted">ยังไม่มีบันทึก เพิ่มได้จากแผงขวาในหน้าบทเรียน</p>}
        <ul className="space-y-2">{list.map((n) => (
          <li key={n.id} className="rounded border border-line p-3">
            <div className="mb-1 flex items-center justify-between text-xs text-muted"><button className="text-accent underline" onClick={() => go({ page: "lessons", subject: DEFAULT_SUBJECT, section: n.section })}>{sectionTitle(DEFAULT_SUBJECT, n.section)}</button><span>{new Date(n.updatedAt).toLocaleString("th-TH")}</span></div>
            {editing?.id === n.id ? (
              <div><textarea className="w-full rounded border border-line bg-bg p-2 text-sm" rows={4} value={editing.body} onChange={(e) => setEditing({ ...editing, body: e.target.value })} />
                <div className="mt-1 flex gap-2"><Button variant="primary" onClick={save}>บันทึก</Button><Button onClick={() => setEditing(null)}>ยกเลิก</Button></div></div>
            ) : <div className="text-sm"><Tex text={n.body} /></div>}
            {editing?.id !== n.id && <div className="mt-1 flex gap-2"><Button variant="ghost" onClick={() => setEditing(n)}>แก้ไข</Button>
              <Button variant="ghost" onClick={async () => { if (confirm("ลบบันทึกนี้?")) { await (await getBackend()).db({ op: "delete_note", id: n.id }); touch(); } }}>ลบ</Button></div>}
          </li>))}</ul>
      </Card>
    </div>
  );
}
