import type { CaseRecord } from "./caseTypes";
import { useState } from "react";
import { Card } from "./components/prismui/card";
import { Button } from "./components/prismui/button";
import { FolderHeart, Stethoscope, ClipboardCheck, FileText, ArrowUpRight, ShieldCheck, Search } from "lucide-react";
import "./viewer-workspace.css";

export default function ViewerWorkspace({ cases, selected, onSelect, page, onCases, onSettings }: {
  cases: CaseRecord[]; selected?: CaseRecord; onSelect: (id: string) => void;
  page: "overview" | "cases"; onCases: () => void; onSettings: () => void;
}) {
  const [query, setQuery] = useState("");
  const matching = cases.filter(item => item.case_code.toLowerCase().includes(query.toLowerCase().trim()));
  const doctors = new Set(cases.flatMap(item => (item.assigned_doctors || []).map(doctor => doctor.id))).size;
  if (page === "overview") return <div className="viewer-portal">
    <header className="viewer-welcome"><p className="eyebrow">YOUR PERSONAL WORKSPACE</p><h1>A clearer view of your results.</h1><p>Your shared studies, recorded findings and assigned care team—together in one place.</p><Button type="button" onClick={onCases}>View assigned cases <ArrowUpRight size={17} aria-hidden="true" /></Button></header>
    <div className="viewer-summary" aria-label="Your workspace summary">
      {[{ icon: FolderHeart, label: "Assigned cases", value: cases.length }, { icon: ClipboardCheck, label: "Cases with a review", value: cases.filter(item => item.latest_review).length }, { icon: Stethoscope, label: "Assigned doctors", value: doctors }].map(({icon: Icon, label, value}) => <div key={label}><Icon size={21} aria-hidden="true" /><strong>{value}</strong><span>{label}</span></div>)}
    </div>
    <section className="viewer-start"><div><p className="eyebrow">WHAT’S NEXT</p><h2>{cases.length ? "Pick up with your latest study" : "Your workspace is ready"}</h2><p>{cases.length ? "Open an assigned case to see its recorded review and the doctor responsible for it." : "Once a doctor or case owner shares a study, you’ll find its details here. You don’t need to upload or run any models."}</p>{cases.length ? <Button type="button" variant="outline" onClick={onCases}>Open case details</Button> : <button type="button" className="viewer-text-link" onClick={onSettings}>Review your account details <ArrowUpRight size={16} aria-hidden="true" /></button>}</div><ol className="viewer-how"><li><span>01</span><div><strong>A case is shared</strong><p>A case owner or authorized administrator grants access.</p></div></li><li><span>02</span><div><strong>Your doctor reviews it</strong><p>Findings and review notes are recorded on the case.</p></div></li><li><span>03</span><div><strong>You explore the results</strong><p>Read the findings and see your assigned doctor.</p></div></li></ol></section>
    <p className="viewer-privacy"><ShieldCheck size={17} aria-hidden="true" /> Only cases shared with your account are visible. Research outputs are not a substitute for clinical advice.</p>
  </div>;
  return <div className="viewer-portal">
    <header className="viewer-cases-heading"><div><p className="eyebrow">SHARED WITH YOU</p><h1>Assigned cases</h1><p>Explore a study, read its recorded results and find your assigned doctor.</p></div><span className="viewer-readonly"><ShieldCheck size={16} aria-hidden="true" /> Read-only access</span></header>
    {!cases.length ? <section className="viewer-empty"><div className="viewer-empty-symbol"><FolderHeart size={42} strokeWidth={1.4} aria-hidden="true" /></div><h2>No cases shared yet</h2><p>You’re in the right place. Your cases will appear here after a case owner or authorized administrator grants access.</p><div className="viewer-empty-help"><Stethoscope size={20} aria-hidden="true" /><div><strong>Expecting a study?</strong><p>Ask your doctor or case administrator to confirm that it was shared with the account you’re signed in to.</p></div></div><Button type="button" variant="outline" onClick={onSettings}>Check account details</Button><small>No cases, reports or doctor assignments have been added to this account.</small></section> : <>
      <div className="viewer-case-search"><label htmlFor="viewer-case-search"><Search size={18} aria-hidden="true" /> Find a case</label><input id="viewer-case-search" placeholder="Search by case reference" value={query} onChange={event => setQuery(event.target.value)} /></div>
      <div className="viewer-case-list" aria-label="Assigned studies">{matching.map(item => <button type="button" key={item.id} aria-pressed={selected?.id === item.id} onClick={() => onSelect(item.id)}><FolderHeart size={20} aria-hidden="true" /><span><strong>{item.case_code}</strong><small>{item.modality} · {item.scan_date || "Scan date not recorded"}</small></span><span>{item.latest_review ? "Review recorded" : "Awaiting review"}</span></button>)}{!matching.length && <p>No cases match that reference.</p>}</div>
      {selected && <div className="settings-grid">
        <Card className="panel"><h3><FolderHeart size={20} aria-hidden="true" /> Case details</h3><dl><dt>Case reference</dt><dd>{selected.case_code}</dd><dt>Scan date</dt><dd>{selected.scan_date || "Not recorded"}</dd><dt>Image type</dt><dd>{selected.modality}</dd><dt>Area examined</dt><dd>{selected.anatomy || "Not recorded"}</dd><dt>Case status</dt><dd>{selected.workflow_status?.replaceAll("_", " ") || selected.status}</dd></dl></Card>
        <Card className="panel"><h3><Stethoscope size={20} aria-hidden="true" /> Assigned doctor</h3>{selected.assigned_doctors?.length ? selected.assigned_doctors.map(doctor => <div key={doctor.id}><strong>{doctor.name}</strong><p className="muted">{doctor.role === "doctor" ? "Doctor" : "Clinical reviewer"}</p></div>) : <p className="muted">No reviewing doctor is currently assigned. Ask the case owner or administrator to assign one.</p>}</Card>
        <Card className="panel"><h3><ClipboardCheck size={20} aria-hidden="true" /> Recorded clinical results</h3>{selected.latest_review ? <><p><strong>Review status:</strong> {selected.latest_review.decision.replaceAll("_", " ")}</p><p><strong>Doctor-assessed severity:</strong> {selected.latest_review.stenosis_severity || "Not specified"}</p><p style={{ whiteSpace: "pre-wrap" }}>{selected.latest_review.notes || "No review notes recorded."}</p><p className="muted">Reviewed by {selected.latest_review.reviewer_name || "a clinical reviewer"} · {new Date(selected.latest_review.created_at).toLocaleString()}</p></> : <p className="muted">Your doctor has not recorded a review yet. No clinical conclusion is available.</p>}<small>These are recorded review findings, not a new diagnosis. Discuss their meaning with your assigned doctor.</small></Card>
        <Card className="panel"><h3><FileText size={20} aria-hidden="true" /> Report status</h3><p>{selected.report_status?.replaceAll("_", " ") || "No report available"}</p><p className="muted">{selected.report_status === "approved" ? "An approved report is recorded for this case. Contact your doctor for guidance on the findings." : "A final approved report is not yet available."}</p></Card>
      </div>}
    </>}
  </div>;
}
