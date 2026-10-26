import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";
const source = fs.readFileSync(new URL("../src/evaluationData.ts", import.meta.url), "utf8");
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const { comparable, filterRuns, metricText } = await import("data:text/javascript;base64," + Buffer.from(js).toString("base64"));
// Synthetic fixtures only; never shown in the application.
const fixture = (id, value) => ({ id, task: "test-segmentation", dimension: "2D",
  dataset: { name: "synthetic-test", version: "fixture-v1", split: "validation" },
  protocol: { id: "test-protocol" }, model: { architecture: id, version: "test" },
  metrics: [{ name: "Dice", value, unit: "ratio", aggregation: "mean", definition: "test only" }] });
test("format missing, zero and non-finite scores without invented values", () => {
  assert.equal(metricText(null), "Not recorded");
  assert.equal(metricText(NaN), "Not recorded");
  assert.equal(metricText(0), "0.0000");
  assert.equal(metricText(.8272773138933874), "0.8273");
});
test("filter and sort without mutating historical records", () => {
  const runs = [fixture("a", .4), fixture("b", .8)];
  assert.deepEqual(filterRuns(runs, "", "all", "all", "dice").map(r => r.id), ["b", "a"]);
  assert.equal(runs[0].id, "a");
  assert.equal(filterRuns(runs, "b", "all", "all", "architecture").length, 1);
  assert.equal(filterRuns(runs, "", "different", "all", "architecture").length, 0);
  assert.deepEqual(filterRuns([], "", "all", "all", "architecture"), []);
});
test("comparison rejects incompatible or unknown protocols", () => {
  const a = fixture("a", .4), b = fixture("b", .8);
  assert.equal(comparable(a, b), true);
  assert.equal(comparable(a, { ...b, task: "detection" }), false);
  assert.equal(comparable(a, { ...b, dataset: { ...b.dataset, split: "test" } }), false);
  assert.equal(comparable(a, { ...b, protocol: { id: null } }), false);
  assert.equal(comparable(a, { ...b, dataset: { ...b.dataset, version: null } }), false);
  assert.equal(comparable(a, { ...b, metrics: [{ ...b.metrics[0], aggregation: "pooled" }] }), false);
});
