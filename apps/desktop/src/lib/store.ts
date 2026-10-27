import { create } from "zustand";
import { getBackend } from "./backend";
import { DEFAULT_SETTINGS, type Problem, type Profile, type Settings, type Step } from "./types";

export type Page = "dashboard" | "subjects" | "courses" | "lessons" | "practice" | "exam" | "viz" | "progress" | "notes" | "tutor" | "settings";

export interface Route { page: Page; subject?: string; section?: string; mode?: "guided" | "free" | "weak" }

/** Context the AI tutor may use; the student chooses what is actually sent. */
export interface TutorContext {
  subject: string;
  section: string;
  problem?: Problem;
  attempt?: string;
  selectedStep?: { index: number; step: Step };
  objective?: string;
}

interface AppState {
  ready: boolean;
  profile: Profile | null;
  settings: Settings;
  route: Route;
  tutor: TutorContext | null;
  dataVersion: number; // bump to refresh views after writes
  init(): Promise<void>;
  go(r: Route): void;
  setSettings(p: Partial<Settings>): Promise<void>;
  setProfile(p: Profile): void;
  setTutor(c: TutorContext | null): void;
  touch(): void;
}

export const useApp = create<AppState>((set, get) => ({
  ready: false,
  profile: null,
  settings: DEFAULT_SETTINGS,
  route: { page: "dashboard" },
  tutor: null,
  dataVersion: 0,
  async init() {
    const be = await getBackend();
    const [profile, s, last] = await Promise.all([
      be.db<Profile | null>({ op: "get_profile" }),
      be.db<Settings | null>({ op: "get_settings" }),
      be.db<string | null>({ op: "get_kv", key: "last_route" }),
    ]);
    let route: Route = { page: "dashboard" };
    try { if (last) route = JSON.parse(last); } catch { /* ignore corrupt value */ }
    set({ profile, settings: { ...DEFAULT_SETTINGS, ...(s ?? {}) }, route, ready: true });
  },
  go(r) {
    set({ route: r });
    getBackend().then((be) => be.db({ op: "set_kv", key: "last_route", value: JSON.stringify(r) }));
  },
  async setSettings(p) {
    const settings = { ...get().settings, ...p };
    set({ settings });
    const be = await getBackend();
    await be.db({ op: "set_settings", settings });
  },
  setProfile: (profile) => set({ profile }),
  setTutor: (tutor) => set({ tutor }),
  touch: () => set((s) => ({ dataVersion: s.dataVersion + 1 })),
}));
