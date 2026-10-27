import { describe, expect, it } from "vitest";
import { compile, ExprError } from "@viz/expr";
import { riemannRects, simpson, validateSpec } from "@viz/spec";
import { recommend, sectionMastery, type AttemptRecord } from "@assess/mastery";
import { loadSubject, validateManifest } from "@curriculum/registry";
import calcManifest from "@subjects/calculus/manifest.json";
import sampleManifest from "@subjects/sample-subject/manifest.json";

describe("plot expression compiler (restricted grammar)", () => {
  it("evaluates allowlisted math", () => {
    expect(compile("x^2 + 1")(2)).toBe(5);
    expect(compile("2x")(3)).toBe(6);
    expect(compile("sin(pi/2)")(0)).toBeCloseTo(1);
    expect(compile("|x|")(-4)).toBe(4);
    expect(compile("x**3")(2)).toBe(8);
    expect(compile("exp(-x)")(0)).toBe(1);
  });
  it("rejects anything outside the grammar", () => {
    for (const bad of ["alert(1)", "x; y", "constructor", "x[0]", "window", "'a'", "x".repeat(500)]) {
      expect(() => compile(bad)).toThrow(ExprError);
    }
  });
});

describe("visualization specs", () => {
  it("validates and rejects", () => {
    expect(validateSpec({ type: "riemann", f: "x^2", a: 0, b: 2, n: 4, method: "left" }).ok).toBe(true);
    expect(validateSpec({ type: "riemann", f: "x^2", a: 2, b: 0, n: 4, method: "left" }).ok).toBe(false);
    expect(validateSpec({ type: "function_plot", expressions: ["fetch()"], domain: [0, 1] }).ok).toBe(false);
    expect(validateSpec({ type: "script", src: "x" }).ok).toBe(false);
  });
  it("riemann sums match hand computation", () => {
    const r = riemannRects(compile("x^2"), 0, 2, 4, "right");
    expect(r.sum).toBeCloseTo(15 / 4);
    expect(simpson(compile("x^2"), 0, 1)).toBeCloseTo(1 / 3, 8);
  });
});

describe("mastery model", () => {
  const mk = (correct: boolean, at: number, section = "5.5"): AttemptRecord => ({ section, templateId: "t", difficulty: 2, correct, hintsUsed: 0, solutionRevealed: false, timeMs: 1, at });
  it("is 0 with no attempts and grows with correct answers", () => {
    const now = Date.now();
    expect(sectionMastery([], now)).toBe(0);
    const good = Array.from({ length: 10 }, (_, i) => mk(true, now - i * 1000));
    const bad = Array.from({ length: 10 }, (_, i) => mk(false, now - i * 1000));
    expect(sectionMastery(good, now)).toBeGreaterThan(0.6);
    expect(sectionMastery(bad, now)).toBe(0);
  });
  it("recommends unpracticed / weak sections first, deterministically", () => {
    const now = Date.now();
    const att = Array.from({ length: 8 }, (_, i) => mk(true, now - i, "5.1"));
    const r1 = recommend(["5.1", "5.2"], att, {}, now), r2 = recommend(["5.1", "5.2"], att, {}, now);
    expect(r1[0].section).toBe("5.2");
    expect(r1).toEqual(r2);
  });
});

describe("subject package registry", () => {
  it("accepts the bundled manifests", () => {
    expect(validateManifest(calcManifest)).toEqual([]);
    expect(validateManifest(sampleManifest)).toEqual([]);
  });
  it("rejects incompatible packages", () => {
    expect(validateManifest({ ...calcManifest, contentApi: 99 }).length).toBeGreaterThan(0);
    expect(validateManifest({ ...calcManifest, requiredEngines: ["gpu-cas@9"] }).length).toBeGreaterThan(0);
    expect(loadSubject({ ...calcManifest, id: "Bad Id" }, []).errors.length).toBeGreaterThan(0);
  });
});

import { parseBlocks } from "../src/components/Markdown";
describe("tutor markdown parser", () => {
  it("splits headings, lists, math, tables, code", () => {
    const b = parseBlocks("## ขั้นตอน\n\n1. ให้ $u = x^2$\n2. ได้ **du**\n\n$$\int u\,du$$\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```\ncode\n```\n- x\n- y");
    expect(b.map((x) => x.t)).toEqual(["h", "ol", "math", "table", "code", "ul"]);
  });
  it("keeps raw HTML as plain text (no markup injection)", () => {
    const b = parseBlocks("<script>alert(1)</script>");
    expect(b).toEqual([{ t: "p", text: "<script>alert(1)</script>" }]);
  });
});
