import { useEffect, useState, type FormEvent } from "react";
import { KeyRound } from "lucide-react";
import { request } from "./api";
import { Card } from "./components/prismui/card";
import { Button } from "./components/prismui/button";

type AccessRequest = { id: string; email: string; requested_role: string; reason: string; status: string; decision_notes: string | null };
export default function AccessRequests({ token, admin = false }: { token: string; admin?: boolean }) {
  const [items, setItems] = useState<AccessRequest[]>([]);
  const [role, setRole] = useState("researcher");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const path = admin ? "/api/admin/access-requests" : "/api/auth/access-requests";
  async function refresh() { setItems(await request<AccessRequest[]>(path, token)); }
  useEffect(() => { refresh().catch((cause: Error) => setError(cause.message)); }, [token, admin]);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      await request(path, token, { requested_role: role, reason }, "POST");
      setReason(""); await refresh(); setMessage("Access request submitted. Your permissions have not changed.");
    } catch (cause) { setError((cause as Error).message); } finally { setBusy(false); }
  }
  async function decide(item: AccessRequest, decision: "approved" | "rejected") {
    setBusy(true); setError(""); setMessage("");
    try {
      await request(`${path}/${item.id}/decision`, token, { decision, notes: notes[item.id] || "" }, "POST");
      await refresh(); setMessage(`Request ${decision}. The decision was audited.`);
    } catch (cause) { setError((cause as Error).message); } finally { setBusy(false); }
  }
  return <Card className="panel access-request-panel"><h3><KeyRound size={20} aria-hidden="true" /> {admin ? "Access requests & approvals" : "Request workspace access"}</h3>
    <p className="muted">{admin ? "Verify eligibility outside the app before approving. Record the verification performed; clinical report approval and case assignments are separate grants. Do not request or paste sensitive documents here." : "Request research, clinical review or ML access. Explain your institutional authorization without including patient details or sensitive credential documents. An administrator must verify eligibility."}</p>
    {error && <p role="alert" className="message error">{error}</p>}{message && <p role="status">{message}</p>}
    {!admin && !items.some(item => item.status === "pending") && <form className="aligned-settings-form" onSubmit={submit}>
      <label htmlFor="requested-role">Requested workspace</label><select id="requested-role" value={role} onChange={event => setRole(event.target.value)}><option value="researcher">Researcher</option><option value="clinician">Doctor</option><option value="ml_engineer">ML Engineer</option></select>
      <label htmlFor="access-reason">Purpose and eligibility</label><textarea id="access-reason" required minLength={20} maxLength={2000} rows={5} placeholder="Describe your workspace needs and institutional authorization. Do not include patient details." value={reason} onChange={event => setReason(event.target.value)} />
      <Button type="submit" disabled={busy}>Submit access request</Button>
    </form>}
    {!items.length && <p className="muted">No access requests yet.</p>}
    {items.map(item => <div className="access-request-item" key={item.id}><strong>{item.requested_role.replaceAll("_", " ")} · {item.status}</strong>{admin && <p>{item.email}</p>}<p style={{ whiteSpace: "pre-wrap" }}>{item.reason}</p>{item.decision_notes && <p>Decision: {item.decision_notes}</p>}
      {admin && item.status === "pending" && <><label htmlFor={`decision-${item.id}`}>Verification performed / rejection reason (at least 20 characters)</label><textarea id={`decision-${item.id}`} minLength={20} maxLength={2000} value={notes[item.id] || ""} onChange={event => setNotes(previous => ({ ...previous, [item.id]: event.target.value }))} /><div className="connected-actions"><Button type="button" disabled={busy || (notes[item.id] || "").trim().length < 20} onClick={() => decide(item, "approved")}>Approve verified access</Button><Button type="button" variant="outline" disabled={busy || (notes[item.id] || "").trim().length < 20} onClick={() => decide(item, "rejected")}>Reject request</Button></div></>}
    </div>)}
  </Card>;
}
