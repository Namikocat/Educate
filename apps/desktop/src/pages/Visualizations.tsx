import { useState } from "react";
import { Card } from "../components/ui";
import { VizView } from "../components/VizView";

const GALLERY: { id: string; title: string; section: string; spec: Record<string, unknown>; editable?: boolean }[] = [
  { id: "riemann", title: "ผลรวมรีมันน์ (ปรับจำนวนสี่เหลี่ยม)", section: "5.1", spec: { type: "riemann", f: "x^2 + 1", a: 0, b: 2, n: 4, method: "left" }, editable: true },
  { id: "signed", title: "พื้นที่เชิงเครื่องหมาย", section: "5.3", spec: { type: "area", f: "x^3 - 3*x", a: -2, b: 2, signed: true }, editable: true },
  { id: "accum", title: "ฟังก์ชันสะสม F(x) = ∫ f", section: "5.4", spec: { type: "accumulation", f: "cos(x)", a: 0, b: 6.28 }, editable: true },
  { id: "between", title: "พื้นที่ระหว่างเส้นโค้ง (ปรับขอบเขต)", section: "5.6", spec: { type: "area_between", f: "x + 2", g: "x^2", a: -1, b: 2 } },
  { id: "disk", title: "วิธีจาน (Disk Method)", section: "6.1", spec: { type: "revolution", f: "sqrt(x)", a: 0, b: 4, axis: "x", method: "disk" } },
  { id: "washer", title: "วิธีแหวน (Washer Method)", section: "6.1", spec: { type: "revolution", f: "x", g: "x^2", a: 0, b: 1, axis: "x", method: "washer" } },
  { id: "cross", title: "หน้าตัดสี่เหลี่ยมจัตุรัส", section: "6.1", spec: { type: "cross_section", f: "2 - x", a: 0, b: 2, shape: "square" } },
  { id: "shell", title: "วิธีเปลือกทรงกระบอก (Shell Method)", section: "6.2", spec: { type: "revolution", f: "2*x - x^2", a: 0, b: 2, axis: "y", method: "shell" } },
  { id: "arc", title: "ความยาวส่วนโค้งด้วยเส้นหัก", section: "6.3", spec: { type: "arc", f: "x^3/6 + 1/(2*x)", a: 1, b: 3, n: 3 }, editable: true },
  { id: "surface", title: "พื้นที่ผิวของการหมุน", section: "6.4", spec: { type: "revolution", f: "sqrt(x)", a: 0, b: 2, axis: "x", method: "surface" } },
  { id: "inverse", title: "ฟังก์ชันผกผันและการสะท้อนข้าม y = x", section: "7.1", spec: { type: "inverse", f: "exp(x)", g: "ln(x)", a: -2, b: 3 }, editable: true },
  { id: "tangent", title: "เส้นสัมผัสของ ln x", section: "7.2", spec: { type: "tangent", f: "ln(x)", a: 0.1, b: 5, x0: 1 }, editable: true },
  { id: "lhop", title: "ลิมิต sin(3x)/x ใกล้ 0", section: "7.5", spec: { type: "function_plot", expressions: ["sin(3*x)/x", "3"], domain: [-3, 3] } },
  { id: "improper", title: "อินทิกรัลไม่ตรงแบบ: ขอบเขตบน → ∞", section: "8.8", spec: { type: "improper", f: "1/x^2", a: 1, b: 12 }, editable: true },
  { id: "singular", title: "จุดเอกฐานภายในช่วง", section: "8.8", spec: { type: "improper", f: "1/abs(x)^(2/3)", a: -1, b: 8, singularity: 0 } },
];

export default function Visualizations() {
  const [sel, setSel] = useState(GALLERY[0].id);
  const item = GALLERY.find((g) => g.id === sel)!;
  return (
    <div className="flex h-full">
      <aside className="w-72 shrink-0 overflow-y-auto border-r border-line bg-surface p-3">
        <h1 className="mb-2 text-lg font-bold">ภาพจำลองคณิตศาสตร์</h1>
        <ul>{GALLERY.map((g) => <li key={g.id}><button onClick={() => setSel(g.id)} className={`w-full rounded px-2 py-1.5 text-left text-sm ${g.id === sel ? "bg-accent/10 text-accent" : "hover:bg-bg"}`}><span className="text-xs text-muted">{g.section}</span> {g.title}</button></li>)}</ul>
      </aside>
      <div className="min-w-0 flex-1 overflow-y-auto p-6">
        <Card title={`${item.section} · ${item.title}`}>
          <VizView key={item.id} spec={item.spec} editable={item.editable} />
          {item.editable && <p className="mt-2 text-xs text-muted">แก้ไขฟังก์ชันได้ (ไวยากรณ์เดียวกับช่องคำตอบ เช่น <code>x^2</code>, <code>sin(x)</code>, <code>exp(-x)</code>) ระบบตรวจนิพจน์ก่อนวาดทุกครั้ง</p>}
        </Card>
      </div>
    </div>
  );
}
