/**
 * Subject package registry: data-driven, trusted packages only (no executable plugin loading).
 * Validates manifests and lessons, checks platform/engine compatibility and reports errors
 * instead of crashing the app.
 */
export const PLATFORM_CONTENT_API = 1;
export const AVAILABLE_ENGINES = ["sympy-math-engine@1", "viz-2d@1", "viz-3d@1"];

export interface SubjectManifest {
  id: string;
  name: string;
  nameEn: string;
  version: string;
  contentApi: number;
  language: string[];
  description: string;
  dependencies: string[];
  curriculumVersion: string;
  requiredEngines: string[];
  capabilities: string[];
  book?: { title: string; edition: string; authors: string[]; sha256?: string; rights: "private-study-reference" | "licensed" | "none" };
  completeness: "full-course" | "example";
  chapters: { id: string; title: string; titleEn: string; sections: string[] }[];
}

export interface Lesson {
  id: string;
  section: string;
  title: string;
  titleEn: string;
  version: string;
  status: "draft" | "machine-validated" | "reviewed" | "published";
  source?: { printedPages: [number, number]; pdfIndex: number; verified: boolean };
  objectives: { id: string; text: string }[];
  prerequisites: string[];
  levels: { beginner: string; standard: string; advanced: string };
  definitions: { term: string; termEn: string; body: string }[];
  theorems: { name: string; statement: string; conditions?: string }[];
  formulas: { tex: string; note: string }[];
  examples: { title: string; problem: string; steps: string[]; answer: string; verify?: Record<string, unknown> }[];
  misconceptions: { wrong: string; right: string }[];
  visualizations: Record<string, unknown>[];
  summary: string[];
  review: { q: string; a: string }[];
}

export interface LoadedSubject { manifest: SubjectManifest; lessons: Record<string, Lesson>; errors: string[] }

const SEMVER = /^\d+\.\d+\.\d+$/;

export function validateManifest(m: any): string[] {
  const e: string[] = [];
  for (const k of ["id", "name", "version", "description", "curriculumVersion"]) if (typeof m?.[k] !== "string" || !m[k]) e.push(`manifest.${k} missing`);
  if (m && !/^[a-z0-9-]+$/.test(m.id ?? "")) e.push("manifest.id must be kebab-case");
  if (m && !SEMVER.test(m.version ?? "")) e.push("manifest.version must be semver");
  if (m?.contentApi !== PLATFORM_CONTENT_API) e.push(`contentApi ${m?.contentApi} not supported (platform ${PLATFORM_CONTENT_API})`);
  for (const eng of m?.requiredEngines ?? []) if (!AVAILABLE_ENGINES.includes(eng)) e.push(`required engine ${eng} not available`);
  if (!Array.isArray(m?.chapters) || !m.chapters.length) e.push("manifest.chapters missing");
  if (!["full-course", "example"].includes(m?.completeness)) e.push("manifest.completeness invalid");
  return e;
}

export function validateLesson(l: any, manifest: SubjectManifest): string[] {
  const e: string[] = [];
  const where = `lesson ${l?.section ?? "?"}`;
  for (const k of ["id", "section", "title", "version", "status"]) if (typeof l?.[k] !== "string") e.push(`${where}: ${k} missing`);
  const sections = manifest.chapters.flatMap((c) => c.sections);
  if (!sections.includes(l?.section)) e.push(`${where}: section not in manifest`);
  for (const k of ["beginner", "standard", "advanced"]) if (typeof l?.levels?.[k] !== "string" || l.levels[k].length < 40) e.push(`${where}: levels.${k} too short`);
  if (!Array.isArray(l?.objectives) || l.objectives.length < 2) e.push(`${where}: needs ≥2 objectives`);
  if (!Array.isArray(l?.examples) || l.examples.length < 2) e.push(`${where}: needs ≥2 worked examples`);
  if (!Array.isArray(l?.formulas) || !l.formulas.length) e.push(`${where}: formulas missing`);
  for (const p of l?.prerequisites ?? []) if (typeof p !== "string") e.push(`${where}: bad prerequisite`);
  return e;
}

export function loadSubject(manifest: any, lessonFiles: any[]): LoadedSubject {
  const errors = validateManifest(manifest);
  const lessons: Record<string, Lesson> = {};
  if (!errors.length) {
    for (const l of lessonFiles) {
      const le = validateLesson(l, manifest);
      if (le.length) errors.push(...le);
      else lessons[l.section] = l;
    }
  }
  return { manifest, lessons, errors };
}

export function compareVersions(a: string, b: string): number {
  const pa = a.split(".").map(Number), pb = b.split(".").map(Number);
  for (let i = 0; i < 3; i++) if (pa[i] !== pb[i]) return pa[i] - pb[i];
  return 0;
}
