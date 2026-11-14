import { useEffect, useState, type FormEvent } from 'react';
import { apiUrl } from './api';

type Record = {id:string; analysis_event_id:string; created_at:string; result:{narrowing_percent:number; minimum_diameter:number; reference_diameter:number; diameter_unit:string; candidate_id:string; reference_segment_id:string; measurement_frame:string; quality_gate?:{status:string}; severity:{status:string;category:string|null;protocol_id?:string;protocol_version?:string;reference?:string;measurement_method?:string}; explanation:{text:string}}};
type Props = {token:string;caseId:string;imageId:string;runId:string;candidates:string[];canReview:boolean;canAssess:boolean};
const reasonLabel=(reason?:string)=>({
  mask_width_percentile_estimate:'Experimental Gharshitha mask-width estimate · source pixels',
  low_local_boundary_contrast:'Not assessable · insufficient vessel-boundary contrast',
  no_stable_nearby_reference_segment:'Not assessable · no stable nearby reference segment',
  ambiguous_vessel_paths:'Not assessable · candidate crosses multiple vessel paths',
  no_candidate_crossing_centerline:'Not assessable · no centerline crosses the candidate',
  boundary_sensitivity_measurement_failed:'Not assessable · measurement is unstable at the vessel boundary',
  reference_suitability_unconfirmed_equal_widths:'Not assessable · reference suitability is unconfirmed',
  candidate_vessel_association_unverified:'Not assessable · vessel association is unverified',
  original_coordinate_mapping_unreliable:'Not assessable · source-coordinate mapping is unreliable'
}[reason||'']||reason?.replaceAll('_',' ')||'Not assessable · measurement evidence is insufficient');

