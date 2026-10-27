/** Content packages are bundled at build time from /subjects and validated on load. */
import { loadSubject, type Lesson, type LoadedSubject, type SubjectManifest } from "@curriculum/registry";

const manifests = import.meta.glob("@subjects/*/manifest.json", { eager: true, import: "default" }) as Record<string, SubjectManifest>;
const lessonFiles = import.meta.glob("@subjects/*/lessons/*.json", { eager: true, import: "default" }) as Record<string, Lesson>;

function dirOf(path: string) {
  const m = /subjects\/([^/]+)\//.exec(path);
  return m ? m[1] : "";
}

export const SUBJECTS: LoadedSubject[] = Object.entries(manifests).map(([path, manifest]) => {
  const dir = dirOf(path);
  const lessons = Object.entries(lessonFiles).filter(([p]) => dirOf(p) === dir).map(([, l]) => l);
  return loadSubject(manifest, lessons);
}).sort((a, b) => (a.manifest.completeness === "full-course" ? -1 : 1) - (b.manifest.completeness === "full-course" ? -1 : 1));

export const subjectById = (id: string) => SUBJECTS.find((s) => s.manifest.id === id);
export const DEFAULT_SUBJECT = "calculus";

export function sectionTitle(subject: string, section: string): string {
  const l = subjectById(subject)?.lessons[section];
  return l ? `${section} ${l.title}` : section;
}

export function allSections(subject: string): string[] {
  return subjectById(subject)?.manifest.chapters.flatMap((c) => c.sections) ?? [];
}

export function prerequisiteMap(subject: string): Record<string, string[]> {
  const s = subjectById(subject);
  const out: Record<string, string[]> = {};
  for (const [sec, l] of Object.entries(s?.lessons ?? {})) out[sec] = l.prerequisites;
  return out;
}

export function searchLessons(q: string) {
  const needle = q.trim().toLowerCase();
  if (!needle) return [];
  const hits: { subject: string; section: string; title: string; match: string }[] = [];
  for (const s of SUBJECTS) {
    for (const l of Object.values(s.lessons)) {
      const fields = [l.title, l.titleEn, ...l.definitions.map((d) => `${d.term} ${d.termEn}`), ...l.objectives.map((o) => o.text)];
      const f = fields.find((x) => x.toLowerCase().includes(needle));
      if (f || l.section.startsWith(needle)) hits.push({ subject: s.manifest.id, section: l.section, title: `${l.title} (${l.titleEn})`, match: f ?? l.section });
    }
  }
  return hits.slice(0, 12);
}

export const EXAM_PRESETS: { id: string; label: string; sections: string[] }[] = [
  { id: "ch5", label: "บทที่ 5 อินทิกรัล", sections: ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6"] },
  { id: "ch6", label: "บทที่ 6 การประยุกต์ของอินทิกรัล", sections: ["6.1", "6.2", "6.3", "6.4"] },
  { id: "ch7", label: "บทที่ 7 ฟังก์ชันอดิศัย", sections: ["7.1", "7.2", "7.3", "7.5"] },
  { id: "ch8", label: "บทที่ 8 เทคนิคการอินทิเกรต", sections: ["8.1", "8.2", "8.3", "8.4", "8.5", "8.8"] },
  { id: "final", label: "สอบปลายภาค (ครบ 20 หัวข้อ)", sections: ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "6.1", "6.2", "6.3", "6.4", "7.1", "7.2", "7.3", "7.5", "8.1", "8.2", "8.3", "8.4", "8.5", "8.8"] },
];
