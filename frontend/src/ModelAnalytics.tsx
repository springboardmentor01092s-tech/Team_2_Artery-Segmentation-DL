import { useState } from "react";
import type { ModelRegistry, ModelStatus } from "./ModelWorkspace";

type Metric = "dice" | "iou" | "precision" | "recall" | "f1";
const metrics: Metric[] = ["dice", "iou", "precision", "recall", "f1"];
const taskName = (task: string) => task === "syntax" ? "Artery" : task === "stenosis" ? "Stenosis" : task;
const valid = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);
const score = (value: unknown) => valid(value) ? value.toFixed(4) : "Not reported";

function Bars({ rows, label }: { rows: { label: string; value?: number }[]; label: string }) {
  return <div className="cv-model-bars" role="list" aria-label={label}>
    <div className="cv-model-scale" aria-hidden="true"><span>0</span><span>Score · 0–1</span><span>1</span></div>
    {rows.length ? rows.map((row, index) => <div role="listitem" key={index} className="cv-model-bar-row">
      <div><span>{row.label}</span><strong>{score(row.value)}</strong></div>
      <div className="cv-model-track" aria-hidden="true"><span style={{ width: valid(row.value) ? `${Math.max(0, Math.min(1, row.value)) * 100}%` : "0%" }} /></div>
    </div>) : <p className="muted">No comparable metrics have been imported.</p>}
  </div>;
}

