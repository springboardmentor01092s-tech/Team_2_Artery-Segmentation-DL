import { useState } from "react";
import type { CaseRecord } from "./caseTypes";
import { Card } from "./components/prismui/card";
import { Button } from "./components/prismui/button";
import { taskLabel } from "./caseConfiguration";

export default function ReviewQueue({ cases, onOpen }: { cases: CaseRecord[]; onOpen: (id: string) => void }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const assigned = cases.filter(c => c.permissions?.can_review);
  const filtered = assigned.filter(c => `${c.case_code} ${c.modality} ${c.anatomy}`.toLowerCase().includes(query.toLowerCase()) &&
    (status === "all" || (status === "pending" ? c.workflow_status === "pending_review" : c.latest_review?.decision === status)));
  return <div className="settings-page"><div className="page-heading"><div><p className="eyebrow">ASSIGNED RESEARCH REVIEW</p><h2>Severity Review</h2><p className="muted">Inspect the image and recorded evidence before entering a human assessment. No automated clinical grade or urgency is assigned.</p></div></div>
    <div className="case-section-nav"><label>Search review cases<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Case reference, modality or anatomy" /></label><label>Review state<select value={status} onChange={e => setStatus(e.target.value)}><option value="all">All review-authorized cases</option><option value="pending">Awaiting review</option><option value="approved">Accepted for research review</option><option value="needs_followup">Follow-up requested</option><option value="rejected">Rejected</option><option value="reviewed">Observation recorded</option></select></label></div>
    <p className="caption">{filtered.length} matching cases of {assigned.length} review-authorized cases. Pending means the recorded workflow is pending review, not a clinical priority.</p>
    {!filtered.length && <Card className="panel"><h3>No matching review cases</h3><p>Only owned cases or explicit review/edit assignments with clinical review permission appear. A read-only assignment does not permit a decision.</p></Card>}
    {filtered.map(c => <Card key={c.id} className="panel"><h3>{c.case_code}</h3><p>{c.modality} · {c.anatomy} · {taskLabel(c.intended_task)}</p><p>Workflow: {c.workflow_status.replaceAll("_", " ")} · Latest human assessment: {c.latest_review?.stenosis_severity || "Unspecified"}</p><p className="caption">{c.latest_review ? `Last review: ${new Date(c.latest_review.created_at).toLocaleString()}` : "No review recorded"}</p><Button type="button" onClick={() => onOpen(c.id)}>Open case review</Button></Card>)}
  </div>;
}
