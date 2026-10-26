import { FormEvent, useEffect, useRef, useState } from "react";
import { request } from "./api";
import type { CaseRecord } from "./caseTypes";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";
import { Input } from "./components/prismui/input";
import { Stethoscope, CheckCircle2, AlertCircle, FileDown, ShieldAlert } from "lucide-react";
import { taskLabel } from "./caseConfiguration";
import { reviewLabels } from "./reviewLabels";

const histories = ["hypertension", "diabetes", "prior_mi", "prior_pci", "hyperlipidemia", "none", "unknown"];
const risks = ["smoking", "family_history", "obesity", "sedentary", "hypertension", "diabetes", "none", "unknown"];
const display = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function CaseDetails({
  caseRecord, token, modelVersion, userRole, currentUserId, onSaved, section = "overview",
}: {
  caseRecord: CaseRecord;
  token: string;
  modelVersion?: string;
  userRole?: string;
  currentUserId?: string;
  onSaved: (updated: CaseRecord) => void;
  section?: string;
}) {
  const [patientCode, setPatientCode] = useState("");
  const [ageBand, setAgeBand] = useState("unknown");
  const [gender, setGender] = useState("unknown");
  const [medicalHistory, setMedicalHistory] = useState<string[]>([]);
  const [riskFactors, setRiskFactors] = useState<string[]>([]);
  const [clinicalNotes, setClinicalNotes] = useState("");
  const [scanDate, setScanDate] = useState("");
  const [modality, setModality] = useState("XCA");
  const [clinicalEnabled, setClinicalEnabled] = useState(false);
  const [sourceDataset, setSourceDataset] = useState("");
  const [sourceReference, setSourceReference] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Clinical Review state (for doctors)
  const [decision, setDecision] = useState<"approved" | "needs_followup" | "rejected" | "reviewed">("approved");
  const [stenosisSeverity, setStenosisSeverity] = useState("unspecified");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewMessage, setReviewMessage] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [exportBusy, setExportBusy] = useState(false);
  const [assignee, setAssignee] = useState("");
  const [accessLevel, setAccessLevel] = useState<"read" | "review" | "edit">("read");
  const [assignmentBusy, setAssignmentBusy] = useState(false);
  const [assignmentMessage, setAssignmentMessage] = useState("");
  const [assignmentError, setAssignmentError] = useState("");
  const [formDirty, setFormDirty] = useState(false);
  const [remoteUpdatePending, setRemoteUpdatePending] = useState(false);
  const lastCaseId = useRef(caseRecord.id);
  const lastSyncedFields = useRef("");
  const caseFields = JSON.stringify([
    caseRecord.patient_code, caseRecord.age_band, caseRecord.gender,
    caseRecord.medical_history, caseRecord.risk_factors, caseRecord.clinical_notes,
    caseRecord.scan_date, caseRecord.modality, caseRecord.clinical_metadata_enabled,
    caseRecord.source_dataset, caseRecord.source_reference,
  ]);

  const isDoctor = userRole === "doctor" || userRole === "clinician" || userRole === "admin";
  const labels = reviewLabels(userRole);
  const isViewer = userRole === "viewer";
  const isReadOnly = isViewer || caseRecord.permissions?.can_edit === false;
  const canExport = caseRecord.permissions?.can_export ?? (userRole === "doctor" || userRole === "clinician" || userRole === "researcher");
  const canAssign = caseRecord.permissions?.can_assign ?? (userRole === "admin" || !!currentUserId && caseRecord.owner_id === currentUserId);

  useEffect(() => {
    const switchedCase = lastCaseId.current !== caseRecord.id;
    if (switchedCase) {
      lastCaseId.current = caseRecord.id;
      setFormDirty(false);
    }
    if (!switchedCase && formDirty) {
      if (caseFields !== lastSyncedFields.current) setRemoteUpdatePending(true);
      return;
    }
    setPatientCode(caseRecord.patient_code || "");
    setAgeBand(caseRecord.age_band || "unknown");
    setGender(caseRecord.gender || "unknown");
    setMedicalHistory(caseRecord.medical_history || []);
    setRiskFactors(caseRecord.risk_factors || []);
    setClinicalNotes(caseRecord.clinical_notes || "");
    setScanDate(caseRecord.scan_date || "");
    setModality(caseRecord.modality);
    setClinicalEnabled(caseRecord.clinical_metadata_enabled ?? false);
    setSourceDataset(caseRecord.source_dataset || "");
    setSourceReference(caseRecord.source_reference || "");
    setError("");
    setMessage("");
    setReviewError("");
    setReviewMessage("");
    setRemoteUpdatePending(false);
    lastSyncedFields.current = caseFields;
  }, [caseRecord.id, caseFields, formDirty]);

  function toggle(values: string[], setValues: (items: string[]) => void, item: string) {
    if (isReadOnly) return;
    if (values.includes(item)) { setValues(values.filter((value) => value !== item)); return; }
    if (item === "none" || item === "unknown") { setValues([item]); return; }
    setValues([...values.filter((value) => value !== "none" && value !== "unknown"), item]);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (isReadOnly || remoteUpdatePending) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const updated = await request<CaseRecord>(`/api/cases/${caseRecord.id}`, token, {
        patient_code: patientCode.trim() || null, age_band: ageBand, gender,
        ...(clinicalEnabled ? { medical_history: medicalHistory, risk_factors: riskFactors,
          clinical_notes: clinicalNotes.trim() || null } : {}),
        clinical_metadata_enabled: clinicalEnabled, source_dataset: sourceDataset.trim() || null,
        source_reference: sourceReference.trim() || null, scan_date: scanDate || null, modality,
      }, "PATCH");
      onSaved(updated);
      setFormDirty(false);
      setMessage("Case details saved.");
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }

  async function submitClinicalReview(event: FormEvent) {
    event.preventDefault();
    setReviewBusy(true);
    setReviewError("");
    setReviewMessage("");
    try {
      const updated = await request<CaseRecord>(`/api/cases/${caseRecord.id}/review`, token, {
        decision,
        stenosis_severity: stenosisSeverity,
        notes: reviewNotes.trim() || null,
      }, "POST");
      onSaved(updated);
      setReviewMessage(`Clinical decision '${decision}' recorded successfully.`);
    } catch (cause) {
      setReviewError((cause as Error).message);
    } finally {
      setReviewBusy(false);
    }
  }

  async function handleExport() {
    setExportBusy(true);
    try {
      const data = await request<{ export_metadata: object; case: CaseRecord }>(`/api/cases/${caseRecord.id}/export`, token);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `case_${caseRecord.case_code}_report.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setExportBusy(false);
    }
  }

  async function assignCase(event: FormEvent) {
    event.preventDefault();
    if (!canAssign || !assignee.trim()) return;
    setAssignmentBusy(true); setAssignmentMessage(""); setAssignmentError("");
    try {
      const result = await request<{ detail: string }>(`/api/cases/${caseRecord.id}/access`, token,
        { user_email_or_id: assignee.trim(), access_level: accessLevel }, "POST");
      setAssignmentMessage(result.detail);
      setAssignee("");
    } catch (cause) { setAssignmentError((cause as Error).message); }
    finally { setAssignmentBusy(false); }
  }

  return (
    <>
      {section === "overview" && <><Card className="panel case-details">
        <div className="viewer-heading">
          <h3>Case details</h3>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            {canExport && (
              <Button variant="outline" type="button" onClick={handleExport} disabled={exportBusy} style={{ padding: "0.3rem 0.6rem", fontSize: "0.78rem", height: "auto" }}>
                <FileDown size={14} style={{ marginRight: "4px" }} />
                {exportBusy ? "Exporting…" : "Export Report"}
              </Button>
            )}
            <span>{caseRecord.status}</span>
          </div>
        </div>
        <p className="caption">Case code: {caseRecord.case_code} · Anatomy: {caseRecord.anatomy} · Tasks: {(caseRecord.intended_tasks || [caseRecord.intended_task]).map(taskLabel).join(", ")} · Model: {modelVersion || "No analysis yet"}</p>
        <p className="privacy-note">Use only public or de-identified studies. Patient ID must be a pseudonym; do not enter names, contact details, or dates of birth.</p>
        
        {isReadOnly && (
          <div style={{ background: "#f4f4f5", padding: "0.6rem 0.8rem", borderRadius: "8px", margin: "0.8rem 0", fontSize: "0.84rem", color: "#52525b" }}>
            <strong>Read-only case access:</strong> You can inspect study parameters but cannot modify clinical metadata.
          </div>
        )}

        <form onSubmit={save} onChangeCapture={() => setFormDirty(true)} className="case-details-form">
          {remoteUpdatePending && <p className="message error" role="status">This case changed in another session while you were editing. <button type="button" onClick={() => setFormDirty(false)}>Discard my edits and load the latest details</button></p>}
          <div className="case-form-grid">
            <label>Patient ID (pseudonym)<Input value={patientCode} onChange={(event) => setPatientCode(event.target.value)} pattern="[A-Za-z0-9_-]{3,40}" maxLength={40} placeholder="e.g. ARCADE-001" disabled={isReadOnly} /></label>
            <label>Age band<select value={ageBand} onChange={(event) => setAgeBand(event.target.value)} disabled={isReadOnly}>{["unknown", "under_30", "30_39", "40_49", "50_59", "60_69", "70_79", "80_plus"].map((value) => <option key={value} value={value}>{display(value)}</option>)}</select></label>
            <label>Gender<select value={gender} onChange={(event) => setGender(event.target.value)} disabled={isReadOnly}>{["unknown", "female", "male", "other"].map((value) => <option key={value} value={value}>{display(value)}</option>)}</select></label>
            <label>Imaging modality<select value={modality} onChange={(event) => setModality(event.target.value)} disabled={isReadOnly || caseRecord.images.length > 0}>{["XCA", "CTA", "CT", "MRA"].map(v => <option key={v}>{v}</option>)}</select></label>
            <label>Source dataset or release<Input value={sourceDataset} maxLength={120} onChange={e => setSourceDataset(e.target.value)} disabled={isReadOnly} /></label>
            <label>Source case or study reference<Input value={sourceReference} maxLength={200} onChange={e => setSourceReference(e.target.value)} disabled={isReadOnly} /></label>
            <label>Scan date, if de-identified<Input type="date" value={scanDate} onChange={(event) => setScanDate(event.target.value)} disabled={isReadOnly} /></label>
          </div>
          <label className="clinical-metadata-toggle"><input type="checkbox" checked={clinicalEnabled} disabled={isReadOnly} onChange={e => setClinicalEnabled(e.target.checked)} />Enable optional de-identified clinical context for a permitted research purpose</label>
          <p className="caption">Disabled by default for demonstrations. Enabling this does not verify consent or de-identification. Existing recorded context is retained when disabled.</p>
          <fieldset disabled={!clinicalEnabled || isReadOnly}>
          <legend>Optional restricted clinical context</legend>
          <fieldset><legend>Medical history</legend><div className="case-options">{histories.map((item) => <label key={item}><input type="checkbox" checked={medicalHistory.includes(item)} onChange={() => toggle(medicalHistory, setMedicalHistory, item)} disabled={isReadOnly} />{display(item)}</label>)}</div></fieldset>
          <fieldset><legend>Risk factors</legend><div className="case-options">{risks.map((item) => <label key={item}><input type="checkbox" checked={riskFactors.includes(item)} onChange={() => toggle(riskFactors, setRiskFactors, item)} disabled={isReadOnly} />{display(item)}</label>)}</div></fieldset>
          <label>De-identified clinical notes<textarea value={clinicalNotes} onChange={(event) => setClinicalNotes(event.target.value)} maxLength={500} rows={3} placeholder="Optional observations without personal identifiers" disabled={isReadOnly} /></label>
          </fieldset>
          {error && <p className="message error" role="alert">{error}</p>}
          {message && <p className="message success" role="status">{message}</p>}
          {!isReadOnly && <Button className="primary" disabled={busy || remoteUpdatePending}>{busy ? "Saving…" : "Save case details"}</Button>}
        </form>
      </Card>

      {canAssign && <Card className="panel case-assignment"><h3>Assign case access</h3><p className="muted">Share this de-identified case with an existing user. Their role must also permit the requested action.</p><form onSubmit={assignCase} className="case-assignment-form"><label>User email or ID<Input value={assignee} onChange={(event) => setAssignee(event.target.value)} placeholder="reviewer@example.org" required /></label><label>Access level<select value={accessLevel} onChange={(event) => setAccessLevel(event.target.value as typeof accessLevel)}><option value="read">Read</option><option value="review">Review</option><option value="edit">Edit and upload</option></select></label><Button className="primary" disabled={assignmentBusy}>{assignmentBusy ? "Assigning…" : "Assign access"}</Button></form>{assignmentMessage && <p className="message success" role="status">{assignmentMessage}</p>}{assignmentError && <p className="message error" role="alert">{assignmentError}</p>}</Card>}</>}

      {/* Clinical Review & Approval Section */}
      {section === "reviews" && <Card className="panel clinical-review-panel">
        <div className="viewer-heading">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Stethoscope size={20} color="#0284c7" />
            <h3 style={{ margin: 0 }}>{labels.title}</h3>
          </div>
          {caseRecord.latest_review ? (
            <span style={{
              background: caseRecord.latest_review.decision === "approved" ? "#ecfdf5" : caseRecord.latest_review.decision === "rejected" ? "#fef2f2" : "#fef9c3",
              color: caseRecord.latest_review.decision === "approved" ? "#047857" : caseRecord.latest_review.decision === "rejected" ? "#b91c1c" : "#854d0e",
              fontWeight: 700, padding: "0.2rem 0.6rem", borderRadius: "100px", fontSize: "0.78rem",
            }}>
              {caseRecord.latest_review.decision.toUpperCase()}
            </span>
          ) : (
            <span style={{ color: "#71717a", fontSize: "0.82rem" }}>Pending Review</span>
          )}
        </div>

        {caseRecord.latest_review && (
          <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "0.85rem", borderRadius: "10px", margin: "0.8rem 0" }}>
            <p style={{ margin: "0 0 0.4rem 0", fontSize: "0.88rem" }}>
              <strong>Decision:</strong> {display(caseRecord.latest_review.decision)} · <strong>Assessed Severity:</strong> {display(caseRecord.latest_review.stenosis_severity || "unspecified")}
            </p>
            {caseRecord.latest_review.notes && (
              <p style={{ margin: "0 0 0.4rem 0", fontSize: "0.84rem", color: "#334155" }}>
                <em>"{caseRecord.latest_review.notes}"</em>
              </p>
            )}
            <small style={{ color: "#64748b" }}>
              Reviewed by {caseRecord.latest_review.reviewer_name || "Clinical reviewer"} on {new Date(caseRecord.latest_review.created_at).toLocaleString()}
            </small>
          </div>
        )}

        {isDoctor && caseRecord.permissions?.can_review ? (
          <form onSubmit={submitClinicalReview} className="case-details-form clinical-review-form">
            <div className="case-form-grid">
              <label>
              {labels.decision}
                <select value={decision} onChange={(e) => setDecision(e.target.value as any)}>
                  <option value="approved">Accepted for research review</option>
                  <option value="needs_followup">Needs Clinical Follow-up</option>
                  <option value="rejected">Rejected — Artifact or scan inadequate</option>
                  <option value="reviewed">Reviewed — Observation only</option>
                </select>
              </label>

              <label>
                {labels.severity}
                <select value={stenosisSeverity} onChange={(e) => setStenosisSeverity(e.target.value)}>
                  <option value="unspecified">Unspecified / Research</option>
                  <option value="none">None observed</option>
                  <option value="mild">Mild</option>
                  <option value="moderate">Moderate</option>
                  <option value="severe">Severe</option>
                </select>
              </label>
            </div>

            <label>
              {labels.notes}
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                maxLength={1000}
                rows={4}
                placeholder="Record de-identified review observations, limitations or required corrections"
              />
            </label>

            {reviewError && <p className="message error" role="alert">{reviewError}</p>}
            {reviewMessage && <p className="message success" role="status">{reviewMessage}</p>}

            <Button className="primary" disabled={reviewBusy} style={{ marginTop: "0.8rem" }}>
              {reviewBusy ? "Submitting…" : labels.submit}
            </Button>
          </form>
        ) : (
          !caseRecord.latest_review && (
            <p style={{ fontSize: "0.84rem", color: "#71717a", marginTop: "0.5rem" }}>
              Clinical review requires a <strong>Doctor or Clinician</strong> role and review access to this case.
            </p>
          )
        )}
        <p className="caption">A review is not clinical validation or a standalone diagnosis. Earlier decisions remain in case history.</p>
        {(caseRecord.reviews || []).length > 0 && <details><summary>Recorded review history ({caseRecord.reviews?.length})</summary>{caseRecord.reviews?.map(review => <p key={review.id}><strong>{display(review.decision)}</strong> · {review.reviewer_name || "Assigned reviewer"} · {new Date(review.created_at).toLocaleString()}<br />{review.notes || "No notes recorded"}</p>)}</details>}
      </Card>}
    </>
  );
}
