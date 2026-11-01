import { useEffect, useRef, useState } from 'react';
import { Download, Printer, Save } from 'lucide-react';
import ResultEvidence from './ResultEvidence';
import { apiUrl, request } from './api';
import type { AnalysisResult, CaseRecord, ClinicalReviewRecord, ImageRecord } from './caseTypes';
import { Button } from './components/prismui/button';
import { Card } from './components/prismui/card';
import { canExportReports } from './permissions';
import ImagePanelGallery, { type ImagePanel } from './ImagePanelGallery';

type Snapshot = {
  report_id: string; version: number; generated_at: string; sections: string[];
  case: { id: string; case_code: string; modality: string; anatomy: string };
  image: { id: string; original_name: string; width: number; height: number };
  analysis: AnalysisResult; human_review: ClinicalReviewRecord | null; review_history: ClinicalReviewRecord[];
  provenance: object; limitations: string[]; image_panels?: ImagePanel[];
};
type ReportIndex = { id: string; version: number; image_id: string; analysis_event_id: string; created_at: string };
const choices = [['images', 'Original image & overlay'], ['measurements', 'Vessel measurements & units'], ['candidates', 'Stenosis candidate evidence'], ['review', 'Run-linked human assessment'], ['appendix', 'Technical evaluation references']];