export default function ModelAnalytics({ status, registry, refreshing, updatedAt, onRefresh }: {
  status: ModelStatus; registry: ModelRegistry | null; refreshing: boolean; updatedAt: string; onRefresh: () => void;
}) {
  const [view, setView] = useState("Evaluation");
  const [metric, setMetric] = useState<Metric>("dice");
  const [task, setTask] = useState("all");
  const evidence = status.trained_release?.research_evidence;
  const connections=status.task_connections;
  const connected = connections?.filter(item=>item.connected).length ?? evidence?.tasks.filter(item => item.inference_connected).length ?? 0;
  const total = connections?.length ?? evidence?.tasks.length ?? 0;
  const experiments = status.comparison?.experiments ?? [];
  const filtered = experiments.filter(item => task === "all" || item.task === task);
  const releaseModels = status.trained_release?.models ?? [];
  const evaluationRows = releaseModels.length
    ? releaseModels.map(item => ({ label: `${taskName(item.task)} · ${item.task === "syntax" ? "mean image Dice" : "pooled union Dice"}`, value: item.validation_dice }))
    : Object.entries(status.validation).map(([name, item]) => ({ label: `${taskName(name)} · validation Dice`, value: item.validation_dice }));
  return <section className="model-analytics" aria-label="Model analytics">
    <div className="cv-model-heading"><div><p className="eyebrow">MODEL INSIGHTS</p><h3>Monitor. Compare. Evaluate.</h3></div><button type="button" disabled={refreshing} onClick={onRefresh}>{refreshing ? "Refreshing…" : "Refresh status"}</button></div>
    <div className="cv-model-navigation" role="group" aria-label="Analytics views">{["Evaluation", "Comparison", "Monitoring"].map(name => <button type="button" key={name} aria-pressed={view === name} onClick={() => setView(name)}>{name}</button>)}</div>
    <div aria-live="polite" className="caption">Last successful status refresh: {updatedAt || "Not yet refreshed"}. Recorded research metrics; not clinical performance.</div>
    {view === "Evaluation" && <>
      <div className="cv-model-grid">
        <article className="cv-model-card"><h4>Connected release · validation Dice</h4><Bars rows={evaluationRows} label="Validation Dice scores" /><p className="caption">Different tasks and aggregation methods are shown separately. These scores are not a ranking across tasks.</p></article>
        <article className="cv-model-card"><h4>Research task coverage</h4>{total ? <><div className="cv-model-donut-layout"><svg className="cv-model-donut" viewBox="0 0 120 120" role="img" aria-label={`${connected} of ${total} research tasks connected to inference`}><circle cx="60" cy="60" r="44" fill="none" stroke="currentColor" strokeOpacity=".16" strokeWidth="16" /><circle cx="60" cy="60" r="44" fill="none" stroke="currentColor" strokeWidth="16" pathLength="100" strokeDasharray={`${connected / total * 100} 100`} transform="rotate(-90 60 60)" /><text x="60" y="57" textAnchor="middle" fill="currentColor" fontSize="22" fontWeight="700">{connected}/{total}</text><text x="60" y="74" textAnchor="middle" fill="currentColor" fontSize="10">connected</text></svg><div><p><strong>{connected}</strong> connected · {(connected / total * 100).toFixed(1)}%</p><p><strong>{total - connected}</strong> not enabled · {((total - connected) / total * 100).toFixed(1)}%</p></div></div><p className="caption">Current hash-verified task routes, not model accuracy. Two hepatic tasks remain excluded. CADICA has two output views sharing one checkpoint.</p></> : <p className="muted">No research task inventory is available.</p>}</article>
      {connections&&<details className="evaluation-section"><summary>Task connection registry</summary><div className="evaluation-section-body table-scroll"><table><caption>Current adapter availability · not clinical approval</caption><thead><tr><th>Task</th><th>Input</th><th>State</th></tr></thead><tbody>{connections.map(item=><tr key={item.id}><th scope="row">{item.title}</th><td>{item.dimension} · {item.modality} · {item.anatomy}</td><td>{item.connected?'Connected · research only':item.state.replaceAll('_',' ')}</td></tr>)}</tbody></table><p>2D tasks: open a coronary case → Assets &amp; preparation → Choose a task model. 3D tasks: select a matching coronary CTA or aorta CT case and use its volume workflow.</p></div></details>}
      </div>
      <details className="evaluation-section"><summary>Validation results table<span aria-hidden="true">⌄</span></summary><div className="evaluation-section-body table-scroll"><table><caption>Connected model validation reports</caption><thead><tr><th scope="col">Task</th><th scope="col">Architecture</th><th scope="col">Dice</th><th scope="col">Images</th><th scope="col">Aggregation</th></tr></thead><tbody>{releaseModels.map(item => <tr key={item.task}><th scope="row">{taskName(item.task)}</th><td>{item.architecture}</td><td>{score(item.validation_dice)}</td><td>{item.validation_images}</td><td>{item.task === "syntax" ? "Mean image Dice" : "Pooled union Dice"}</td></tr>)}</tbody></table>{!releaseModels.length && <p>No connected release reports imported.</p>}</div></details>
    </>}
    {view === "Comparison" && <article className="cv-model-card"><h4>Architecture comparison · same task, same metric</h4><div className="cv-model-filters"><label>Metric<select value={metric} onChange={event => setMetric(event.target.value as Metric)}>{metrics.map(name => <option key={name} value={name}>{name.toUpperCase()}</option>)}</select></label><label>Task<select value={task} onChange={event => setTask(event.target.value)}><option value="all">All tasks (labelled separately)</option>{Array.from(new Set(experiments.map(item => item.task))).map(name => <option key={name} value={name}>{taskName(name)}</option>)}</select></label></div>
      <Bars rows={filtered.map(item => ({ label: `${taskName(item.task)} · ${item.architecture}`, value: item.best_validation[metric] }))} label={`Architecture validation ${metric} comparison`} />
      {filtered.length ? <div className="table-scroll"><table><caption>Recorded binary-mask validation experiments</caption><thead><tr><th scope="col">Task / architecture</th>{metrics.map(name => <th scope="col" key={name}>{name.toUpperCase()}</th>)}<th scope="col">Validation images</th></tr></thead><tbody>{filtered.map((item, index) => <tr key={index}><th scope="row">{taskName(item.task)} · {item.architecture}</th>{metrics.map(name => <td key={name}>{score(item.best_validation[name])}</td>)}<td>{item.validation_images}</td></tr>)}</tbody></table></div> : <p className="muted">Import comparable experiment reports to populate this graph and table. Connected models perform different tasks and cannot substitute for a controlled architecture comparison.</p>}
      <p className="caption">Binary-mask experiments only. Instance-aware ARCADE results remain in their separate section below. Missing metrics are not treated as zero.</p>
    </article>}
    {view === "Monitoring" && <><div className="cv-model-grid"><article className="cv-model-card"><h4>Inference snapshot</h4><dl className="cv-model-status"><dt>Service model readiness</dt><dd>{status.models_ready ? "Ready" : "Unavailable"}</dd><dt>Active version</dt><dd>{status.model_version}</dd><dt>Release verification</dt><dd>{status.trained_release?.configured ? status.trained_release.ready ? "Verified and ready" : "Not ready" : "No release configured"}</dd><dt>Registered architectures</dt><dd>{registry ? registry.models.length : "Not available"}</dd></dl></article><article className="cv-model-card"><h4>Live telemetry</h4><p>Latency, error rates, drift, GPU usage and epoch-by-epoch loss are not connected.</p><p className="caption">This is a manually refreshed readiness snapshot, not continuous monitoring. No historical trend is inferred from validation scores.</p></article></div>
      <article className="cv-model-card"><h4>Deployment event log</h4>{registry?.history.length ? <div className="table-scroll"><table><caption>Recorded model deployment events, in source order</caption><thead><tr><th scope="col">Event</th><th scope="col">Model / version</th><th scope="col">Recorded time</th></tr></thead><tbody>{registry.history.map((item, index) => <tr key={index}><td>{item.event.replaceAll("_", " ")}</td><td>{item.version || item.architecture}</td><td>{item.activated_at ? new Date(item.activated_at).toLocaleString() : "Initial configuration (no timestamp)"}</td></tr>)}</tbody></table></div> : <p>No deployment events are available.</p>}</article>
    </>}
  </section>;
}
