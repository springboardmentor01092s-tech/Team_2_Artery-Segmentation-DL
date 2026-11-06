import { useState } from 'react';

type Row = Record<string, unknown>;
function object(value: unknown): Row | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Row : null;
}
const finite = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);

export default function WidthProfileReview({ value, runId, expanded = false, candidateId }: { value: unknown; runId: string; expanded?: boolean; candidateId?: string }) {
  const [selected, setSelected] = useState('');
  const bundle = object(value);
  if (!bundle) return <p className="caption">{candidateId ? `No saved candidate-linked width profile for ${candidateId}. Lesion diameters and narrowing are unavailable; whole-vessel profiles are not substituted.` : "No saved ordered width profiles are available for this historical run."}</p>;
  if (bundle.analysis_run_id !== runId) return <p className="caption">Width-profile run identity mismatch; display blocked.</p>;
  if (bundle.status === 'unavailable') return <p className="caption">Width profiles unavailable: {String(bundle.reason || 'Source geometry unavailable')}</p>;
  const profiles = Array.isArray(bundle.profiles) ? bundle.profiles.map(object).filter((v): v is Row => v !== null && v.analysis_run_id === runId && v.unit === 'pixels' && Array.isArray(v.samples) && (!candidateId || v.candidate_id === candidateId)) : [];
  const profile = profiles.find(v => v.profile_id === selected) || profiles[0];
  const samples = profile && Array.isArray(profile.samples) ? profile.samples.map(object).filter((s): s is Row & { arc_length: number; width: number } => s !== null && finite(s.arc_length) && finite(s.width) && s.arc_length >= 0 && s.width > 0) : [];
  const xmax = Math.max(1, ...samples.map(s => s.arc_length));
  const ymax = Math.max(1, ...samples.map(s => s.width));
  const points = samples.map(s => `${40+520*s.arc_length/xmax},${180-150*s.width/ymax}`).join(' ');
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `width-profiles-${runId}.json`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return <details open={expanded || undefined} className="evidence-details width-profile-review"><summary>{candidateId ? `Selected candidate ${candidateId} · saved width profile` : 'Ordered source-image mask-width profiles'}</summary>
    <p className="caption">Source-pixel research estimates derived from 2D mask widths. These are not validated lumen diameters, clinical narrowing percentages or anatomical artery identities.</p>
    {profiles.length ? <>
      <label>Saved path <select value={String(profile?.profile_id || '')} onChange={event => setSelected(event.target.value)}>
        {profiles.map(p => <option key={String(p.profile_id)} value={String(p.profile_id)}>{String(p.vessel_path_id)}</option>)}
      </select></label>
      {profile?.ambiguous_multiple_paths === true && <p role="status" className="caption">Multiple saved paths overlap this candidate. The selected interval is ambiguous and requires review; no anatomical vessel identity is assigned.</p>}
      <div className="profile-sample-summary" aria-label="Saved path measurements">
        <div><span>Minimum mask width</span><strong>{samples.length ? Math.min(...samples.map(s => s.width)).toFixed(2) : '—'} <small>px</small></strong></div>
        <div><span>Maximum mask width</span><strong>{samples.length ? ymax.toFixed(2) : '—'} <small>px</small></strong></div>
        <div><span>Sampled path extent</span><strong>{samples.length ? Math.max(...samples.map(s => s.arc_length)).toFixed(2) : '—'} <small>px</small></strong></div>
      </div>
      <svg viewBox="0 0 600 225" role="img" aria-label="Saved mask width versus ordered distance along the path" style={{ width: '100%', maxWidth: 700 }}>
        <line x1="40" y1="180" x2="560" y2="180" stroke="currentColor" />
        <line x1="40" y1="30" x2="40" y2="180" stroke="currentColor" />
        <polyline points={points} fill="none" stroke="#27a7a0" strokeWidth="2" />
        <text x="200" y="215" fill="currentColor">Path distance (source pixels)</text>
        <text x="45" y="20" fill="currentColor">Mask width (source pixels), maximum {ymax.toFixed(2)}</text>
        <text x="480" y="198" fill="currentColor">{xmax.toFixed(2)}</text>
      </svg>
      <p className="caption">{samples.length} saved samples · coordinate frame {String(profile?.coordinate_frame)} · method {String(profile?.method)}</p>
      <p className="caption">{samples.filter(s => Array.isArray(s.quality_flags) && s.quality_flags.length).length} samples have branch/border review flags. Review individual flags in the evidence download.</p>
    </> : <p className="caption">{candidateId ? 'No candidate-linked width profile was saved for this region. Whole-vessel profiles are not substituted for lesion measurements.' : 'No usable open paths were saved. This does not establish absence of disease.'}</p>}
    <p className="caption">Rejected paths: {Array.isArray(bundle.rejected_paths) ? bundle.rejected_paths.length : 0}. Uncertainty and reference-lumen validation remain unavailable.</p>
    <button type="button" onClick={download}>Download run-bound width evidence</button>
  </details>;
}
