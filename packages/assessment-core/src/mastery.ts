/**
 * Transparent initial mastery model (heuristic, NOT a validated psychometric estimate).
 *
 * For each attempt i on a section:  credit_i = correct · w_diff · w_help
 *   w_diff = 0.7 / 1.0 / 1.2 for difficulty 1/2/3
 *   w_help = 1 − 0.15·hints − (solutionRevealed ? 0.5 : 0), floored at 0.2
 * Attempts are weighted by recency: weight = 0.85^(rank from newest) and by retention
 * decay exp(−days/30). mastery = Σ weight·credit / Σ weight·w_diff, clipped to [0,1],
 * then shrunk toward 0 when there are few attempts: × n/(n+3).
 * The function is pure so it can be replaced without touching storage.
 */
export interface AttemptRecord {
  section: string;
  templateId: string;
  difficulty: number;
  correct: boolean;
  hintsUsed: number;
  solutionRevealed: boolean;
  errorType?: string | null;
  timeMs: number;
  at: number; // epoch ms
}

const W_DIFF: Record<number, number> = { 1: 0.7, 2: 1.0, 3: 1.2 };

export function sectionMastery(attempts: AttemptRecord[], now = Date.now()): number {
  if (!attempts.length) return 0;
  const sorted = [...attempts].sort((a, b) => b.at - a.at).slice(0, 30);
  let num = 0, den = 0;
  sorted.forEach((a, rank) => {
    const wd = W_DIFF[a.difficulty] ?? 1;
    const help = Math.max(0.2, 1 - 0.15 * a.hintsUsed - (a.solutionRevealed ? 0.5 : 0));
    const days = Math.max(0, (now - a.at) / 86_400_000);
    const w = Math.pow(0.85, rank) * Math.exp(-days / 30);
    num += w * (a.correct ? wd * help : 0);
    den += w * wd;
  });
  const n = sorted.length;
  return den ? Math.min(1, Math.max(0, num / den)) * (n / (n + 3)) : 0;
}

export interface Recommendation {
  section: string;
  reason: string;
  score: number;
  difficulty: number;
}

/**
 * Deterministic recommendation: priority = (1 − mastery) + 0.3·recentErrors + 0.2·staleness
 * + 0.25 if a prerequisite of a weak section, limited to the exam scope.
 */
export function recommend(scope: string[], attempts: AttemptRecord[], prereqs: Record<string, string[]>, now = Date.now()): Recommendation[] {
  const bySec: Record<string, AttemptRecord[]> = {};
  for (const a of attempts) (bySec[a.section] ??= []).push(a);
  const mastery: Record<string, number> = {};
  for (const s of scope) mastery[s] = sectionMastery(bySec[s] ?? [], now);
  const out: Recommendation[] = scope.map((s) => {
    const list = (bySec[s] ?? []).sort((a, b) => b.at - a.at);
    const recentErrors = list.slice(0, 5).filter((a) => !a.correct).length / 5;
    const lastOk = list.find((a) => a.correct)?.at;
    const staleness = lastOk ? Math.min(1, (now - lastOk) / (14 * 86_400_000)) : 1;
    const isPrereqOfWeak = scope.some((t) => (prereqs[t] ?? []).includes(s) && mastery[t] < 0.4);
    const score = 1 - mastery[s] + 0.3 * recentErrors + 0.2 * staleness + (isPrereqOfWeak ? 0.25 : 0);
    const reason = !list.length ? "ยังไม่เคยฝึกหัวข้อนี้" : recentErrors >= 0.4 ? "ตอบผิดบ่อยในช่วงหลัง" : isPrereqOfWeak ? "เป็นพื้นฐานของหัวข้อที่ยังอ่อน"
      : staleness > 0.7 ? "ไม่ได้ทบทวนมานาน (spaced review)" : mastery[s] < 0.6 ? "ความเชี่ยวชาญยังต่ำ" : "รักษาระดับ";
    const difficulty = mastery[s] < 0.35 ? 1 : mastery[s] < 0.7 ? 2 : 3;
    return { section: s, reason, score, difficulty };
  });
  return out.sort((a, b) => b.score - a.score || a.section.localeCompare(b.section));
}

export function weaknessCategories(attempts: AttemptRecord[]): { errorType: string; count: number }[] {
  const c: Record<string, number> = {};
  for (const a of attempts) if (!a.correct && a.errorType) c[a.errorType] = (c[a.errorType] ?? 0) + 1;
  return Object.entries(c).map(([errorType, count]) => ({ errorType, count })).sort((a, b) => b.count - a.count);
}
