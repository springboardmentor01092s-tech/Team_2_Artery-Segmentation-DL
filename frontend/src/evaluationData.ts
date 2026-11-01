export type MetricSummary = { name: string; value: number | null; unit: string; aggregation: string; definition: string };
export type ModelMetadata = { architecture: string; version: string; checkpoint_sha256: string; checkpoint_reference: string };
export type DatasetMetadata = { name: string; version: string | null; split: string; patient_independence_verified: boolean | null };
export type EvaluationRun = {
  id: string; record_type: string; model: ModelMetadata; task: string; dataset: DatasetMetadata; dimension: string;
  sample_counts: { images: number | null; patients: number | null; studies: number | null; excluded: number | null };
  metrics: MetricSummary[]; protocol: { id: string | null; description: string; independent_final_test: boolean };
  evaluated_at: string | null; runtime_seconds: number | null; hardware: string | null;
  approval_status: string | null; reviewer_status: string | null; source: string; limitations: string[];
  training_history: EpochMetric[]; prediction_artifacts: PredictionArtifact[]; sample_evaluations: SampleEvaluation[];
};
export type EpochMetric = { epoch: number; metrics: Record<string, number | null> };
export type PredictionArtifact = { id: string; sample_id: string; kind: string; authorized_url: string; coordinate_frame: string };
export type SampleEvaluation = { id: string; dataset: DatasetMetadata; metrics: MetricSummary[]; artifacts: PredictionArtifact[] };
export type ErrorAnalysis = { sample_id: string; category: string; matching_rule: string | null };
export type ModelApproval = { status: string; reviewer: string; reason: string; criteria_version: string; decided_at: string };
export type EvaluationReport = { runs: EvaluationRun[]; research_only: boolean; summary: Record<string, number | string | null>; capabilities: Record<string, boolean> };
export const metricText = (value: number | null | undefined) => value == null || !Number.isFinite(value) ? "Not recorded" : value.toFixed(4);
export function comparable(a: EvaluationRun, b: EvaluationRun) {
  return a.task === b.task && a.dimension === b.dimension && a.dataset.name === b.dataset.name &&
    Boolean(a.dataset.version) && a.dataset.version === b.dataset.version && a.dataset.split === b.dataset.split &&
    Boolean(a.protocol.id) && a.protocol.id === b.protocol.id &&
    JSON.stringify(a.metrics.map(m => [m.name, m.unit, m.definition, m.aggregation])) ===
    JSON.stringify(b.metrics.map(m => [m.name, m.unit, m.definition, m.aggregation]));
}
export function filterRuns(runs: EvaluationRun[], query: string, task: string, architecture: string, sort: string) {
  return runs.filter(run => (task === "all" || run.task === task) && (architecture === "all" || run.model.architecture === architecture) &&
    [run.id, run.task, run.dataset.name, run.model.architecture, run.model.version].join(" ").toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => sort === "dice" ? (b.metrics.find(m => m.name === "Dice")?.value ?? -1) - (a.metrics.find(m => m.name === "Dice")?.value ?? -1) : a.model.architecture.localeCompare(b.model.architecture));
}
