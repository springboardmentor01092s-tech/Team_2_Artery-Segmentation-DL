import { useCallback, useEffect, useRef, useState } from "react";
import { apiUrl, request } from "./api";
import "./research-progress.css";

type Evidence = {id:string; label:string; available:boolean; url:string|null; updated_at:string|null};
type Progress = {
  task_proof?:Array<{id:string;title:string;status:string;detail:string;required_proof:string;evidence_id:string|null}>;
  next_local_trial_at?:string|null;
  checked_at:string; last_evidence_at:string|null; telemetry:{detail:string; state:string; title?:string; kind?:string; step?:string; heartbeat_at?:string; started_at?:string; finished_at?:string; completed_units?:number|null; total_units?:number|null; elapsed_seconds?:number}; caveat:string; next_action:string;
  summary:{recorded_experiments:number; measured_gains:number; framework_tests:number|null; downloaded_bundles:number|null; verified_checkpoint_matches:number|null; quarantined_checkpoints:number|null};
  experiments:Array<{id:string; title:string; status:string; metric:string; count_unit?:"pixels"|"instances"|"voxels"; baseline:number; candidate:number; delta:number; baseline_fn:number; candidate_fn:number; baseline_fp:number; candidate_fp:number; limitation:string; evidence_id:string}>;
  tasks:Array<{id:string; title:string; status:string; detail:string; checkpoint_sha256:string|null; evidence_id:string}>;
  activity:Array<{id:string; title:string; detail:string; status:string; recorded_at:string; evidence_id:string}>;
  evidence:Evidence[]; warnings:string[];
};
const featuredTasks = ['baseline-implementation', 'segmentation-comparison', 'stenosis', 'dashboard', 'reports'];
const openTasks = ['measurements', 'severity', 'unseen', 'explainability'];
const statusLabels: Record<string, string> = {
  software_verified: 'Workflow verified',
  research_validated: 'Research replay verified',
  comparison_recorded: 'Comparison completed',
  blocked: 'Evidence needed',
  verification_required: 'Verification needed',
};
const time = (value:string|null) => value ? new Date(value).toLocaleString() : "Unavailable";
export default function ResearchProgress({token}:{token:string}) {
  const [data,setData]=useState<Progress|null>(null), [error,setError]=useState(""), [busy,setBusy]=useState(false), [auto,setAuto]=useState(true);
  const pending=useRef(false), mounted=useRef(true);
  const refresh=useCallback(async()=>{
    if(pending.current) return;
    pending.current=true; setBusy(true);
    try {const result=await request<Progress>("/api/research-progress",token); if(mounted.current){setData(result);setError("");}}
    catch(cause){if(mounted.current)setError(cause instanceof Error?cause.message:"Unable to refresh evidence");}
    finally{pending.current=false;if(mounted.current)setBusy(false);}
  },[token]);
  useEffect(()=>{mounted.current=true;void refresh();return()=>{mounted.current=false;};},[refresh]);
  useEffect(()=>{if(!auto)return; const id=window.setInterval(()=>{if(document.visibilityState==="visible")void refresh();},15000);return()=>window.clearInterval(id);},[auto,refresh]);
  async function download(id:string){
    const evidence=data?.evidence.find(row=>row.id===id);if(!evidence?.url)return;
    try{const response=await fetch(apiUrl(evidence.url),{headers:{Authorization:`Bearer ${token}`}});if(!response.ok)throw new Error("Evidence download failed");
      const blob=await response.blob(), url=URL.createObjectURL(blob), link=document.createElement("a");link.href=url;link.download=`${id}.${blob.type.includes("json")?"json":"md"}`;link.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
    }catch(cause){setError(cause instanceof Error?cause.message:"Download failed");}
  }
  const evidenceButton=(id:string)=><button className="rp-evidence-button" disabled={!data?.evidence.find(e=>e.id===id)?.available} onClick={()=>void download(id)}>Download evidence</button>;
  const tasks = data?.task_proof ?? [];
  const selectTasks = (ids: string[]) => ids.flatMap(id => tasks.filter(task => task.id === id));
  const renderTasks = (rows: typeof tasks) => <div className="rp-proof-list">{rows.map(task =>
    <details key={task.id}>
      <summary><span>{task.title}</span><span className="rp-badge">{statusLabels[task.status] ?? task.status}</span></summary>
      <p>{task.detail}</p>
      <h4>Further evidence</h4>
      <p>{task.required_proof}</p>
      {task.evidence_id && data?.evidence.some(item => item.id === task.evidence_id && item.available) && evidenceButton(task.evidence_id)}
    </details>
  )}</div>;
  return <div className="research-progress">
    <section className="rp-banner"><div><span className="rp-label">RESEARCH EVIDENCE</span><h3>Results and validation</h3><p>{"Review the verified results behind the application and the evidence still needed for stronger claims."}</p></div><span role="status" aria-atomic="true" className="rp-badge">{error?"Connection error · status unconfirmed":data?.telemetry.state==="running"?"Local job running":data?.telemetry.state==="stale"?"Heartbeat stale":data?.telemetry.state==="not_connected"||!data?"No local job telemetry":`Last local job: ${data.telemetry.state}`}</span></section>
    <div className="rp-controls"><div><p>Last checked: {time(data?.checked_at??null)}</p><p>Latest evidence file update: {time(data?.last_evidence_at??null)}</p></div><label><input type="checkbox" checked={auto} onChange={event=>setAuto(event.target.checked)}/> Refresh evidence every 15 seconds</label><button disabled={busy} onClick={()=>void refresh()}>{busy?"Checking…":"Refresh now"}</button></div>
    {error&&<p role="alert" className="rp-warning">{error}. Previously loaded evidence may be stale.</p>}
    {!data&&!error&&<p role="status">Loading evidence…</p>}
    {data&&<>
      <section className="rp-panel">
        <h3>Key application results</h3>
        {tasks.length ? renderTasks(selectTasks(featuredTasks)) : <p>No task evidence is available in this installation.</p>}
      </section>
      <section className="rp-panel">
        <h3>Validation still needed</h3>
        <p className="rp-caption">These checks support independent performance, clinical measurements or model explanations.</p>
        {renderTasks(selectTasks(openTasks))}
      </section>
      <details className="rp-panel rp-archive">
        <summary>Full research history and source files</summary>
        <section><h3>Additional task records</h3>{renderTasks(tasks.filter(task => !featuredTasks.includes(task.id) && !openTasks.includes(task.id)))}</section>
      {data.telemetry.title&&<section className="rp-panel rp-job"><span className="rp-label">MONITORED LOCAL WORKER · {data.telemetry.kind?.replaceAll("_"," ")}</span><h3>{data.telemetry.title}</h3><p>{data.telemetry.step}</p><div className="rp-job-facts"><p>Heartbeat: {time(data.telemetry.heartbeat_at??null)}</p><p>Elapsed: {data.telemetry.elapsed_seconds?.toFixed(1)??"—"} seconds</p><p>Completed units: {data.telemetry.completed_units??"—"} / {data.telemetry.total_units??"—"}</p></div>{data.telemetry.completed_units!=null&&data.telemetry.total_units!=null&&<progress aria-label="Actual completed work units" value={data.telemetry.completed_units} max={data.telemetry.total_units}/>}<p className="rp-caption">A completed quality audit is not a completed model experiment or an accuracy improvement.</p></section>}
      <div className="rp-stats">{[["Recorded experiments",data.summary.recorded_experiments,"Completed comparisons in this evidence set"],["Measured improvements",data.summary.measured_gains,"Gains require matched validation and review"],["Framework checks",data.summary.framework_tests,"Software checks, not model accuracy"],["Quarantined checkpoints",data.summary.quarantined_checkpoints,"Downloaded weights awaiting validation"]].map(([label,value,hint])=><section key={String(label)}><p>{label}</p><strong>{value??"—"}</strong><small>{hint}</small></section>)}</div>
      <p className="rp-caption">{data.caveat}</p>
      <div className="rp-columns"><section className="rp-panel"><h3>Measured experiments</h3>{data.experiments.length===0?<p>No verified comparison is available.</p>:data.experiments.map(experiment=><article key={experiment.id}><span className="rp-badge">{experiment.status.replaceAll("_"," ")}</span><h4>{experiment.title}</h4><div className="rp-table-wrap"><table><caption>Matched development-validation results</caption><thead><tr><th>Metric</th><th>Baseline</th><th>Candidate</th></tr></thead><tbody><tr><th>{experiment.metric}</th><td>{(experiment.baseline*100).toFixed(4)}%</td><td>{(experiment.candidate*100).toFixed(4)}%</td></tr><tr><th>False-positive {experiment.count_unit??"pixels"}</th><td>{experiment.baseline_fp?.toLocaleString()??"—"}</td><td>{experiment.candidate_fp?.toLocaleString()??"—"}</td></tr><tr><th>Missed {experiment.count_unit??"foreground pixels"}</th><td>{experiment.baseline_fn?.toLocaleString()??"—"}</td><td>{experiment.candidate_fn?.toLocaleString()??"—"}</td></tr></tbody></table></div><p>Metric change: {(experiment.delta*100).toFixed(4)} percentage points. Original baseline retained.</p><p className="rp-caption">{experiment.limitation}</p>{evidenceButton(experiment.evidence_id)}</article>)}</section>
      <section className="rp-panel"><h3>Recorded work</h3><p className="rp-caption">Explicitly recorded actions, not a live view of agent activity.</p>{!data.activity.length&&<p>No activity entries recorded yet.</p>}<ol className="rp-timeline">{data.activity.map(event=><li key={event.id}><div><span className="rp-badge">{event.status}</span><time dateTime={event.recorded_at}>{time(event.recorded_at)}</time></div><h4>{event.title}</h4><p>{event.detail}</p>{evidenceButton(event.evidence_id)}</li>)}</ol></section></div>
      <section className="rp-panel"><h3>Dataset and task readiness</h3><p className="rp-caption">A pinned hash identifies a recorded baseline; it does not mean a new model has improved or is installed.</p><div className="rp-task-grid">{data.tasks.map(task=><article key={task.id}><h4>{task.title}</h4><span className="rp-badge">{task.status}</span><p>{task.detail}</p>{task.checkpoint_sha256&&<details><summary>Recorded baseline hash</summary><code>{task.checkpoint_sha256}</code></details>}{evidenceButton(task.evidence_id)}</article>)}</div></section>
      <section className="rp-panel"><h3>Archived planning notes</h3><p>{data.next_action}</p>{data.next_local_trial_at&&<p>Next local experiment eligible after: <strong>{time(data.next_local_trial_at)}</strong> (your local time). Eligibility is not a promise of execution; inputs and resource checks must also pass.</p>}<p>{data.summary.downloaded_bundles??"—"} verified download bundles · {data.summary.verified_checkpoint_matches??"—"} original checkpoint matches. No automatic model activation.</p></section>
      <section className="rp-panel"><h3>Source evidence</h3><div className="rp-source-grid">{data.evidence.map(e=><article key={e.id}><h4>{e.label}</h4><p className="rp-caption">{e.available?`File updated ${time(e.updated_at)}`:"Not available in this installation"}</p>{evidenceButton(e.id)}</article>)}</div></section>
      </details>
      {data.warnings.map((warning,index)=><p className="rp-warning" key={index}>{warning}</p>)}
    </>}
  </div>;
}
