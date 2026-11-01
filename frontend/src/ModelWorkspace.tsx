import { type ReactNode, useEffect, useState } from "react";
import "./model-workspace.css";
import { request } from "./api";
import { Card } from "./components/prismui/card";
import ModelAnalytics from "./ModelAnalytics";
import EvaluationExplorer from "./EvaluationExplorer";
import ExperimentLab from "./ExperimentLab";
import ResearchProgress from "./ResearchProgress";

export type ModelStatus = {
  task_connections?:Array<{id:string;title:string;connected:boolean;state:string;dimension:string;anatomy:string;modality:string;checkpoint_sha256:string|null;limitation:string}>;
  trained_release?: { configured: boolean; ready: boolean; version: string; input_contract: string; limitations: string[]; models: Array<{ task: string; architecture: string; sha256: string; validation_dice: number; validation_images: number; validation_status: string }>; research_evidence?: { scope: string; limitations: string[]; tasks: Array<{ task_id: string; title: string; validation_support: string; baseline_result: string; outcome: string; inference_connected: boolean }>; calibration_studies: Array<{ task: string; cases: number; raw_NLL: number; crossfit_NLL: number; raw_Brier: number; crossfit_Brier: number }> } };
  models_ready: boolean;
  model_version: string;
  instance_models_ready?: boolean;
  validation: Record<string, { validation_dice: number; mean_image_pixel_f1?: number; selection_score?: number; validation_images: number }>;
  research_only: boolean;
  comparison?: {
    experiments?: Array<{
      task: string;
      architecture: string;
      train_images: number;
      validation_images: number;
      best_validation: { dice: number; iou: number; precision: number; recall: number; sensitivity?: number; specificity?: number; f1: number; mean_image_pixel_f1?: number; selection_score?: number; auc_roc?: number; pixel_accuracy?: number };
      test_split_used: boolean;
    }>;
    architecture_mean_validation_dice?: Record<string, number>;
    architecture_mean_validation_image_f1?: Record<string, number>;
    architecture_mean_validation_composite_score?: Record<string, number>;
    selection_metric?: string;
    selected_architecture?: string | null;
  };
  selection?: { architecture?: string; version?: string; input_size?: number; selection_metric?: string; validation_dice_by_architecture?: Record<string, number>; validation_image_f1_by_architecture?: Record<string, number>; validation_composite_score_by_architecture?: Record<string, number> };
  test_report?: {
    architecture?: string;
    test_split_used?: boolean;
    results?: Array<{ task: string; test_images: number; metrics: { dice: number; iou: number; precision: number; recall: number; sensitivity?: number; f1: number; specificity: number; auc_roc?: number; pixel_accuracy?: number } }>;
  };
  instance_aware?: {
    selection?: { architecture?: string; run_id?: string; selection_metric?: string; validation_official_f1_by_architecture?: Record<string, number>; test_used_for_training_or_selection?: boolean };
    comparison?: { experiments?: Array<{ task: string; architecture: string; training_images: number; validation_images: number; best_validation?: { arcade_official_f1?: number; pixel_accuracy_union_mask?: number; pixel_precision_union_mask?: number; pixel_recall_sensitivity_union_mask?: number; pixel_specificity_union_mask?: number; pixel_f1_union_mask?: number; pixel_dice_union_mask?: number; pixel_iou_union_mask?: number; pixel_auc_roc_union_score?: number; instance_precision_iou50?: number; instance_recall_iou50?: number; instance_f1_iou50?: number; matched_instance_dice_iou50?: number; matched_instance_iou_iou50?: number } }> };
    test_report?: { architecture?: string; final_test_results?: Record<string, { test_images: number; metrics: { arcade_official_f1?: number; pixel_accuracy_union_mask?: number; pixel_precision_union_mask?: number; pixel_recall_sensitivity_union_mask?: number; pixel_specificity_union_mask?: number; pixel_f1_union_mask?: number; pixel_dice_union_mask?: number; pixel_iou_union_mask?: number; pixel_auc_roc_union_score?: number } }> };
  };
};

