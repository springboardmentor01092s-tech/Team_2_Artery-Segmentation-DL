import { useState, type FormEvent } from "react";
import type { User } from "./AccountPanel";
import { request } from "./api";
import { Card } from "./components/prismui/card";
import { Button } from "./components/prismui/button";
import { KeyRound } from "lucide-react";

export default function OperationalGrants({ users, token, actorId, onChanged }: { users: User[]; token: string; actorId: string; onChanged: () => Promise<void> }) {
  const [userId, setUserId] = useState("");
  const [permission, setPermission] = useState("analysis:run");
  const [enabled, setEnabled] = useState(true);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const target = users.find(user => user.id === userId);
  const options = target?.role === "admin" ? ["case:create", "case:upload", "analysis:run", "analysis:export"] : ["analysis:run"];
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      await request(`/api/admin/users/${userId}/operational-grant`, token, { permission, enabled, reason }, "POST");
      await onChanged(); setMessage("Operational access updated and audited. Case assignments are still required.");
    } catch (cause) { setError((cause as Error).message); } finally { setBusy(false); }
  }
  return <Card className="panel"><h3><KeyRound size={20} aria-hidden="true" /> Separate operational grants</h3><p className="muted">Technicians need a separate grant to run AI analysis. Administrators need separate grants for case creation, uploads, analysis and export. These grants never grant clinical sign-off or bypass case assignment. You cannot authorize your own account.</p>
    {error && <p className="message error" role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    <form className="aligned-settings-form" onSubmit={save}><label htmlFor="grant-user">Account</label><select id="grant-user" required value={userId} onChange={event => { setUserId(event.target.value); setPermission("analysis:run"); }}><option value="">Select another account</option>{users.filter(user => user.id !== actorId && ["admin", "technician"].includes(user.role)).map(user => <option key={user.id} value={user.id}>{user.display_name || user.email} · {user.role}</option>)}</select>
      <label htmlFor="grant-action">Action</label><select id="grant-action" value={permission} onChange={event => setPermission(event.target.value)}>{options.map(action => <option key={action} value={action}>{action}</option>)}</select>
      {target && <p className="muted">Effective access: {target.permissions?.includes(permission) ? "Allowed" : "Not granted"}</p>}
      <label htmlFor="grant-decision">Decision</label><select id="grant-decision" value={enabled ? "allow" : "revoke"} onChange={event => setEnabled(event.target.value === "allow")}><option value="allow">Grant action</option><option value="revoke">Revoke action</option></select>
      <label htmlFor="grant-reason">Authorization reason (no patient identifiers)</label><textarea id="grant-reason" required minLength={20} maxLength={1000} value={reason} onChange={event => setReason(event.target.value)} />
      <Button type="submit" disabled={busy || !userId}>{busy ? "Saving…" : "Save audited decision"}</Button>
    </form></Card>;
}
