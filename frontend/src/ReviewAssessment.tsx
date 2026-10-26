import { useState, type FormEvent } from 'react';
import type { AnalysisResult, CaseRecord } from './caseTypes';
import { request } from './api';
import { reviewLabels } from './reviewLabels';
import { reviewsForRun } from './reviewEvidence';
import { Button } from './components/prismui/button';

export default function ReviewAssessment({ token, role, caseRecord, analysis, onSaved }: {
  token: string; role: string; caseRecord: CaseRecord; analysis: AnalysisResult | null; onSaved: (record: CaseRecord) => void;
}) {
  const [decision, setDecision] = useState('reviewed');
  const [severity, setSeverity] = useState('unspecified');
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const labels = reviewLabels(role);
  const linked = reviewsForRun(caseRecord.reviews || [], analysis?.id);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!analysis) return;
    setBusy(true); setError(''); setMessage('');
    try {
      const updated = await request<CaseRecord>(`/api/cases/${caseRecord.id}/review`, token, {
        decision, stenosis_severity: severity, notes: notes.trim() || null,
        image_id: analysis.image_id, analysis_event_id: analysis.id,
      }, 'POST');
      onSaved(updated); setNotes(''); setMessage('Human assessment saved for this exact analysis run.');
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }
  return <section className="panel review-assessment" aria-labelledby="assessment-heading">
    <header className="assessment-heading"><p className="eyebrow">HUMAN ASSESSMENT</p><h3 id="assessment-heading">{labels.decision}</h3><p className="caption">Separate from model predictions. No automated clinical grade or urgency is assigned.</p></header>
    <div className="assessment-evidence"><span>Evidence run</span><code>{analysis?.id || 'Select a completed analysis'}</code></div>
    {caseRecord.permissions?.can_review && analysis ? <form onSubmit={submit}>
      <div className="case-form-grid"><label>Review outcome<select value={decision} onChange={e => setDecision(e.target.value)}><option value="reviewed">Reviewed · observation only</option><option value="approved">Accepted for research review</option><option value="needs_followup">Needs more evidence / follow-up</option><option value="rejected">Inadequate image or artifact</option></select></label>
      <label>{labels.severity}<select value={severity} onChange={e => setSeverity(e.target.value)}><option value="unspecified">Unspecified / Research</option><option value="insufficient_evidence">Insufficient evidence</option><option value="none">None observed</option><option value="mild">Mild</option><option value="moderate">Moderate</option><option value="severe">Severe</option></select></label></div>
      <label>{labels.notes}<textarea rows={3} maxLength={1000} required={severity === 'insufficient_evidence'} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Record evidence, limitations and your assessment; no identifying patient details" /></label>
      <Button className="primary" disabled={busy}>{busy ? 'Saving…' : labels.submit}</Button>
    </form> : <p>Review permission and a saved analysis are required. Existing case reviews remain in case history.</p>}
    {error && <p role="alert" className="message error">{error}</p>}{message && <p role="status" className="message success">{message}</p>}
    <details className="assessment-history"><summary>Assessment history for this run ({linked.length})</summary>{linked.length ? linked.map(r => <div key={r.id}><strong>{r.decision.replaceAll('_', ' ')} · {r.stenosis_severity || 'Unspecified'}</strong><p>{r.notes || 'No notes'}</p><small>{r.reviewer_name || r.reviewer_id} · {r.reviewer_role} · {new Date(r.created_at).toLocaleString()} · {r.id}</small></div>) : <p className="caption">No assessment recorded for this run yet.</p>}</details>
    {!!caseRecord.reviews?.filter(r => !r.analysis_event_id).length && <p className="caption">{caseRecord.reviews.filter(r => !r.analysis_event_id).length} legacy case-only reviews are preserved, but are not attributed to this run.</p>}
  </section>;
}
