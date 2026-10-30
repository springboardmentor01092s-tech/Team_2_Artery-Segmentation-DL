import { useEffect, useState, type FormEvent } from 'react';
import { apiUrl } from './api';

type Record = {id:string; analysis_event_id:string; created_at:string; result:{narrowing_percent:number; minimum_diameter:number; reference_diameter:number; severity:{status:string;category:string|null}; explanation:{text:string}}};
type Props = {token:string;caseId:string;imageId:string;runId:string;candidates:string[];canReview:boolean};

export default function StenosisMeasurements({token,caseId,imageId,runId,candidates,canReview}:Props) {
  const [rows,setRows]=useState<Record[]>([]);
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(true);
  const [saving,setSaving]=useState(false);
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
      measurement_evidence:fields.get('measurement_evidence'),calibration_verified:true,reference_selection_reviewed:true};
    try {
      const response=await fetch(url,{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify(payload)});
      if(!response.ok)throw new Error('Measurement was not saved. Check run/candidate identity, reviewer access, calibration evidence and diameter consistency.');
      const saved=await response.json();setRows(previous=>[saved,...previous]);form.reset();
    }catch(e){setError(e instanceof Error?e.message:'Measurement could not be saved.');}
    finally{setSaving(false);}
  }
  return <section aria-label="Reviewed stenosis measurements">
    <h3>Reviewed diameter reduction</h3>
    <p className="caption">Separate clinician-supplied measurements for this saved run. Model scores and global mask widths are not reference diameters. New entries preserve previous records.</p>
    {error&&<p role="alert">{error}</p>}
    {loading?<p role="status">Loading reviewed measurements…</p>:!rows.length?<p>No reviewed measurements saved for this run. Narrowing and severity remain unavailable.</p>:rows.map(row=><article key={row.id} className="evidence-details">
      <strong>{row.result.narrowing_percent.toFixed(2)}% estimated diameter reduction</strong>
      <p>{row.result.explanation.text}</p><p>Severity: {row.result.severity.category||'Not assessable — no approved reference protocol'}</p>
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
          <label><input type="checkbox" required /> I verified calibration and reviewed the local/reference measurements in the same frame.</label>
          <button type="submit">{saving?'Saving…':'Save separate reviewed measurement'}</button>
        </fieldset>
      </form>
    </details>}
  </section>;
}