export default function ReportsPage({ token, role, cases, selectedCase, selectedImage, analysis, history, onSelectAnalysis, onCaseChange, onImageChange, onAnalysis }: {
  token: string; role: string; cases: CaseRecord[]; selectedCase?: CaseRecord; selectedImage?: ImageRecord;
  analysis: AnalysisResult | null; history: AnalysisResult[]; onSelectAnalysis: (result: AnalysisResult) => void;
  onCaseChange: (id: string) => void; onImageChange: (id: string) => void; onAnalysis: () => void;
}) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [reports, setReports] = useState<ReportIndex[]>([]);
  const [sections, setSections] = useState(['images', 'measurements', 'candidates', 'review']);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const allowed = !!selectedCase?.permissions?.can_export && canExportReports(role);
  const context = useRef('');
  context.current = `${selectedCase?.id}:${selectedImage?.id}:${analysis?.id}`;
  useEffect(() => {
    setSnapshot(null); setReports([]); setError('');
    if (!selectedCase || !allowed) return;
    let active = true;
    request<ReportIndex[]>(`/api/cases/${selectedCase.id}/research-reports`, token)
      .then(data => { if (active) setReports(data); }).catch(cause => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [selectedCase?.id, token, allowed]);
  useEffect(() => { setSnapshot(null); }, [selectedImage?.id, analysis?.id]);
  async function generate() {
    if (!selectedCase || !selectedImage || !analysis || analysis.image_id !== selectedImage.id) return;
    setBusy(true); setError('');
    const selection = context.current;
    try {
      const saved = await request<Snapshot>(`/api/cases/${selectedCase.id}/research-reports`, token, { image_id: selectedImage.id, analysis_event_id: analysis.id, sections }, 'POST');
      if (context.current !== selection) return;
      setSnapshot(saved);
      const versions = await request<ReportIndex[]>(`/api/cases/${selectedCase.id}/research-reports`, token);
      if (context.current === selection) setReports(versions);
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }
  async function openReport(id: string) {
    if (!id || !selectedCase) { setSnapshot(null); return; }
    setBusy(true); setError('');
    const selection = context.current;
    try { const saved = await request<Snapshot>(`/api/cases/${selectedCase.id}/research-reports/${id}`, token); if (context.current === selection) setSnapshot(saved); }
    catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }
  async function exportReport(format: 'json' | 'csv' | 'pdf') {
    if (!snapshot) return;
    setBusy(true); setError('');
    try {
      const response = await fetch(apiUrl(`/api/cases/${snapshot.case.id}/research-reports/${snapshot.report_id}/export/${format}`), { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || 'Export failed');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = url;
      link.download = `${snapshot.case.case_code.replace(/[^a-z0-9_-]/gi, '_')}-research-v${snapshot.version}.${format}`;
      link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }
  const result = snapshot?.analysis;
  return <div className="reports-page">
    <div className="page-heading"><div><p className="eyebrow">DOCUMENT · SAVED ANALYSIS</p><h2>Research Reports</h2><p className="muted">One image, one saved run, an immutable report version.</p></div><span className="stage-badge">Research only · not clinical approval</span></div>
    <p className="caption">New report source · these selectors configure the next saved version.</p>
    <div className="report-actions">
      <label>Case<select value={selectedCase?.id || ''} onChange={e => onCaseChange(e.target.value)}><option value="">Select a case</option>{cases.map(c => <option key={c.id} value={c.id}>{c.case_code}</option>)}</select></label>
      <label>Image<select value={selectedImage?.id || ''} onChange={e => onImageChange(e.target.value)} disabled={!selectedCase?.images.length}><option value="">Select an image</option>{selectedCase?.images.map(i => <option key={i.id} value={i.id}>{i.original_name}</option>)}</select></label>
      <label>Analysis run<select value={analysis?.id || ''} disabled={!history.length} onChange={e => { const run = history.find(r => r.id === e.target.value); if (run) onSelectAnalysis(run); }}><option value="">Select saved run</option>{history.map(r => <option key={r.id} value={r.id}>{new Date(r.created_at).toLocaleString()} · {r.id.slice(0, 8)}</option>)}</select></label>
      <Button variant="outline" onClick={onAnalysis}>Back to Image Review</Button>
    </div>
    {error && <p role="alert" className="message error">{error}</p>}
    {!allowed ? <Card className="panel"><h3>Research export permission required</h3><p>Approved clinical reports remain in the case’s existing approval workflow. Research snapshots require case access and export permission.</p></Card> : <div className="report-builder-grid">
      <Card className="panel report-contents"><p className="eyebrow">REPORT BUILDER</p><h3>Contents</h3><p className="caption">Identifiers, provenance and safety limitations are mandatory.</p>
        <fieldset disabled={busy}><legend>Optional sections</legend>{choices.map(([key, label]) => <label className="report-section-choice" key={key}><input type="checkbox" checked={sections.includes(key)} onChange={e => setSections(p => e.target.checked ? [...p, key] : p.filter(k => k !== key))} />{label}</label>)}</fieldset>
        <Button className="primary" disabled={busy || !analysis || analysis.image_id !== selectedImage?.id} onClick={generate}><Save size={16} aria-hidden="true" />{busy ? 'Working…' : 'Save new report version'}</Button>
        <label>Saved report version<select disabled={busy || !reports.length} value={snapshot?.report_id || ''} onChange={e => openReport(e.target.value)}><option value="">Select a saved version</option>{reports.map(r => <option key={r.id} value={r.id}>v{r.version} · run {r.analysis_event_id.slice(0, 8)} · {new Date(r.created_at).toLocaleString()}</option>)}</select></label>
        <p className="caption">{reports.length} saved versions. Controls configure the next report; existing snapshots are never edited.</p>
      </Card>
      <Card className="panel report-sheet">
        {!snapshot ? <><h3>Choose your report source</h3><p>Select an analyzed image, then save a report version or open an earlier snapshot. No empty draft is presented as a completed report.</p></> : <>
          <div className="report-heading"><div><p className="eyebrow">COROVISION AI · RESEARCH ANALYSIS REPORT</p><h3>{snapshot.case.case_code} · v{snapshot.version}</h3></div></div>
          {snapshot.analysis.id !== analysis?.id && <p className="privacy-note">Viewing an earlier saved snapshot from run {snapshot.analysis.id}. Exports below use this snapshot, not the new-report source selected above.</p>}
          <div className="report-export-buttons">{(['json', 'csv', 'pdf'] as const).map(format => <Button key={format} variant="outline" disabled={busy} onClick={() => exportReport(format)}><Download size={16} aria-hidden="true" />{format.toUpperCase()}</Button>)}<Button variant="outline" onClick={() => window.print()}><Printer size={16} aria-hidden="true" />Print</Button></div>
          <p className="caption">Saved {new Date(snapshot.generated_at).toLocaleString()} · Report {snapshot.report_id}</p>
          <div className="report-facts">{[['Case ID', snapshot.case.id], ['Image', `${snapshot.image.original_name} · ${snapshot.image.width} × ${snapshot.image.height}`], ['Analysis run', result?.id], ['Model version', result?.model_version], ['Modality / anatomy', `${snapshot.case.modality} · ${snapshot.case.anatomy}`], ['Analysis timestamp', result?.created_at]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
          {snapshot.sections.includes('images') && <ImagePanelGallery token={token} imageId={snapshot.image.id} runId={snapshot.analysis.id} modelVersion={snapshot.analysis.model_version} panels={snapshot.image_panels} />}
          <div className="report-facts"><div><span>Artery mask</span><strong>{result?.artery_pixels ?? 'Unavailable'} px</strong></div><div><span>Stenosis mask</span><strong>{result?.stenosis_pixels ?? 'Unavailable'} px</strong></div><div><span>Automated severity</span><strong>Not assessed · insufficient validated evidence</strong></div></div>
          {snapshot.sections.includes('measurements') && <section><h4>Derived vessel measurements</h4><div className="report-facts">{[['Centerline length', result?.vessel_analysis?.centerline_length], ['Mean diameter', result?.vessel_analysis?.mean_diameter], ['Branch candidates', result?.vessel_analysis?.branching_points]].map(([label, value]) => <div key={String(label)}><span>{label}</span><strong>{value ?? 'Unavailable'} {value != null && label !== 'Branch candidates' ? result?.vessel_analysis?.diameter_unit : ''}</strong></div>)}</div></section>}
          {snapshot.sections.includes('candidates') && <details><summary>Candidate evidence · {result?.structured_result?.candidates.length ?? 'Unavailable'}</summary>{result?.structured_result?.candidates.map(c => <p key={c.candidate_id}>{c.candidate_id} · raw score {c.model_score ?? 'Unavailable'} · prepared bounds {c.bbox_prepared_xyxy?.join(', ') || 'Unavailable'}</p>)}</details>}
          {snapshot.sections.includes('review') && <section className="report-review"><h4>Run-linked human assessment</h4>{snapshot.human_review ? <><p>{snapshot.human_review.reviewer_role} · {snapshot.human_review.reviewer_name || snapshot.human_review.reviewer_id}</p><p>Decision: {snapshot.human_review.decision} · assessed severity: {snapshot.human_review.stenosis_severity || 'Unspecified'}</p><p>{snapshot.human_review.notes || 'No notes'}</p><small>{snapshot.human_review.created_at} · Review {snapshot.human_review.id}</small></> : <p>No assessment linked to this exact run. Case-only reviews are not silently substituted.</p>}</section>}
          <details><summary>Model & preprocessing provenance</summary><pre className="provenance-json">{JSON.stringify(snapshot.provenance, null, 2)}</pre></details>
          <details><summary>Evidence-based explanation & skipped stages</summary><ResultEvidence result={result?.structured_result} /></details>
          {snapshot.sections.includes('appendix') && <details><summary>Recorded evaluation references</summary><pre className="provenance-json">{JSON.stringify(result?.validation, null, 2)}</pre></details>}
          <section><h4>Warnings & limitations</h4><ul>{snapshot.limitations.map((l, i) => <li key={i}>{l}</li>)}{result?.vessel_analysis?.quality_flags?.map(f => <li key={f.code}>{f.message}</li>)}</ul></section>
        </>}
      </Card>
    </div>}
  </div>;
}
