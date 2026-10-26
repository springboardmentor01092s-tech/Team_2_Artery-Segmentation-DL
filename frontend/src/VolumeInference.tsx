import { useEffect, useState } from 'react';
import { apiUrl } from './api';
import { Button } from './components/prismui/button';

type VolumeRun = { id: string; status: string; error: string | null; created_at: string;model_key?:string;
  input_kind: 'medical_study' | 'synthetic_fixture' | 'unspecified';
  artifacts: Record<string,string>; result: null | { model_id: string; duration_seconds: number;
  coarse_foreground_voxels: number; source_shape: number[]; limitations: string[];
  slices: { axis: string; coarse_index: number; artifact: string }[] } };

export default function VolumeInference({caseId, token, readOnly = false,anatomy='coronary'}: {caseId: string; token: string; readOnly?: boolean;anatomy?:string}) {
  const [modelKey,setModelKey]=useState('imagecas');
  const [models,setModels]=useState<Array<{model_key:string;title:string;anatomy:string;installed:boolean;limits:{max_file_bytes:number;max_source_voxels:number}}>>([]);
  const [file, setFile] = useState<File | null>(null);
  const [hu, setHu] = useState(false);
  const [research, setResearch] = useState(false);
  const [installed, setInstalled] = useState(false);
  const [limits, setLimits] = useState({max_file_bytes:384*1024*1024, max_source_voxels:96_000_000});
  const [runs, setRuns] = useState<VolumeRun[]>([]);
  const [chosen, setChosen] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [previews, setPreviews] = useState<Record<string,string>>({});
  const selected = runs.find(r => r.id === chosen) || runs[0];
  const active = runs.some(r => ['queued','running'].includes(r.status));
  const headers = {Authorization: `Bearer ${token}`};

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
      .then(rows => { if (!disposed) { const eligible=rows.filter((r:{anatomy:string})=>r.anatomy===anatomy);setModels(eligible);const chosen=eligible.find((r:{model_key:string})=>r.model_key===modelKey)||eligible[0];if(chosen){setModelKey(chosen.model_key);setInstalled(Boolean(chosen.installed));setLimits(chosen.limits);}else setInstalled(false); } })
      .catch(cause => { if (!disposed) setError(cause.message); });
    return () => { disposed = true; clearTimeout(timer); };
  }, [caseId, token, active, busy,modelKey,anatomy]);

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
    if (!file || busy) return;
    setBusy(true); setError('');
    try {
      if (!/\.nii(\.gz)?$/i.test(file.name) || !file.size || file.size > limits.max_file_bytes)
        throw new Error(`Choose an intact .nii or .nii.gz file between 1 byte and ${Math.floor(limits.max_file_bytes/1024/1024)} MiB`);
      const body = new FormData();
      body.append('file',file); body.append('hu_confirmed',String(hu)); body.append('research_confirmed',String(research)); body.append('input_kind','medical_study');
      body.append('model_key',modelKey);
      const response = await fetch(apiUrl(`/api/cases/${caseId}/volumes/analyses`), {method:'POST', headers, body});
      if (!response.ok) throw new Error((await response.json()).detail || '3D inference rejected');
      const row: VolumeRun = await response.json();
      setRuns(previous => [row,...previous]); setChosen(row.id);
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }

  async function download(name: string) {
    if (!selected) return;
    try {
      const response = await fetch(apiUrl(selected.artifacts[name]), {headers});
      if (!response.ok) throw new Error('Artifact unavailable or access expired');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = url; link.download = name; link.click();
      setTimeout(() => URL.revokeObjectURL(url),30000);
    } catch (cause) { setError((cause as Error).message); }
  }

  return <section className="volume-inference" aria-labelledby="volume-inference-title">
    <header><p className="eyebrow">Separate 3D research pipeline</p><h3 id="volume-inference-title">{anatomy==='aorta'?'Aortic CT':'Coronary CTA'} segmentation</h3>
      <p>Preserved 3D U-Net checkpoints · coarse 128³ full-field input. No training starts here. Small vessels may be lost; results require expert review. AortaSeg uses AI pseudo-reference training labels.</p></header>
    {!readOnly && <form onSubmit={start} className="volume-run-form" aria-busy={busy}>
      <label>3D task checkpoint<select value={modelKey} disabled={busy||active} onChange={e=>setModelKey(e.target.value)}>{models.map(model=><option key={model.model_key} value={model.model_key} disabled={!model.installed}>{model.title}{!model.installed?' · unavailable':''}</option>)}</select></label>
      <label>Original de-identified {anatomy==='aorta'?'CT/CTA':'coronary CTA'} NIfTI<input type="file" accept=".nii,.nii.gz" required disabled={busy} aria-describedby={error ? 'volume-input-help volume-error' : 'volume-input-help'} onChange={e => { setFile(e.target.files?.[0] || null); setError(''); }} /></label>
      <p id="volume-input-help">NIfTI only · up to {Math.floor(limits.max_file_bytes/1024/1024)} MiB and {(limits.max_source_voxels/1_000_000).toFixed(0)} million native voxels. The header must specify millimetres. JPEG/PNG images and 4D sequences are not 3D CT volumes.</p>
      <label className="volume-confirm"><input type="checkbox" checked={hu} onChange={e => setHu(e.target.checked)} required />I confirm original Hounsfield-unit CT intensities, not a normalized or enhanced export.</label>
      <label className="volume-confirm"><input type="checkbox" checked={research} onChange={e => setResearch(e.target.checked)} required />I confirm de-identification and research-only use; this model is not clinically validated.</label>
      <Button type="submit" disabled={!installed || !file || !hu || !research || busy || active}>{busy ? 'Uploading and validating…' : active ? '3D analysis in progress…' : 'Run 3D segmentation'}</Button>
      {!installed && <p role="status">Pinned 3D checkpoint is not installed. Inference is unavailable.</p>}
    </form>}
    {error && <p id="volume-error" role="alert" className="message error">{error}</p>}
    <section className="volume-saved-results" aria-label="Saved 3D results">
      <h4>Saved 3D analyses</h4>
      {!runs.length ? <p>No 3D analyses yet.</p> : <>
        <label>Analysis run<select value={selected?.id || ''} onChange={e => setChosen(e.target.value)}>{runs.map(run => <option key={run.id} value={run.id}>{run.model_key||'imagecas'} · {new Date(run.created_at).toLocaleString()} · {run.status} · {run.id.slice(0,8)}</option>)}</select></label>
        <p role="status">Status: {selected?.status}{selected?.error ? ` — ${selected.error}` : ''}</p>
        {selected?.result && <>
          {selected.input_kind === 'synthetic_fixture' && <div className="message warning" role="note"><strong>Synthetic geometry test — not a medical scan.</strong><p>This saved run used an artificial gradient, not coronary CTA anatomy. Grey slices and an empty vessel mask do not demonstrate medical segmentation. Upload a real, de-identified CTA from Assets & preparation.</p></div>}
          {selected.input_kind === 'unspecified' && <p className="message warning">Legacy source provenance is unspecified. Verify the original volume before interpreting this result.</p>}
          <p>{selected.result.model_id} · {selected.result.duration_seconds.toFixed(2)} s · source {selected.result.source_shape.join(' × ')} voxels</p>
          <p>Predicted foreground: {selected.result.coarse_foreground_voxels.toLocaleString()} coarse-grid voxels. This is not an accuracy score or anatomical volume measurement.</p>
          <p className="message warning">A completed job does not establish anatomically correct segmentation. Predictions can include false positives and missed vessels; no reference coronary mask was used to validate this result.</p>
          {selected.result.coarse_foreground_voxels === 0 && <p className="message warning">No vessel overlay was produced by this model. This is not a healthy/normal finding; check source eligibility and image quality and obtain expert review.</p>}
          <details open={selected.input_kind !== 'synthetic_fixture'} key={selected.id}><summary>{selected.input_kind === 'synthetic_fixture' ? 'Show synthetic test slices (not medical images)' : 'Orthogonal slice previews — not an interactive 3D reconstruction'}</summary>
          <div className="volume-slices">{selected.result.slices.map(slice => <figure key={slice.artifact}>
            {previews[slice.artifact] ? <img src={previews[slice.artifact]} alt={`Predicted coronary overlay on ${slice.axis} slice ${slice.coarse_index}`} /> : <p>Loading saved preview…</p>}
            <figcaption>{slice.axis} · coarse slice {slice.coarse_index}</figcaption></figure>)}</div></details>
          <div className="volume-downloads"><Button onClick={() => void download('mask_source.nii.gz')}>Download source-grid mask</Button><Button onClick={() => void download('probability_coarse.nii.gz')}>Download coarse probability volume</Button><Button onClick={() => void download('result.json')}>Download result JSON</Button></div>
          <details><summary>Model limitations and provenance</summary><p>Run: {selected.id}. Predictions use the pinned ImageCAS checkpoint; the mask is resampled back to source geometry without recovering lost detail.</p><ul>{selected.result.limitations.map(value => <li key={value}>{value}</li>)}</ul></details>
        </>}
      </>}
    </section>
  </section>;
}
