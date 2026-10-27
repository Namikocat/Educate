import type { AttemptRecord } from "@assess/mastery";

export type { AttemptRecord };

export interface Step {
  rule: string;
  explain: string;
  before: string | null;
  after: string | null;
  assumptions: string[];
  verified: boolean | null;
  checkMethod: string | null;
  viz: string | null;
}

export interface Problem {
  id: string;
  templateId: string;
  templateVersion: string;
  seed: number;
  difficulty: number;
  params: Record<string, unknown>;
  section: string;
  subject: string;
  title: string;
  statement: string;
  display: string;
  answerType: "expr" | "antiderivative" | "choice" | "improper";
  choices: { id: string; label: string }[] | null;
  answerTex?: string;
  variable: string;
  steps?: Step[];
  hints?: string[];
  viz: Record<string, unknown> | null;
  verification: { answer: string; steps: (string | null)[] };
  canonical: string;
  objectives: string[];
}

export interface CheckResult {
  correct: boolean;
  method: string;
  feedback?: string | null;
  parseError?: string;
  errorType?: string | null;
  missingConstant?: boolean;
  problemId?: string;
}

export interface TemplateMeta {
  id: string;
  subject: string;
  section: string;
  title: string;
  objectives: string[];
  answerType: string;
  difficulties: number[];
  visualization: string | null;
  version: string;
}

export interface Profile { id: number; name: string; createdAt: number }
export interface Note { id: number; section: string; body: string; updatedAt: number }
export interface Bookmark { section: string; createdAt: number }

export interface ExamQuestion extends Problem { answer?: string; result?: CheckResult }
export interface ExamSession {
  id: string;
  title: string;
  config: ExamConfig;
  questions: ExamQuestion[];
  startedAt: number;
  endsAt: number;
  submittedAt?: number;
  score?: number;
}
export interface ExamConfig {
  sections: string[];
  count: number;
  difficulty: number | null;
  minutes: number;
  seed: number;
  immediateFeedback: boolean;
  includeChoice: boolean;
  preset: string;
}

export type ClaudeState = "not_installed" | "not_authenticated" | "available" | "busy" | "rate_limited" | "failed" | "unavailable" | "disabled" | "unknown";
export interface ClaudeStatus { state: ClaudeState; version?: string; path?: string; message?: string }
export interface TutorRequest {
  mode: "explain_step" | "explain_differently" | "explain_mistake" | "socratic" | "formula" | "visualization";
  style?: "simpler" | "detailed" | "formal" | "analogy" | "visual";
  context: Record<string, unknown>;
  question: string;
}
export interface Conversation { id: number; createdAt: number; request: { mode: string; style?: string; question: string; section?: string; problem?: string }; response: string }
export interface TutorResponse { ok: boolean; text?: string; error?: string; state?: ClaudeState; durationMs?: number }

export interface Settings {
  theme: "system" | "light" | "dark";
  fontScale: number;
  level: "beginner" | "standard" | "advanced";
  aiEnabled: boolean;
  leftPanel: boolean;
  rightPanel: boolean;
  focusMode: boolean;
  saveTutorHistory: boolean;
}

export const DEFAULT_SETTINGS: Settings = {
  theme: "system", fontScale: 1, level: "standard", aiEnabled: false, leftPanel: true, rightPanel: true, focusMode: false, saveTutorHistory: true,
};