export type ModelRegistry = {
  can_activate?: boolean;
  active_architecture?: string;
  model_version: string;
  models: { architecture: string; display_name: string; version: string; input_size?: number; available: boolean; active: boolean; mean_validation_dice: number | null; mean_validation_image_f1?: number | null; mean_validation_composite_score?: number | null; checkpoint_sha256: Record<string, string>; tasks: { task: string; train_images?: number; validation_images?: number; validation_dice?: number; epochs?: number; seed?: number; dataset?: string; threshold?: number }[] }[];
  history: { event: string; architecture: string; version?: string; previous_architecture?: string; activated_at?: string | null; activated_by?: string }[];
};

function EvaluationSection({ title, children }: { title: string; children: ReactNode }) {
  return <details className="evaluation-section"><summary><span>{title}</span><span className="evaluation-chevron" aria-hidden="true">⌄</span></summary><div className="evaluation-section-body">{children}</div></details>;
}

export default function ModelWorkspace({ token }: { token: string }) {
  const [panel,setPanel]=useState<"progress"|"evaluation">("progress");
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [error, setError] = useState("");
  const [registry, setRegistry] = useState<ModelRegistry | null>(null);
  const [activationBusy, setActivationBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const [updatedAt, setUpdatedAt] = useState("");

  useEffect(() => {
    let active = true;
    setRefreshing(true);
    Promise.all([request<ModelStatus>("/api/analysis/status", token), request<ModelRegistry>("/api/analysis/models", token)])
      .then(([result, modelRegistry]) => { if (active) { setStatus(result); setRegistry(modelRegistry); setError(""); setUpdatedAt(new Date().toLocaleTimeString()); } })
      .catch((cause: Error) => { if (active) setError(cause.message); })
      .finally(() => { if (active) setRefreshing(false); });
    return () => { active = false; };
  }, [token, refreshKey]);

  async function activate(architecture: string) {
    setActivationBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await request<{ detail: string; model_version: string }>("/api/analysis/models/activate", token, { architecture }, "POST");
      const [nextStatus, nextRegistry] = await Promise.all([request<ModelStatus>("/api/analysis/status", token), request<ModelRegistry>("/api/analysis/models", token)]);
      setStatus(nextStatus);
      setRegistry(nextRegistry);
      setNotice(`${result.detail}: ${result.model_version}. New analyses will use this version.`);
    } catch (cause) { setError((cause as Error).message); }
    finally { setActivationBusy(false); }
  }

  const navigation=<nav className="research-view-nav" aria-label="Model workspace views"><button aria-pressed={panel==="progress"} onClick={()=>setPanel("progress")}>Research progress</button><button aria-pressed={panel==="evaluation"} onClick={()=>setPanel("evaluation")}>Model evaluation</button></nav>;
  if(panel==="progress")return <div className="settings-page model-workspace"><div className="page-heading"><div><p className="eyebrow">MODEL WORKSPACE</p><h2>Research progress</h2></div><span className="stage-badge">Research only</span></div>{navigation}<ResearchProgress token={token}/></div>;
  return <div className="settings-page model-workspace">
    <div className="page-heading"><div><p className="eyebrow">RESEARCH EVALUATION</p><h2>Model Evaluation</h2></div><span className="stage-badge">Research only</span></div>
    {navigation}
    <p className="muted">Review ARCADE model experiments, validation results, and the selected research checkpoint.</p>
    <ExperimentLab token={token} />
    {status && <ModelAnalytics status={status} registry={registry} refreshing={refreshing} updatedAt={updatedAt} onRefresh={() => setRefreshKey(key => key + 1)} />}
    <EvaluationSection title="Pinned release report explorer"><EvaluationExplorer token={token} /></EvaluationSection>

    {status?.trained_release?.research_evidence && <section aria-labelledby="dataset-results-heading" className="evaluation-datasets">
      <div><h3 id="dataset-results-heading">Results by dataset & task</h3><p className="muted">Open a task to explore its results, validation data and limitations.</p><p className="caption">{status.trained_release.research_evidence.scope}</p></div>
      <div className="evaluation-task-grid">{status.trained_release.research_evidence.tasks.map(task =>
        <details className="evaluation-task" key={task.task_id}>
          <summary><span><strong>{task.title}</strong><small>{task.inference_connected ? "Connected research adapter" : "Research evidence only / excluded"}</small></span><span className="evaluation-chevron" aria-hidden="true">⌄</span></summary>
          <dl><dt>Validation data</dt><dd>{task.validation_support}</dd><dt>Measured results & limitations</dt><dd>{task.baseline_result}</dd><dt>Outcome</dt><dd>{task.outcome.replaceAll("_", " ")}</dd><dt>Application inference</dt><dd>{task.inference_connected ? "Connected to application inference." : "Separate research evidence; not connected to application inference."}</dd></dl>
        </details>
      )}</div>
      <EvaluationSection title="Prepared-grid voxel-score studies">{status.trained_release.research_evidence.calibration_studies.map(study => <p key={study.task}><strong>{study.task}</strong>: {study.cases} volumes · cross-fitted NLL {study.raw_NLL.toFixed(6)} → {study.crossfit_NLL.toFixed(6)} · Brier {study.raw_Brier.toFixed(6)} → {study.crossfit_Brier.toFixed(6)}. Masks unchanged; no native/patient calibration or deployment.</p>)}</EvaluationSection>
      <EvaluationSection title="Research evidence limitations">{status.trained_release.research_evidence.limitations.map((text, index) => <p key={index}>{text}</p>)}</EvaluationSection>
    </section>}
    {status?.trained_release?.configured && <EvaluationSection title="Connected training release"><p>{status.trained_release.version} · {status.trained_release.ready ? "Checkpoint hashes verified; ready for research inference" : "Unavailable: check installed artifacts and optional inference dependencies"}</p><p className="caption">{status.trained_release.input_contract}</p>{status.trained_release.models.map(model => <p key={model.task}><strong>{model.task === "syntax" ? "Binary artery mask" : "ARCADE stenosis masks"}</strong>: {model.architecture} · {model.task === "syntax" ? "mean image Dice" : "pooled union Dice"} {model.validation_dice.toFixed(4)} on {model.validation_images} images.<br/><small>{model.validation_status} · SHA256 {model.sha256}</small></p>)}<p className="caption">{status.trained_release.limitations.join(" ")}</p></EvaluationSection>}
    {error && <p className="message error" role="alert">{error}</p>}
    {notice && <p className="message success" role="status">{notice}</p>}
    {!status && !error && <p role="status">Loading model status…</p>}
    {status && <div className="settings-grid">
      <Card className="panel"><h3>Active inference deployment</h3><p><strong>{status.models_ready ? "Model ready" : "Models unavailable"}</strong></p><p className="muted">Live analysis model version: {status.model_version}</p>{status.instance_models_ready ? <p className="caption">Category-aware Mask R-CNN instance checkpoints are present and power the current inference service. Displayed masks are unions for the legacy overlay; category IDs and uncalibrated per-instance scores are retained in analysis metadata.</p> : <p className="caption">The active local model currently produces binary union masks. Its pixel scores are research proxies and do not represent official ARCADE instance/category metrics.</p>}</Card>
      <Card className="panel"><h3>Validation summary</h3>
        {Object.keys(status.validation).length ? Object.entries(status.validation).map(([task, result]) =>
          <p key={task}><strong>{task === "syntax" ? "Artery" : task === "stenosis" ? "Stenosis" : task}</strong>: composite {result.selection_score?.toFixed(3) ?? "—"} · Dice {result.validation_dice.toFixed(3)}{result.mean_image_pixel_f1 == null ? "" : ` · mean image F1 ${result.mean_image_pixel_f1.toFixed(3)}`} on {result.validation_images} validation images</p>
        ) : <p className="muted">No validation report is available.</p>}
        <p className="caption">Dataset split: official ARCADE validation. These are model metrics, not per-image confidence scores or clinical performance.</p>
      </Card>
    </div>}
    {status && <EvaluationSection title="Instance-aware ARCADE evaluation"><div className="viewer-heading"><div><p className="muted">Original COCO polygons and category labels; each vessel/stenosis annotation remains a distinct instance during training.</p></div><span className="stage-badge">{status.instance_aware?.selection?.architecture ?? "Training pending"}</span></div>
      {status.instance_aware?.comparison?.experiments?.length ? <><div className="table-scroll"><table><thead><tr><th>Task / model</th><th>ARCADE val F1*</th><th>Obj. P / R / F1†</th><th>Pixel acc.</th><th>Pixel P / sensitivity</th><th>Pixel specificity</th><th>Pixel F1 / Dice</th><th>IoU</th><th>AUC-ROC</th></tr></thead><tbody>{status.instance_aware.comparison.experiments.map((row, index) => { const m = row.best_validation ?? {}; return <tr key={`instance-${row.task}-${row.architecture}-${index}`}><td>{row.task === "syntax" ? "Vessel syntax" : "Stenosis"}<br /><small>{row.architecture}</small></td><td>{m.arcade_official_f1?.toFixed(3) ?? "—"}</td><td>{m.instance_precision_iou50?.toFixed(3) ?? "—"} / {m.instance_recall_iou50?.toFixed(3) ?? "—"} / {m.instance_f1_iou50?.toFixed(3) ?? "—"}</td><td>{m.pixel_accuracy_union_mask?.toFixed(3) ?? "—"}</td><td>{m.pixel_precision_union_mask?.toFixed(3) ?? "—"} / {m.pixel_recall_sensitivity_union_mask?.toFixed(3) ?? "—"}</td><td>{m.pixel_specificity_union_mask?.toFixed(3) ?? "—"}</td><td>{m.pixel_f1_union_mask?.toFixed(3) ?? "—"} / {m.pixel_dice_union_mask?.toFixed(3) ?? "—"}</td><td>{m.pixel_iou_union_mask?.toFixed(3) ?? "—"}</td><td>{m.pixel_auc_roc_union_score?.toFixed(3) ?? "—"}</td></tr>; })}</tbody></table></div><p className="caption">*Per-image category/instance polygon F1 following the public ARCADE evaluation rules; the local implementation should be cross-checked against the challenge evaluator before submission. It is the primary validation selection metric. †Greedy one-to-one, same-category instance matching at IoU ≥ 0.50. Pixel metrics are supplementary binary-union metrics. Results are research outputs, not clinical validation.</p></> : <p className="muted">No legacy instance-aware comparison report is installed. Use the Experiment Lab above to import external evaluation records; keep independent test results separate from model selection.</p>}
      {status.instance_aware?.selection?.architecture && <p className="caption">Validation-selected architecture: <strong>{status.instance_aware.selection.architecture}</strong> · selection: {status.instance_aware.selection.selection_metric}. {status.instance_models_ready ? "This selected checkpoint pair is present and serving inference." : "After importing its trained checkpoint pair, the backend will use this instance-aware inference path."}</p>}
      {status.instance_aware?.test_report?.final_test_results && <p className="caption">A final held-out report exists for {status.instance_aware.test_report.architecture}. It is displayed separately from validation and did not affect model selection.</p>}
    </EvaluationSection>}
    {registry && <EvaluationSection title="Registered models & deployment"><div className="viewer-heading"><div><p className="muted">{registry.can_activate ? "Activate a research checkpoint pair. Changes are audited; this is not authorization for clinical deployment." : "Read-only model registry. Model activation requires administrator approval; production deployment is not configured."}</p></div><span className="stage-badge">{registry.model_version}</span></div>
      <div className="table-scroll"><table><thead><tr><th>Model / version</th><th>Status</th><th>Composite score*</th><th>Validation Dice</th><th>Mean image F1</th><th>Dataset provenance</th><th>Checkpoint fingerprints</th><th>Action</th></tr></thead><tbody>{registry.models.map((model) => <tr key={model.architecture}><td><strong>{model.display_name}</strong><br /><small>{model.version} · {model.input_size ?? 128}×{model.input_size ?? 128}</small></td><td>{model.active ? "Active" : model.available ? "Registered" : "Checkpoint missing"}</td><td>{model.mean_validation_composite_score == null ? "—" : model.mean_validation_composite_score.toFixed(3)}</td><td>{model.mean_validation_dice == null ? "—" : model.mean_validation_dice.toFixed(3)}</td><td>{model.mean_validation_image_f1 == null ? "—" : model.mean_validation_image_f1.toFixed(3)}</td><td>{[...new Set(model.tasks.map((task) => task.dataset).filter(Boolean))].join(", ") || "Recorded in training report"}<br /><small>{model.tasks.map((task) => `${task.task}: ${task.validation_images ?? "—"} val / ${task.train_images ?? "—"} train`).join(" · ")}</small></td><td>{Object.entries(model.checkpoint_sha256).map(([task, hash]) => <small className="hash-line" key={task}>{task}: {hash.slice(0, 16)}…</small>)}</td><td><button type="button" className="model-activate" disabled={!registry.can_activate || activationBusy || !model.available || model.active} onClick={() => activate(model.architecture)}>{model.active ? "Active" : activationBusy ? "Activating…" : registry.can_activate ? "Activate / rollback" : "Approval required"}</button></td></tr>)}</tbody></table></div>
      <p className="caption">*Composite score is the unweighted mean of the nine listed metrics. Pixel accuracy can be inflated by background pixels, while recall/sensitivity and F1/Dice are duplicate pairs; inspect each metric and validation overlays. Scores use binary pixel masks and are not official ARCADE instance/category F1.</p>
    </EvaluationSection>}
    {registry && <EvaluationSection title="Deployment history"><div className="viewer-heading"><span>{registry.history.length} events</span></div>{registry.history.length ? <div className="model-history-list">{registry.history.map((entry, index) => <div key={`${entry.activated_at || "initial"}-${index}`}><strong>{entry.version || entry.architecture}</strong><span>{entry.event === "initial_selection" ? "Initial selection" : `Activated ${entry.previous_architecture ? `from ${entry.previous_architecture}` : ""}`}</span><small>{entry.activated_at ? new Date(entry.activated_at).toLocaleString() : "Initial project configuration"} · {entry.activated_by || "system"}</small></div>)}</div> : <p className="muted">No model switches recorded yet.</p>}</EvaluationSection>}
    <EvaluationSection title="Architecture scope"><p className="muted">Trained and compared: binary Tiny U-Net and Attention U-Net. U-Net++, ResUNet, DeepLabV3+, nnU-Net, TransUNet, Swin-UNet, and 3D U-Net have not been trained in this workspace. ARCADE supplies 2D X-ray angiography frames, so 3D U-Net and voxel-level segmentation need a separate volumetric dataset.</p></EvaluationSection>
    {status?.comparison?.experiments?.length ? <EvaluationSection title="Architecture comparison"><div className="table-scroll"><table><thead><tr><th>Task</th><th>Architecture</th><th>Train images</th><th>Validation images</th><th>Composite*</th><th>Accuracy</th><th>Precision</th><th>Recall / Sensitivity</th><th>Specificity</th><th>F1 / Dice</th><th>IoU</th><th>AUC-ROC</th><th>Mean image F1</th></tr></thead><tbody>{status.comparison.experiments.map((row, index) => <tr key={`${row.task}-${row.architecture}-${index}`}><td>{row.task === "syntax" ? "Artery" : "Stenosis"}</td><td>{row.architecture}</td><td>{row.train_images}</td><td>{row.validation_images}</td><td>{row.best_validation.selection_score?.toFixed(3) ?? "—"}</td><td>{row.best_validation.pixel_accuracy?.toFixed(3) ?? "—"}</td><td>{row.best_validation.precision.toFixed(3)}</td><td>{(row.best_validation.sensitivity ?? row.best_validation.recall).toFixed(3)}</td><td>{row.best_validation.specificity?.toFixed(3) ?? "—"}</td><td>{row.best_validation.f1.toFixed(3)} / {row.best_validation.dice.toFixed(3)}</td><td>{row.best_validation.iou.toFixed(3)}</td><td>{row.best_validation.auc_roc?.toFixed(3) ?? "—"}</td><td>{row.best_validation.mean_image_pixel_f1?.toFixed(3) ?? "—"}</td></tr>)}</tbody></table></div><p className="caption">*The composite is the unweighted mean of accuracy, precision, recall, F1, AUC-ROC, Dice, IoU, sensitivity, and specificity. Recall/sensitivity and F1/Dice are duplicates; accuracy can be background-dominated. AUC uses 256 bins. These are binary-mask proxy metrics, not official ARCADE instance/category scores.</p></EvaluationSection> : <EvaluationSection title="Model comparison"><p className="muted">No legacy architecture comparison report is installed. Import compatible external experiments in the Experiment Lab above. This application does not launch training.</p></EvaluationSection>}
    {status?.test_report?.results?.length ? <EvaluationSection title="Held-out test report"><div className="table-scroll"><table><thead><tr><th>Task</th><th>Test images</th><th>Dice</th><th>IoU</th><th>Precision</th><th>Sensitivity</th><th>Specificity</th><th>F1</th><th>AUC-ROC</th><th>Pixel acc.</th></tr></thead><tbody>{status.test_report.results.map((row) => <tr key={`test-${row.task}`}><td>{row.task === "syntax" ? "Artery" : "Stenosis"}</td><td>{row.test_images}</td><td>{row.metrics.dice.toFixed(3)}</td><td>{row.metrics.iou.toFixed(3)}</td><td>{row.metrics.precision.toFixed(3)}</td><td>{(row.metrics.sensitivity ?? row.metrics.recall).toFixed(3)}</td><td>{row.metrics.specificity.toFixed(3)}</td><td>{row.metrics.f1.toFixed(3)}</td><td>{row.metrics.auc_roc?.toFixed(3) ?? "—"}</td><td>{row.metrics.pixel_accuracy?.toFixed(3) ?? "—"}</td></tr>)}</tbody></table></div><p className="caption">One-time evaluation of the validation-selected {status.test_report.architecture} checkpoint on the official ARCADE test split. This result did not affect checkpoint selection and is not clinical validation.</p></EvaluationSection> : null}
    <EvaluationSection title="Training scope & limitations"><p className="muted">The reproducible instance trainer compares Mask R-CNN ResNet-50-FPN and its FPN v2 variant using original COCO instances and class labels. The public ARCADE validation F1 is the primary selection metric; Accuracy, Precision, Recall/Sensitivity, Specificity, F1, Dice, IoU, AUC-ROC, and matched-instance metrics are also recorded. The older Tiny U-Net and Attention U-Net remain binary-mask baselines. Transfer learning is used through TorchVision COCO-pretrained weights; Transformer-based architectures are not trained in this instance pipeline.</p><p className="caption">A trained checkpoint only appears here after Colab execution and importing its artifacts. When the connected training release is configured, analysis uses the preserved binary artery U-Net and ARCADE stenosis-mask detector shown above; older comparison reports do not replace these weights. Centerline graphs are algorithmic estimates because ARCADE does not supply curated centerline reference labels. Research visualization is not a clinical diagnosis.</p></EvaluationSection>
  </div>;
}
