import { useEffect, useState } from 'react';
import { apiUrl } from './api';
import { Button } from './components/prismui/button';
import VolumeOrbit from './VolumeOrbit';
import VolumeMeasurementPanel from './VolumeMeasurementPanel';
import { utcDate } from "./lib/time";

type VolumeRun = { id: string; status: string; error: string | null; created_at: string;model_key?:string;
  input_kind: 'medical_study' | 'synthetic_fixture' | 'unspecified';
  preview_url?: string | null; artifacts: Record<string,string>; result: null | { model_id: string; duration_seconds: number;
  coarse_foreground_voxels: number; source_shape: number[]; limitations: string[];
  slices: { axis: string; coarse_index: number; artifact: string }[] } };

type Props = {caseId: string; token: string; readOnly?: boolean; anatomy?: string; historyOnly?: boolean; onOpenAnalysis?: () => void};

export default function VolumeInference(props: Props) {
  return <VolumeCase key={`${props.caseId}:${props.token}`} {...props} />;
}

function VolumeCase({caseId, token, readOnly = false, anatomy = 'coronary', historyOnly = false, onOpenAnalysis}: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dicomFiles, setDicomFiles] = useState<File[]>([]);
  const [hu, setHu] = useState(false);
  const [research, setResearch] = useState(false);
  const [installed, setInstalled] = useState(false);
  const [limits, setLimits] = useState({max_file_bytes:384*1024*1024, max_source_voxels:96_000_000});
  const [runs, setRuns] = useState<VolumeRun[]>([]);
  const [chosen, setChosen] = useState('');
  const [viewingRun, setViewingRun] = useState('');
  const [busy, setBusy] = useState(false);
  const [uploadPercent, setUploadPercent] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [previews, setPreviews] = useState<Record<string,string>>({});
  const [report, setReport] = useState<null | {experimental_geometry?: {status?:string;reasons?:string[];paths?: {id:string;length_mm:number}[];candidates?:{id:string;path_id:string;minimum_area_mm2?:number;reference_area_mm2?:number;area_narrowing_percent?:number;minimum_diameter_mm:number;reference_diameter_mm:number;narrowing_percent:number;severity:string;location_ras_mm:number[]}[];limitations?:string[]}; analysis_run_id:string; model_id:string; explanation:{text:string}; stages:Record<string,{status:string;reason:string}>}>(null);
  const [reportError,setReportError] = useState('');
  const selected = runs.find(r => r.id === chosen) || runs[0];
  const active = runs.some(r => ['queued','running'].includes(r.status));
  const headers = {Authorization: `Bearer ${token}`};

  useEffect(() => {
    let disposed=false;
    setReport(null); setReportError('');
    if (selected?.status === 'completed') void fetch(apiUrl(`/api/cases/${caseId}/volumes/analyses/${selected.id}/report/json`),
      {headers:{Authorization:`Bearer ${token}`}}).then(async response=>{
        if(!response.ok) throw new Error('Saved 3D explanation/report unavailable for this account or run.');
        return response.json();
      }).then(value=>{if(!disposed)setReport(value);}).catch(cause=>{if(!disposed)setReportError(cause.message);});
    return ()=>{disposed=true;};
  },[caseId,selected?.id,selected?.status,token]);

  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const response = await fetch(apiUrl(`/api/cases/${caseId}/volumes/analyses`), {headers: {Authorization:`Bearer ${token}`}});
        if (!response.ok) throw new Error('Unable to load saved 3D analyses');
        const rows: VolumeRun[] = await response.json();
        if (!disposed) setRuns(rows);
      } catch (cause) { if (!disposed) setError((cause as Error).message); }
      if (!disposed) timer = setTimeout(refresh, active ? 2000 : 10000);
    }
    void refresh();
    void fetch(apiUrl('/api/volume-models'), {headers: {Authorization:`Bearer ${token}`}})
      .then(async r => { if (!r.ok) throw new Error('Model status unavailable'); return r.json(); })
      .then(rows => { if (!disposed) { const chosen=rows.find((r:{model_key:string})=>r.model_key===(anatomy==='aorta'?'aorta_aligned':'imagecas'));if(chosen){setInstalled(Boolean(chosen.installed));setLimits(chosen.limits);}else setInstalled(false); } })
      .catch(cause => { if (!disposed) setError(cause.message); });
    return () => { disposed = true; clearTimeout(timer); };
  }, [caseId, token, active, busy,anatomy]);

  useEffect(() => {
    let disposed = false;
    const urls: string[] = [];
    setPreviews({});
    if (selected?.status === 'completed') {
      void Promise.all((selected.result?.slices || []).map(async slice => {
        const response = await fetch(apiUrl(selected.artifacts[slice.artifact]), {headers: {Authorization:`Bearer ${token}`}});
        if (!response.ok) throw new Error('Saved slice preview unavailable');
        const url = URL.createObjectURL(await response.blob()); urls.push(url);
        if (disposed) { URL.revokeObjectURL(url); return; }
        setPreviews(previous => ({...previous, [slice.artifact]:url}));
      })).catch(cause => { if (!disposed) setError(cause.message); });
    }
    return () => { disposed = true; urls.forEach(url => URL.revokeObjectURL(url)); };
  }, [selected?.id, selected?.status, token]);

  async function start(event: React.FormEvent) {
    event.preventDefault();
    if ((!file && !dicomFiles.length) || busy) return;
    setBusy(true); setError(''); setUploadPercent(0);
    try {
      if (!dicomFiles.length && (!file || !/\.(nii(\.gz)?|zip)$/i.test(file.name) || !file.size || file.size > limits.max_file_bytes))
        throw new Error(`Choose an intact .nii, .nii.gz or single-series DICOM .zip file between 1 byte and ${Math.floor(limits.max_file_bytes/1024/1024)} MiB`);
      const body = new FormData();
      if (dicomFiles.length) {
        if (dicomFiles.length < 2 || dicomFiles.length > 2000 || dicomFiles.some(f => !f.size || f.size > 64*1024*1024) || dicomFiles.reduce((s,f)=>s+f.size,0) > limits.max_file_bytes)
          throw new Error('Select 2-2000 non-empty DICOM slices within the volume upload limit.');
        dicomFiles.forEach(f => body.append('files',f));
      } else if (file) body.append('file',file);
      body.append('hu_confirmed',String(hu)); body.append('research_confirmed',String(research)); body.append('input_kind','medical_study');
      const row = await new Promise<VolumeRun>((resolve, reject) => {
        const request = new XMLHttpRequest();
        request.open('POST', apiUrl(`/api/cases/${caseId}/volumes/${dicomFiles.length ? 'dicom-analyses' : 'analyses'}`));
        request.setRequestHeader('Authorization', headers.Authorization);
        request.timeout = 300000;
        request.upload.onprogress = event => setUploadPercent(event.lengthComputable ? Math.round(event.loaded / event.total * 100) : null);
        request.onerror = () => reject(new Error('Upload connection failed. Check saved analysis history before retrying.'));
        request.ontimeout = () => reject(new Error('Upload timed out. Check saved analysis history before retrying.'));
        request.onload = () => {
          try {
            const result = JSON.parse(request.responseText);
            if (request.status < 200 || request.status >= 300)
              throw new Error(typeof result.detail === 'string' ? result.detail : '3D inference rejected');
            resolve(result);
          } catch (cause) { reject(cause); }
        };
        request.send(body);
      });
      setRuns(previous => [row,...previous]); setChosen(row.id);
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); setUploadPercent(null); }
  }

  async function download(name: string) {
    if (!selected) return;
    try {
      const reportFormat = name === 'research-report.json' ? 'json' : name === 'research-report.csv' ? 'csv' : name === 'research-report.pdf' ? 'pdf' : null;
      const endpoint = name === 'evidence.zip' ? `/api/cases/${caseId}/volumes/analyses/${selected.id}/evidence.zip` : reportFormat ? `/api/cases/${caseId}/volumes/analyses/${selected.id}/report/${reportFormat}` : selected.artifacts[name];
      const response = await fetch(apiUrl(endpoint), {headers});
      if (!response.ok) throw new Error('Artifact unavailable or access expired');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = url; link.download = name; link.click();
      setTimeout(() => URL.revokeObjectURL(url),30000);
    } catch (cause) { setError((cause as Error).message); }
  }

  const geometry = report?.experimental_geometry;
  const candidates = geometry?.candidates ?? [];
  const primaryCandidate = candidates[0];
  const geometryReason = geometry?.reasons?.[0]?.replaceAll('_',' ') ?? '';

  if (historyOnly) return <section className="volume-inference" aria-label="3D analysis history">
    <h3>3D analysis history</h3>
    {error && <p role="alert">{error}</p>}
    {!runs.length ? <p>No saved volume analyses.</p> : <table className="stenosis-summary">
      <thead><tr><th>Date</th><th>Run</th><th>Status</th><th>Model</th><th>Duration</th></tr></thead>
      <tbody>{runs.map(run => <tr key={run.id}><td>{utcDate(run.created_at).toLocaleString()}</td><td>{run.id}</td><td>{run.status}</td><td>{run.result?.model_id ?? run.model_key ?? 'Unavailable'}</td><td>{run.result ? `${run.result.duration_seconds.toFixed(2)} s` : 'Unavailable'}</td></tr>)}</tbody>
    </table>}
    {onOpenAnalysis && <Button onClick={onOpenAnalysis}>Open analysis viewer</Button>}
  </section>;
  return <section className="volume-inference" aria-labelledby="volume-inference-title">
    <header><p className="eyebrow">VOLUME ANALYSIS</p><h3 id="volume-inference-title">{anatomy==='aorta'?'Aortic CT':'Coronary CTA'} segmentation</h3>
      <p>View a 3D vessel mask and slice previews. CoroVision selects the research pipeline from the case anatomy. Small vessels may be missed.</p></header>
    {!readOnly && <form onSubmit={start} className="volume-run-form" aria-busy={busy}>
      <label>Original de-identified {anatomy==='aorta'?'CT/CTA':'coronary CTA'} volume<input type="file" accept=".nii,.nii.gz,.zip" required={!dicomFiles.length} disabled={busy} aria-describedby={error ? 'volume-input-help volume-error' : 'volume-input-help'} onChange={e => { setFile(e.target.files?.[0] || null); setError(''); }} /></label>
      <p id="volume-input-help">NIfTI or a ZIP containing exactly one de-identified CT DICOM series · up to {Math.floor(limits.max_file_bytes/1024/1024)} MiB and {(limits.max_source_voxels/1_000_000).toFixed(0)} million native voxels. DICOM reconstruction checks series identity, slice ordering, orientation and spacing before inference. NIfTI headers must specify millimetres. JPEG/PNG images and 4D sequences are not 3D CT volumes.</p>
      <label className="volume-confirm"><input type="checkbox" checked={hu} onChange={e => setHu(e.target.checked)} required />I confirm original Hounsfield-unit CT intensities, not a normalized or enhanced export.</label>
      <label className="volume-confirm"><input type="checkbox" checked={research} onChange={e => setResearch(e.target.checked)} required />I confirm de-identification and research-only use; this model is not clinically validated.</label>
      <label>Or select a complete DICOM series<input type="file" multiple accept=".dcm,.dicom" disabled={busy} onChange={e => {setDicomFiles(Array.from(e.target.files || [])); setError('');}} /></label>
      {dicomFiles.length > 0 && <p role="status">{dicomFiles.length} slices selected · {(dicomFiles.reduce((sum,f)=>sum+f.size,0)/1024/1024).toFixed(1)} MiB. These slices take precedence over the single-file input. Select exactly one study and series; mixed series are rejected.</p>}
      {busy && <div role="status"><progress aria-label="Volume upload progress" max={100} value={uploadPercent ?? undefined} />{uploadPercent === 100 ? 'Upload complete. Validating source geometry…' : uploadPercent === null ? 'Uploading volume…' : `Uploading volume: ${uploadPercent}%`}</div>}
      <Button type="submit" disabled={!installed || (!file && !dicomFiles.length) || !hu || !research || busy || active}>{busy ? 'Uploading and validating…' : active ? '3D analysis in progress…' : 'Run 3D segmentation'}</Button>
      {!installed && <p role="status">Volume analysis is unavailable for this case on this installation.</p>}
    </form>}
    {error && <p id="volume-error" role="alert" className="message error">{error}</p>}
    <section className="volume-saved-results" aria-label="Saved 3D results">
      <h4>Saved 3D analyses</h4>
      {!runs.length ? <p>No 3D analyses yet.</p> : <>
        <label>Analysis run<select value={selected?.id || ''} onChange={e => { setChosen(e.target.value); setViewingRun(''); }}>{runs.map(run => <option key={run.id} value={run.id}>{utcDate(run.created_at).toLocaleString()} · {run.status} · {run.id.slice(0,8)}</option>)}</select></label>
        <p role="status">Status: {selected?.status}{selected?.error ? ` — ${selected.error}` : ''}</p>
        {selected?.result && <>
          {selected.input_kind === 'synthetic_fixture' && <div className="message warning" role="note"><strong>Synthetic geometry test — not a medical scan.</strong><p>This saved run used an artificial gradient, not coronary CTA anatomy. Grey slices and an empty vessel mask do not demonstrate medical segmentation. Upload a real, de-identified CTA from Assets & preparation.</p></div>}
          {selected.input_kind === 'unspecified' && <p className="message warning">Legacy source provenance is unspecified. Verify the original volume before interpreting this result.</p>}
          <p className="volume-run-meta">{selected.result.duration_seconds.toFixed(2)} s · {selected.result.source_shape.join(' × ')} voxels · {selected.result.coarse_foreground_voxels.toLocaleString()} predicted coarse-grid voxels</p>
          {selected.result.coarse_foreground_voxels === 0 && <p className="message warning">No vessel overlay was produced by this model. This is not a healthy/normal finding; check source eligibility and image quality and obtain expert review.</p>}
          <section className="volume-findings-summary" aria-labelledby="volume-findings-title">
            <div className="volume-findings-heading"><div><p className="eyebrow">SAVED 3D CASE</p><h4 id="volume-findings-title">Analysis findings</h4></div><strong className="volume-result-status">{selected.status}</strong></div>
            <dl className="volume-summary-grid">
              <div><dt>Model</dt><dd>{selected.result.model_id}</dd></div>
              <div><dt>Source volume</dt><dd>{selected.result.source_shape.join(' × ')} voxels</dd></div>
              <div><dt>Segmentation</dt><dd>Saved prediction · review required</dd></div>
              <div><dt>Vessel geometry</dt><dd>{geometryReason ? `Not assessable · ${geometryReason}` : geometry ? `${geometry.paths?.length ?? 0} extracted paths` : 'Loading assessment…'}</dd></div>
              <div><dt>Stenosis candidates</dt><dd>{candidates.length ? `${candidates.length} experimental candidate${candidates.length === 1 ? '' : 's'}` : 'None eligible'}</dd></div>
              <div><dt>Estimated narrowing</dt><dd>{primaryCandidate ? `${primaryCandidate.narrowing_percent.toFixed(2)}%` : 'Not assessable'}</dd></div>
              <div className="volume-severity-result"><dt>Severity grading</dt><dd>{primaryCandidate ? primaryCandidate.severity : 'Not assessable'}</dd></div>
              <div><dt>Reason</dt><dd>{primaryCandidate ? 'Experimental mask-geometry result; expert review required.' : geometryReason ? `Measurement withheld because the saved prediction is ${geometryReason}.` : 'No eligible 3D narrowing measurement is available.'}</dd></div>
            </dl>
          </section>
          {selected.preview_url && selected.result.coarse_foreground_voxels > 0 && <section aria-label="Interactive vessel mask">
            <Button type="button" aria-expanded={viewingRun === selected.id} onClick={() => setViewingRun(viewingRun === selected.id ? '' : selected.id)}>
              {viewingRun === selected.id ? 'Close 3D viewer' : 'Open 360° vessel viewer'}
            </Button>
            {viewingRun === selected.id && <VolumeOrbit key={selected.id} url={selected.preview_url} token={token}
              shape={selected.result.source_shape} slices={selected.result.slices} previews={previews} />}
          </section>}
          <details open={selected.input_kind !== 'synthetic_fixture'} key={selected.id}><summary>{selected.input_kind === 'synthetic_fixture' ? 'Show synthetic test slices (not medical images)' : 'Slice previews from three directions'}</summary>
          <div className="volume-slices">{selected.result.slices.map(slice => <figure key={slice.artifact}>
            {previews[slice.artifact] ? <img src={previews[slice.artifact]} alt={`Predicted coronary overlay on ${slice.axis} slice ${slice.coarse_index}`} /> : <p>Loading saved preview…</p>}
            <figcaption>{slice.axis} · coarse slice {slice.coarse_index}</figcaption></figure>)}</div></details>
          <div className="volume-downloads"><Button onClick={() => void download('mask_source.nii.gz')}>Download source-grid mask</Button><Button onClick={() => void download('probability_coarse.nii.gz')}>Download coarse probability volume</Button><Button onClick={() => void download('result.json')}>Download result JSON</Button></div>
          <section className="volume-measurement-report" aria-label="3D measurement report">
            <div className="volume-section-heading"><h4>Measurement details</h4><Button onClick={()=>void download('evidence.zip')}>Download evidence ZIP</Button></div>
            {reportError ? <p role="alert">{reportError}</p> : !report ? <p role="status">Loading saved-run report…</p> : <>
              {report.experimental_geometry && <section aria-label="Experimental 3D geometry">
                <VolumeMeasurementPanel candidates={report.experimental_geometry.candidates ?? []} />
                <div className="volume-subsection-heading"><h4>Candidate measurements</h4><span>{(report.experimental_geometry.paths ?? []).length} paths · {(report.experimental_geometry.paths ?? []).reduce((sum,path)=>sum+path.length_mm,0).toFixed(2)} mm traced</span></div>
                <table className="stenosis-summary"><thead><tr><th>Candidate / path</th><th>Minimum width</th><th>Reference width</th><th>Narrowing</th><th>Experimental grade</th><th>RAS location (mm)</th></tr></thead>
                  <tbody>{(report.experimental_geometry.candidates ?? []).map(candidate=><tr key={candidate.id}><td>{candidate.id} / {candidate.path_id}</td><td>{candidate.minimum_diameter_mm.toFixed(2)} mm<br/>{candidate.minimum_area_mm2?.toFixed(2)} mm²</td><td>{candidate.reference_diameter_mm.toFixed(2)} mm<br/>{candidate.reference_area_mm2?.toFixed(2)} mm²</td><td>Diameter {candidate.narrowing_percent.toFixed(2)}%<br/>Area {candidate.area_narrowing_percent?.toFixed(2)}%</td><td>{candidate.severity}</td><td>{candidate.location_ras_mm.map(value=>value.toFixed(2)).join(', ')}</td></tr>)}</tbody>
                </table>
                {!(report.experimental_geometry.candidates ?? []).length && <p>No candidate met the experimental path-length and narrowing rules.</p>}
                {(report.experimental_geometry.limitations?.length
                  ? report.experimental_geometry.limitations
                  : (report.experimental_geometry.reasons ?? []).map(reason => `Measurement withheld: ${reason.replaceAll('_',' ')}.`)
                ).slice(0,1).map(text=><p className="message warning volume-primary-warning" role="note" key={text}>{text}</p>)}
                {(report.experimental_geometry.limitations?.length ?? 0) > 1 && <details className="volume-method-notes"><summary>Method notes</summary><ul>{report.experimental_geometry.limitations?.slice(1).map(text=><li key={text}>{text}</li>)}</ul></details>}
              </section>}
              {!report.experimental_geometry && <table className="stenosis-summary">
                <caption>Selected 3D scan measurement assessment</caption>
                <thead><tr><th scope="col">Minimum lumen</th><th scope="col">Reference lumen</th><th scope="col">Narrowing</th><th scope="col">Research severity</th></tr></thead>
                <tbody><tr><td>Unavailable</td><td>Unavailable</td><td>Unavailable</td><td>{report.stages.severity?.status.replaceAll('_', ' ') ?? 'Unavailable'}</td></tr></tbody>
              </table>}
              <dl className="volume-stage-grid">{Object.entries(report.stages).map(([name,item])=>{
                const withheld = geometry?.status === 'abstained' && name !== 'segmentation';
                const status = withheld ? 'not assessable' : item.status.replaceAll('_',' ');
                return <div key={name}>
                  <dt>{name.replaceAll('_',' ')}</dt>
                  <dd>{status}</dd>
                </div>;
              })}</dl>
              <div className="volume-downloads"><Button onClick={()=>void download('research-report.json')}>Export 3D research JSON</Button><Button onClick={()=>void download('research-report.csv')}>Export 3D stage CSV</Button><Button onClick={()=>void download('research-report.pdf')}>Export 3D research PDF</Button></div>
            </>}
          </section>
          <details><summary>Model limitations and provenance</summary><p>Run: {selected.id} · Model: {selected.result.model_id}. The vessel mask is mapped back to the original volume grid.</p><ul>{(selected.result.limitations ?? []).map(value => <li key={value}>{value}</li>)}</ul></details>
        </>}
      </>}
    </section>
  </section>;
}
