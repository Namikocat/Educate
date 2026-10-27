import { useState } from "react";
import { getBackend } from "../lib/backend";
import { useData } from "../lib/hooks";
import { useApp } from "../lib/store";
import { Button, Card, ErrorBox, Select } from "../components/ui";

export default function Settings() {
  const { settings, setSettings, profile, touch } = useApp();
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const ping = useData((be) => be.math<{ engine: string; rules: string; templates: number }>("ping"));
  const backupPath = useData((be) => be.db<string>({ op: "backup" }), []);

  const doExport = async () => {
    try {
      const be = await getBackend();
      const data = await be.db<string>({ op: "export" });
      const where = await be.saveFile(`unilearn-backup-${new Date().toISOString().slice(0, 10)}.json`, data, false);
      setMsg(`ส่งออกข้อมูลแล้ว: ${where}`);
    } catch (e) { setErr(e); }
  };
  const doImport = async (file: File) => {
    try {
      if (file.size > 20 * 1024 * 1024) throw new Error("ไฟล์ใหญ่เกินไป");
      const text = await file.text();
      if (!confirm("การนำเข้าจะแทนที่ข้อมูลปัจจุบัน ระบบจะสำรองข้อมูลเดิมก่อน ยืนยัน?")) return;
      await (await getBackend()).db({ op: "import", data: text });
      setMsg("นำเข้าข้อมูลสำเร็จ กรุณาเปิดโปรแกรมใหม่"); touch();
    } catch (e) { setErr(e); }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">ตั้งค่า</h1>
      <Card title="การแสดงผล">
        <div className="grid gap-3 md:grid-cols-3">
          <Select label="ธีม" value={settings.theme} onChange={(v) => setSettings({ theme: v })} options={[{ value: "system", label: "ตามระบบ" }, { value: "light", label: "สว่าง" }, { value: "dark", label: "มืด" }]} />
          <Select label="ขนาดตัวอักษร" value={settings.fontScale} onChange={(v) => setSettings({ fontScale: v })} options={[0.9, 1, 1.1, 1.25, 1.4].map((v) => ({ value: v, label: `${Math.round(v * 100)}%` }))} />
          <Select label="ระดับคำอธิบายเริ่มต้น" value={settings.level} onChange={(v) => setSettings({ level: v })} options={[{ value: "beginner", label: "พื้นฐาน" }, { value: "standard", label: "มาตรฐาน" }, { value: "advanced", label: "เชิงลึก" }]} />
        </div>
        <div className="mt-3 flex flex-wrap gap-2"><Button onClick={() => setSettings({ leftPanel: true, rightPanel: true, focusMode: false })}>รีเซ็ตเลย์เอาต์</Button></div>
      </Card>
      <Card title="AI Tutor (ไม่บังคับ)">
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={settings.aiEnabled} onChange={(e) => setSettings({ aiEnabled: e.target.checked })} />เปิดใช้ AI Tutor ผ่าน Claude Code CLI</label>
        <p className="mt-1 text-xs text-muted">เมื่อปิด ระบบจะไม่เรียก Claude CLI เลย ทุกฟีเจอร์การเรียนยังทำงานแบบออฟไลน์</p>
      </Card>
      <Card title="ข้อมูลของฉัน">
        <p className="mb-2 text-sm">โปรไฟล์: {profile?.name}</p>
        <p className="mb-2 text-xs text-muted">ฐานข้อมูล: {backupPath.data ?? "…"}</p>
        <div className="flex flex-wrap gap-2">
          <Button onClick={doExport}>ส่งออกข้อมูล (JSON)</Button>
          <label className="inline-flex cursor-pointer items-center rounded-md border border-line px-3 py-1.5 text-sm hover:bg-bg">นำเข้าข้อมูล<input type="file" accept="application/json" className="hidden" onChange={(e) => e.target.files?.[0] && doImport(e.target.files[0])} /></label>
        </div>
        {msg && <p className="mt-2 text-sm text-good">{msg}</p>}
        <ErrorBox error={err} />
      </Card>
      <Card title="เกี่ยวกับ">
        <ul className="text-sm"><li>UniLearn Studio 1.0.1</li>
          <li>เครื่องคำนวณ: {ping.data ? `engine ${ping.data.engine}, rules ${ping.data.rules}, ${ping.data.templates} ชุดโจทย์` : "…"}</li>
          <li className="text-xs text-muted">เนื้อหาคำอธิบายเขียนขึ้นใหม่ อ้างอิงหัวข้อ/หน้าจาก Thomas' Calculus 14th ed. เพื่อการศึกษาส่วนบุคคล ไม่ได้แจกจ่ายเนื้อหาตำรา</li></ul>
      </Card>
    </div>
  );
}