export default function StenosisMeasurements({token,caseId,imageId,runId,candidates,canReview,canAssess}:Props) {
  const [rows,setRows]=useState<Record[]>([]);
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(true);
  const [saving,setSaving]=useState(false);
  const [protocolStatus,setProtocolStatus]=useState('Loading protocol…');
  const [canAuthorize,setCanAuthorize]=useState(false);
  const [authorizationChecked,setAuthorizationChecked]=useState(false);
  const [selectedProtocol,setSelectedProtocol]=useState('COROVISION_CADRADS_INFORMED_XCA');
  const candidateKey=candidates.join('|');
  useEffect(()=>{let active=true;Promise.all([
    fetch(apiUrl('/api/research/severity-protocol'),{headers:{Authorization:`Bearer ${token}`}}).then(r=>{if(!r.ok)throw Error('Protocol status unavailable');return r.json()}),
    fetch(apiUrl('/api/auth/me'),{headers:{Authorization:`Bearer ${token}`}}).then(r=>r.json())
  ]).then(([protocol,user])=>{if(active){setProtocolStatus(protocol.status);setCanAuthorize(['admin','researcher'].includes(user.role))}}).catch(()=>{if(active)setProtocolStatus('Unavailable')});return()=>{active=false}},[token]);
  async function protocolDecision(decision:'authorize'|'deactivate'){
    if(decision==='authorize'&&!authorizationChecked)return;
    setSaving(true);try{const r=await fetch(apiUrl('/api/research/severity-protocol'),{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify({protocol_id:selectedProtocol,protocol_version:'1.0.0',research_mode_only:true,decision})});if(!r.ok)throw Error('Protocol decision could not be saved');setProtocolStatus((await r.json()).status);setAuthorizationChecked(false)}catch(e){setError((e as Error).message)}finally{setSaving(false)}
  }
  const [automatic,setAutomatic]=useState<{id:string;records:{candidate_id:string;status:string;reasons:string[];minimum_diameter?:number|null;reference_diameter?:number|null;narrowing_percent?:number|null;association?:{path_id:string;status:string};sensitivity?:{narrowing_range_percentage_points?:number[]};severity?:{category?:string|null;reason?:string};minimum_cross_section?:{endpoints:number[][]};reference_cross_sections?:{endpoints:number[][]}[]}[]}[]>([]);
  async function assessSavedRun(){
    setSaving(true);setError('');
    try{const response=await fetch(apiUrl(`/api/cases/${caseId}/automatic-measurements/${runId}`),{method:'POST',headers:{Authorization:`Bearer ${token}`}});
      if(!response.ok)throw new Error('Saved-run measurement assessment failed.');
      const record=await response.json();setAutomatic([record]);
    }catch(e){setError(e instanceof Error?e.message:'Assessment failed');}finally{setSaving(false);}
  }
  useEffect(()=>{setAutomatic([]);let active=true;
    async function loadOrAssess(){
      try {
        const historyResponse=await fetch(apiUrl(`/api/cases/${caseId}/automatic-measurements/${runId}`),{headers:{Authorization:`Bearer ${token}`}});
        if(!historyResponse.ok)throw Error('Automatic measurement history could not be loaded');
        const history=await historyResponse.json();
        history.sort((left: {created_at?:string}, right: {created_at?:string}) =>
          (right.created_at ?? '').localeCompare(left.created_at ?? ''));
        if(!active)return;
        if(history.length||!canAssess||!candidates.length){setAutomatic(history);return;}
        const assessmentResponse=await fetch(apiUrl(`/api/cases/${caseId}/automatic-measurements/${runId}`),{method:'POST',headers:{Authorization:`Bearer ${token}`}});
        if(!assessmentResponse.ok)throw Error('Automatic severity assessment could not be completed');
        const assessment=await assessmentResponse.json();
        if(active)setAutomatic([assessment]);
      } catch(e) {if(active)setError(e instanceof Error?e.message:'Automatic assessment failed');}
    }
    loadOrAssess();return()=>{active=false};
  },[caseId,runId,token,canAssess,candidateKey]);
  const url=apiUrl(`/api/cases/${caseId}/stenosis-measurements`);
  useEffect(()=>{
    const controller=new AbortController();setRows([]);setError('');setLoading(true);
    fetch(`${url}?analysis_event_id=${encodeURIComponent(runId)}`,{headers:{Authorization:`Bearer ${token}`},signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error('Reviewed measurements could not be loaded.');return r.json();})
      .then(setRows).catch(e=>{if(e.name!=='AbortError')setError(e.message);})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>controller.abort();
  },[url,runId,token]);
  async function save(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();const form=event.currentTarget;const fields=new FormData(form);
    const minimum=Number(fields.get('minimum_diameter_mm')),reference=Number(fields.get('reference_diameter_mm'));
    if(!Number.isFinite(minimum)||!Number.isFinite(reference)||minimum<0||reference<=0||minimum>reference){setError('Minimum diameter must be between zero and the positive reference diameter.');return;}
    setSaving(true);setError('');
    const payload={image_id:imageId,analysis_event_id:runId,candidate_id:fields.get('candidate_id'),
      minimum_diameter_mm:minimum,reference_diameter_mm:reference,
      measurement_frame:fields.get('measurement_frame'),reference_segment_id:fields.get('reference_segment_id'),
      protocol_id:fields.get('protocol_id'),calibration_evidence:fields.get('calibration_evidence'),
      measurement_evidence:fields.get('measurement_evidence'),calibration_verified:true,reference_selection_reviewed:true,
      lumen_boundaries_reviewed:true,reference_segment_suitable:true,anatomy_ambiguous:false,image_quality_acceptable:true};
    try {
      const response=await fetch(url,{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify(payload)});
      if(!response.ok)throw new Error('Measurement was not saved. Check run/candidate identity, reviewer access, calibration evidence and diameter consistency.');
      const saved=await response.json();setRows(previous=>[saved,...previous]);form.reset();
    }catch(e){setError(e instanceof Error?e.message:'Measurement could not be saved.');}
    finally{setSaving(false);}
  }
  return <section aria-label="Reviewed stenosis measurements">
    <p className="eyebrow">IMAGE ANALYSIS · STENOSIS ANALYSIS</p>
    <h3>Severity Assessment · Vessel diameter workflow</h3>
    <p className="caption">The experimental measurement method uses centerline diameter and nearby-reference comparison with source-coordinate mapping, unique-vessel association, branch and contrast checks, stable-reference selection and boundary-sensitivity gating. Every compatible saved run is assessed automatically. Detection identifies a candidate; diameter measurements quantify narrowing; an eligible versioned protocol interprets the percentage. Model confidence is never used as percentage narrowing. New entries preserve previous records.</p>
    <div className="metadata"><div><span>Detected lesions</span><strong>{candidates.length || 'No candidate above threshold'}</strong></div><div><span>Saved run</span><strong>{runId}</strong></div><div><span>Automatic normal grade</span><strong>Never inferred from no detection</strong></div></div>
    {error&&<p role="alert">{error}</p>}
    {candidates.length > 0 && <div className="stenosis-summary-scroll" tabIndex={0} role="region" aria-label="Candidate measurement summary">
      <table className="stenosis-summary">
        <caption>Saved candidate measurements</caption>
        <thead><tr>{['Candidate', 'Vessel path', 'Minimum lumen', 'Reference lumen', 'Research severity', 'Narrowing', 'Evidence'].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead>
        <tbody>{candidates.map(id => {
          const reviewed = rows.find(row => row.result.candidate_id === id)?.result;
          const assessed = automatic[0]?.records.find(candidate => candidate.candidate_id === id);
          const measurement = reviewed ?? assessed;
          const unit = reviewed?.diameter_unit ?? 'source px';
          const diameter = (value?: number | null) => value == null ? 'Unavailable' : `${value.toFixed(2)} ${unit}`;
          return <tr key={id}>
            <th scope="row">{id}</th>
            <td>{reviewed?.reference_segment_id ?? assessed?.association?.path_id ?? 'Unavailable'}</td>
            <td>{diameter(measurement?.minimum_diameter)}</td>
            <td>{diameter(measurement?.reference_diameter)}</td>
            <td><strong>{measurement?.severity?.category ?? (assessed ? 'Not assessable' : error ? 'Unable to load' : 'Pending')}</strong></td>
            <td>{measurement?.narrowing_percent == null ? 'Unavailable' : `${measurement.narrowing_percent.toFixed(2)}%`}</td>
            <td>{reviewed ? 'Reviewed record' : assessed ? reasonLabel(assessed.reasons[0]) : error ? 'Connection or assessment failed. Retry assessment.' : 'Automatic assessment pending'}</td>
          </tr>;
        })}</tbody>
      </table>
    </div>}
    <details className="evidence-details"><summary>Research protocol · {protocolStatus.replaceAll('_',' ')}</summary><label>Protocol to review<select value={selectedProtocol} onChange={e=>{setSelectedProtocol(e.target.value);setAuthorizationChecked(false)}}><option value="COROVISION_CADRADS_INFORMED_XCA">CAD-RADS-informed XCA Research Severity · v1.0.0</option><option value="COROVISION_XCA_RESEARCH_5CLASS">Original five-category experiment · v1.0.0</option></select></label><p>Experimental research adaptation, not official CAD-RADS patient reporting or clinically validated severity.</p>{selectedProtocol==='COROVISION_CADRADS_INFORMED_XCA'?<p>No measured narrowing: exactly 0%; Minimal: (0,25%); Mild: [25,50%); Moderate: [50,70%); Severe: [70,100%). The continuous intervals are an XCA research adaptation of published CCTA terminology.</p>:<p>Normal: exactly 0%; Mild: (0,50%); Moderate: [50,70%); Severe: [70,90%); Critical: [90,100%).</p>}<p>A 100% calculation requires separate possible-occlusion assessment. Measurements crossing boundaries under sensitivity remain indeterminate. Selecting an option does not activate it; new assessments use the recorded authorization.</p>{canAuthorize&&<><label><input type="checkbox" checked={authorizationChecked} onChange={e=>setAuthorizationChecked(e.target.checked)}/> I authorize the selected definitions for experimental Research Mode only. Quality gates remain required.</label><button type="button" disabled={saving||!authorizationChecked} onClick={()=>protocolDecision('authorize')}>Record researcher authorization</button><button type="button" disabled={saving||protocolStatus!=='researcher_authorized'} onClick={()=>protocolDecision('deactivate')}>Deactivate research protocol</button></>}</details>
    <h4>Saved-run automatic measurement assessment</h4>
    <p className="caption">Runs the saved-mask measurement workflow against the selected immutable analysis. It starts automatically for every compatible saved run. Missing vessel association, stable reference evidence or uncertainty is reported as not assessable instead of producing an unsupported severity.</p>
    {canAssess&&<button type="button" disabled={saving} onClick={assessSavedRun}>{saving?'Assessing…':'Reassess saved-run measurement readiness'}</button>}
    {automatic.slice(0, 1).map(record=><article key={record.id}><small>Saved assessment {record.id}</small>{record.records.map(candidate=><section key={candidate.candidate_id} className="evidence-details"><strong>{candidate.candidate_id}: {candidate.severity?.category??'Not assessable'}</strong><div className="metadata"><div><span>MLD / RVD</span><strong>{candidate.minimum_diameter?.toFixed(2)??'Unavailable'} / {candidate.reference_diameter?.toFixed(2)??'Unavailable'} source px</strong></div><div><span>Narrowing</span><strong>{candidate.narrowing_percent==null?'Unavailable':`${candidate.narrowing_percent.toFixed(2)}%`}</strong></div><div><span>Geometric path</span><strong>{candidate.association?.path_id??'Unassociated'}</strong></div><div><span>Sensitivity range</span><strong>{candidate.sensitivity?.narrowing_range_percentage_points?.map(v=>v.toFixed(2)).join('–')??'Unavailable'}</strong></div></div><p><strong>Assessment result:</strong> {candidate.reasons.length?candidate.reasons.map(reasonLabel).join('; '):candidate.severity?.reason}</p><p>Research severity: {candidate.severity?.category??'Not assessable'}{candidate.severity?.category?` · ${candidate.severity.reason}`:''}</p><details><summary>Original-coordinate measurement evidence</summary><pre>{JSON.stringify({minimum:candidate.minimum_cross_section?.endpoints,reference:candidate.reference_cross_sections,association:candidate.association},null,2)}</pre></details></section>)}</article>)}
    {automatic.length > 1 && <details><summary>Earlier assessments ({automatic.length - 1})</summary><p>Earlier saved assessments are retained in the run evidence. The candidate table and details above display the latest assessment.</p></details>}
    {loading?<p role="status">Loading reviewed measurements…</p>:!rows.length?<p>{automatic.length?'Automatic assessment is shown above. No separate reviewed measurement has been saved.':candidates.length?'Automatic assessment is starting for this saved run.':'Severity task completed: no lesion candidate is available for diameter-based grading.'}</p>:rows.map(row=><article key={row.id} className="evidence-details">
      <strong>{row.result.candidate_id} · {row.result.narrowing_percent.toFixed(2)}% estimated diameter reduction</strong>
      <div className="metadata"><div><span>Minimum lumen diameter</span><strong>{row.result.minimum_diameter} {row.result.diameter_unit}</strong></div><div><span>Reference vessel diameter</span><strong>{row.result.reference_diameter} {row.result.diameter_unit}</strong></div><div><span>Reference segment</span><strong>{row.result.reference_segment_id}</strong></div><div><span>Measurement frame</span><strong>{row.result.measurement_frame}</strong></div><div><span>Quality gate</span><strong>{row.result.quality_gate?.status||'Legacy record — not stored'}</strong></div></div>
      <p>{row.result.explanation.text}</p><p>Research severity category: {row.result.severity.category||'Indeterminate — no approved compatible protocol'}</p>
      {row.result.severity.category&&<p>Protocol: {row.result.severity.protocol_id} · version {row.result.severity.protocol_version} · reference {row.result.severity.reference}. Research classification from reviewed measurements; clinical validation is not established.</p>}
      <p className="caption">This measurement-based category is separate from detector confidence, CADICA source-grade predictions, ischemia and clinical risk.</p>
      <small>Record {row.id} · {new Date(row.created_at).toLocaleString()}</small>
    </article>)}
    {canReview&&candidates.length>0&&<details><summary>Record calibrated local/reference measurements</summary>
      <form onSubmit={save}>
        <fieldset disabled={saving}><legend>Reviewed evidence in millimetres</legend>
          <label>Candidate <select name="candidate_id" required>{candidates.map(id=><option key={id}>{id}</option>)}</select></label>
          <label>Minimum local diameter (mm) <input name="minimum_diameter_mm" type="number" min="0" step="any" required /></label>
          <label>Reference diameter (mm) <input name="reference_diameter_mm" type="number" min="0.000001" step="any" required /></label>
          <label>Measurement frame / image coordinates <input name="measurement_frame" maxLength={180} required /></label>
          <label>Reference segment identity <input name="reference_segment_id" maxLength={180} required /></label>
          <label>Measurement protocol identifier <input name="protocol_id" maxLength={180} required /></label>
          <label>Calibration evidence <textarea name="calibration_evidence" minLength={8} maxLength={1000} required /></label>
          <label>Measurement source / reviewed locations <textarea name="measurement_evidence" minLength={8} maxLength={1000} required /></label>
          <label><input type="checkbox" required /> I verified calibration, image quality and lumen boundaries; the local/reference measurements use the same frame.</label>
          <label><input type="checkbox" required /> I reviewed the reference segment as suitable and the anatomy as unambiguous for this research measurement.</label>
          <button type="submit">{saving?'Saving…':'Save separate reviewed measurement'}</button>
        </fieldset>
      </form>
    </details>}
  </section>;
}
