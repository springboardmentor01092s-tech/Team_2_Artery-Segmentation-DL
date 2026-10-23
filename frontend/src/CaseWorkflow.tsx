import { useState, type FormEvent, type ReactNode } from "react";
import { ClipboardCheck, ClipboardList, Eye, FileCheck2, History, Microscope, Send, ShieldCheck, Stethoscope, Trash2 } from "lucide-react";
import { request } from "./api";
import type { CaseRecord } from "./caseTypes";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";
import { InlineDisclosureMenu } from "./components/watermelon/inline-disclosure-menu";

const label = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function CaseWorkflow({ caseRecord, token, role, onUpdated, onDeleted, children, onNext }: {
  caseRecord: CaseRecord;
  token: string;
  role: string;
  onUpdated: (record: CaseRecord) => void;
  onDeleted: (id: string) => void;
  children?: ReactNode;
  onNext?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [comment, setComment] = useState("");
  const [category, setCategory] = useState<"general" | "quality" | "model" | "review">("general");
  const [decisionNotes, setDecisionNotes] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteCode, setDeleteCode] = useState("");
  const canSubmit = !!caseRecord.permissions?.can_submit_report && caseRecord.workflow_status === "reviewed";
  const canApprove = !!caseRecord.permissions?.can_approve_report && caseRecord.report_status === "pending_approval";
  const canDelete = !!caseRecord.permissions?.can_delete;

  async function refresh() {
    onUpdated(await request<CaseRecord>(`/api/cases/${caseRecord.id}`, token));
  }

  async function act(path: string, body?: object, method = "POST", success = "Case updated.") {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await request(path, token, body, method);
      await refresh();
      setNotice(success);
      return true;
    } catch (cause) { setError((cause as Error).message); return false; }
    finally { setBusy(false); }
  }

  async function addComment(event: FormEvent) {
    event.preventDefault();
    if (!comment.trim()) return;
    if (await act(`/api/cases/${caseRecord.id}/comments`, { body: comment.trim(), category }, "POST", "Note shared with the case team.")) setComment("");
  }

  async function deleteCase(event: FormEvent) {
    event.preventDefault();
    if (!canDelete || deleteCode !== caseRecord.case_code) return;
    setBusy(true);
    setError("");
    try {
      await request(`/api/cases/${caseRecord.id}`, token, undefined, "DELETE");
      onDeleted(caseRecord.id);
    } catch (cause) { setError((cause as Error).message); setBusy(false); }
  }

  async function copyCaseCode() {
    try {
      await navigator.clipboard.writeText(caseRecord.case_code);
      setNotice("Case ID copied to your clipboard.");
    } catch {
      setError("Unable to copy the case ID. Select and copy it manually.");
    }
  }

  function openReportHistory() {
    document.getElementById("report-history")?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  const caseActions = [
    { icon: <ClipboardCheck size={20} aria-hidden="true" />, label: "Copy case ID", onClick: copyCaseCode },
    ...(caseRecord.report_revisions?.length ? [{ icon: <History size={20} aria-hidden="true" />, label: "View report history", onClick: openReportHistory }] : []),
    ...(canSubmit ? [{ icon: <Send size={20} aria-hidden="true" />, label: "Submit report for approval", onClick: () => act(`/api/cases/${caseRecord.id}/reports/submit`, {}, "POST", "Report submitted for approval.") }] : []),
  ];

  return <section className="case-workflow" aria-labelledby="case-workflow-title">
    <Card className="panel">
      <div className="viewer-heading"><div><p className="eyebrow">SHARED CASE LIFECYCLE</p><h3 id="case-workflow-title">Workflow & handoffs</h3></div><div className="case-workflow-actions"><span className="stage-badge">{label(caseRecord.workflow_status || "draft")}</span><InlineDisclosureMenu menuItems={caseActions} showDelete={false} menuLabel="Case actions" triggerLabel={`Open actions for ${caseRecord.case_code}`} /></div></div>
      <div className="workflow-role-icons" aria-label="Participating roles">
        <span><ShieldCheck aria-hidden="true" /> Administrator</span>
        <span><ClipboardList aria-hidden="true" /> Technician</span>
        <span><Microscope aria-hidden="true" /> Researcher</span>
        <span><Stethoscope aria-hidden="true" /> Doctor</span>
        <span><Eye aria-hidden="true" /> Viewer</span>
      </div>
      <div className="workflow-states">
        <div><small>Case stage</small><strong>{label(caseRecord.workflow_status || "draft")}</strong></div>
        <div><small>Image processing</small><strong>{label(caseRecord.processing_status || "not_started")}</strong></div>
        <div><small>Report</small><strong>{label(caseRecord.report_status || "draft")}{caseRecord.report_version ? ` · v${caseRecord.report_version}` : ""}</strong></div>
      </div>
      {caseRecord.workflow_status === "validation_failed" && <p className="message error">The latest image failed validation. Correct the file or metadata and upload it again.</p>}
      {caseRecord.workflow_status === "pending_review" && <p className="muted">AI results are ready for an authorized doctor. They are research findings until reviewed.</p>}
      {caseRecord.workflow_status === "changes_requested" && <p className="muted">Changes were requested. Review the notes below, correct the study or rerun analysis, then request another clinical review.</p>}
      {caseRecord.report_status === "approved" && <p className="message success"><FileCheck2 size={17} aria-hidden="true" /> Report v{caseRecord.report_version} approved{caseRecord.report_approved_at ? ` on ${new Date(caseRecord.report_approved_at).toLocaleString()}` : ""}.</p>}
      {canSubmit && <Button type="button" className="primary" disabled={busy} onClick={() => act(`/api/cases/${caseRecord.id}/reports/submit`, {}, "POST", "Report submitted for approval.")}>Submit reviewed report for approval</Button>}
      {canApprove && <div className="workflow-approval">
        <label>Approval notes (optional)<textarea value={decisionNotes} onChange={(event) => setDecisionNotes(event.target.value)} maxLength={1000} rows={2} placeholder="Reason for approval or requested changes" /></label>
        <div><Button type="button" className="primary" disabled={busy} onClick={() => act(`/api/cases/${caseRecord.id}/reports/${caseRecord.report_version}/decision`, { decision: "approved", notes: decisionNotes }, "POST", "Report approved.")}>Approve report v{caseRecord.report_version}</Button>
        <Button type="button" variant="outline" disabled={busy} onClick={() => act(`/api/cases/${caseRecord.id}/reports/${caseRecord.report_version}/decision`, { decision: "changes_requested", notes: decisionNotes }, "POST", "Report returned for changes.")}>Request changes</Button></div>
      </div>}
      {caseRecord.report_revisions?.length ? <div className="workflow-history" id="report-history"><strong>Report history</strong>{caseRecord.report_revisions.map((item) => <span key={item.id}>v{item.version} · {label(item.status)} · {new Date(item.created_at).toLocaleString()}</span>)}</div> : null}
    </Card>
    <Card className="panel">
      <h3>Case notes</h3>
      <p className="muted">Share a quality, model, or review note with users assigned to this case.</p>
      {role !== "viewer" && <form className="workflow-comment-form" onSubmit={addComment}><select aria-label="Note category" value={category} onChange={(event) => setCategory(event.target.value as typeof category)}><option value="general">General</option><option value="quality">Image quality</option><option value="model">Model finding</option><option value="review">Clinical review</option></select><textarea aria-label="Case note" value={comment} onChange={(event) => setComment(event.target.value)} maxLength={1000} rows={2} placeholder="Add a de-identified note" required /><Button type="submit" disabled={busy || !comment.trim()}>Post note</Button></form>}
      <div className="workflow-comments">{caseRecord.comments?.length ? caseRecord.comments.map((item) => <div key={item.id}><strong>{label(item.category)} · {new Date(item.created_at).toLocaleString()}</strong><p>{item.body}</p></div>) : <p className="muted">No notes yet.</p>}</div>
    </Card>
    {children && <div className="case-overview-details">{children}</div>}
    {canDelete && <Card className="panel workflow-danger"><div className="viewer-heading"><div><p className="eyebrow">CASE MANAGEMENT</p><h3>Delete case</h3></div><Trash2 size={19} aria-hidden="true" /></div><p className="muted">Remove this case from active workspaces. An administrator can restore it from Trash; images and audit history are retained.</p>{!deleting ? <Button type="button" variant="outline" onClick={() => setDeleting(true)}>Delete case…</Button> : <form onSubmit={deleteCase}><label>Type <strong>{caseRecord.case_code}</strong> to confirm<input value={deleteCode} onChange={(event) => setDeleteCode(event.target.value)} autoComplete="off" /></label><div><Button type="submit" disabled={busy || deleteCode !== caseRecord.case_code}>Move case to Trash</Button><Button type="button" variant="outline" onClick={() => { setDeleting(false); setDeleteCode(""); }}>Cancel</Button></div></form>}</Card>}
    {onNext && <div className="case-bottom-navigation"><Button type="button" className="primary" onClick={onNext}>Next: Assets &amp; preparation →</Button></div>}
    {error && <p className="message error" role="alert">{error}</p>}
    {notice && <p className="message success" role="status">{notice}</p>}
  </section>;
}
