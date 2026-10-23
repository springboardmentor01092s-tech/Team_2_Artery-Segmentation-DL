import { useEffect, useState } from "react";
import { request } from "./api";
import type { User } from "./AccountPanel";
import { Card } from "./components/prismui/card";
import { ShieldCheck, UserCheck, Stethoscope, FlaskConical, Wrench, Eye, Cpu } from "lucide-react";
import AccessRequests from "./AccessRequests";
import OperationalGrants from "./OperationalGrants";
import PermissionMatrix from "./PermissionMatrix";

type Audit = { id: string; user_id: string; action: string; case_id: string | null; created_at: string };
type TrashedCase = { id: string; case_code: string; deleted_at: string };

const ROLE_OPTIONS = [
  { value: "admin", label: "System Administrator", icon: ShieldCheck, desc: "Full user management, audit logs, system & model governance" },
  { value: "doctor", label: "Doctor", icon: Stethoscope, desc: "Case review, stenosis examination, clinical review decisions" },
  { value: "researcher", label: "Medical Researcher", icon: FlaskConical, desc: "De-identified cases, model evaluation, research exports" },
  { value: "ml_engineer", label: "ML Engineer", icon: Cpu, desc: "Model status and validation without case access or activation rights" },
  { value: "technician", label: "Technician / Data Operator", icon: Wrench, desc: "Case creation, DICOM/raster uploads, image quality verification" },
  { value: "viewer", label: "Standard User / Viewer", icon: Eye, desc: "Read-only assigned case details, recorded results and assigned doctors" },
] as const;

const STATUS_OPTIONS = [
  { value: "active", label: "Active" },
  { value: "suspended", label: "Suspended" },
  { value: "pending", label: "Pending Approval" },
  { value: "deactivated", label: "Deactivated" },
] as const;

export default function AdminPanel({ token, currentUser, section = "users" }: { token: string; currentUser: User; section?: "users" | "permissions" | "access" | "audit" }) {
  const [users, setUsers] = useState<User[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [trash, setTrash] = useState<TrashedCase[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busyId, setBusyId] = useState("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [auditFilter, setAuditFilter] = useState("");
  const [showAllAudit, setShowAllAudit] = useState(false);
  const titles = { users: "User Management", permissions: "Roles & Permissions", access: "Workspace & Case Access", audit: "Audit Logs" };

  async function refresh() {
    const [nextUsers, nextAudit, nextTrash] = await Promise.all([
      section === "users" || section === "permissions" ? request<User[]>("/api/admin/users", token) : Promise.resolve([]),
      section === "audit" ? request<Audit[]>("/api/admin/audit", token) : Promise.resolve([]),
      section === "access" ? request<TrashedCase[]>("/api/admin/trash", token) : Promise.resolve([]),
    ]);
    setUsers(nextUsers);
    setAudit(nextAudit);
    setTrash(nextTrash);
    setLoading(false);
  }

  useEffect(() => {
    setLoading(true);
    refresh().catch((cause: Error) => { setError(cause.message); setLoading(false); });
  }, [token, section]);

  async function changeRole(userId: string, role: string) {
    setError("");
    setMessage("");
    setBusyId(userId);
    try {
      await request(`/api/admin/users/${userId}/role`, token, { role }, "POST");
      await refresh();
      setMessage("Role updated successfully.");
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusyId("");
    }
  }

  async function changeStatus(userId: string, status: string) {
    setError("");
    setMessage("");
    setBusyId(userId);
    try {
      await request(`/api/admin/users/${userId}/status`, token, { status }, "POST");
      await refresh();
      setMessage("Account status updated.");
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusyId("");
    }
  }

  async function changeReportApproval(userId: string, enabled: boolean) {
    setBusyId(userId);
    setError("");
    try {
      await request(`/api/admin/users/${userId}/report-approval`, token, { enabled }, "POST");
      await refresh();
      setMessage(enabled ? "Report approval granted." : "Report approval revoked.");
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusyId(""); }
  }

  async function restoreCase(caseId: string) {
    setBusyId(caseId);
    setError("");
    try {
      await request(`/api/admin/trash/${caseId}/restore`, token, {}, "POST");
      await refresh();
      setMessage("Case restored to active workspaces.");
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusyId(""); }
  }

  return (
    <div className="settings-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">GOVERNANCE & RBAC</p>
          <h2>{titles[section]}</h2>
        </div>
      </div>
      {error && <p className="message error" role="alert">{error} <button type="button" onClick={() => { setError(""); refresh().catch(cause => setError(cause.message)); }}>Retry</button></p>}
      {loading && <p role="status">Loading authorized administrative records…</p>}
      {message && <p className="message success" role="status">{message}</p>}
      {section === "users" && <AccessRequests token={token} admin />}
      {section === "permissions" && <OperationalGrants token={token} users={users} actorId={currentUser.id} onChanged={refresh} />}

      {/* Role Management Card */}
      {section === "users" && <Card className="panel">
        <h3>Role & Account Management</h3>
        <p className="muted">
          Assign role-based access control (RBAC) permissions and manage account status.
        </p>
        <label>Search accounts<input value={search} onChange={e => setSearch(e.target.value)} placeholder="Name, email, role or account status" /></label>
        <div className="user-list">
          {!loading && users.filter(item => `${item.display_name} ${item.email} ${item.role} ${item.status}`.toLowerCase().includes(search.toLowerCase())).length === 0 && <p>No accounts match this search.</p>}
          {users.filter(item => `${item.display_name} ${item.email} ${item.role} ${item.status}`.toLowerCase().includes(search.toLowerCase())).map((item) => (
            <div className="user-row" key={item.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", padding: "0.85rem 0", borderBottom: "1px solid #f0f0f2" }}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <strong>{item.display_name || item.email}</strong>
                  {item.id === currentUser.id && <span style={{ fontSize: "0.72rem", background: "#f4f4f5", padding: "0.15rem 0.45rem", borderRadius: "6px" }}>You</span>}
                  <span style={{
                    fontSize: "0.72rem",
                    fontWeight: 650,
                    padding: "0.15rem 0.5rem",
                    borderRadius: "6px",
                    background: item.status === "active" ? "#ecfdf5" : item.status === "suspended" ? "#fef2f2" : "#fef9c3",
                    color: item.status === "active" ? "#047857" : item.status === "suspended" ? "#b91c1c" : "#854d0e",
                  }}>
                    {item.status || "active"}
                  </span>
                </div>
                <span style={{ fontSize: "0.82rem", color: "#71717a" }}>{item.email}</span>
                {(["doctor", "clinician", "admin"].includes(item.role)) && <label className="approval-toggle"><input type="checkbox" checked={!!item.can_approve_reports} disabled={busyId === item.id} onChange={(event) => changeReportApproval(item.id, event.target.checked)} /> Authorized to approve reports</label>}
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <label htmlFor={`role-${item.id}`} className="sr-only">Role for {item.email}</label>
                <select
                  id={`role-${item.id}`}
                  value={item.role === "clinician" ? "doctor" : item.role}
                  disabled={busyId === item.id || item.id === currentUser.id}
                  onChange={(event) => changeRole(item.id, event.target.value)}
                  style={{ minWidth: "160px", padding: "0.45rem 0.65rem", borderRadius: "8px" }}
                >
                  {ROLE_OPTIONS.map(({ value, label }) => (
                    <option value={value} key={value}>{label}</option>
                  ))}
                </select>

                <label htmlFor={`status-${item.id}`} className="sr-only">Status for {item.email}</label>
                <select
                  id={`status-${item.id}`}
                  value={item.status || "active"}
                  disabled={busyId === item.id || item.id === currentUser.id}
                  onChange={(event) => changeStatus(item.id, event.target.value)}
                  style={{ padding: "0.45rem 0.65rem", borderRadius: "8px" }}
                >
                  {STATUS_OPTIONS.map(({ value, label }) => (
                    <option value={value} key={value}>{label}</option>
                  ))}
                </select>
              </div>
            </div>
          ))}
        </div>
      </Card>}

      {section === "access" && <><Card className="panel"><h3>Case content remains separately authorized</h3><p>Administrator status does not grant medical-image access. Existing case owners assign collaborators from the case Overview & access section. Institution membership, ownership correction and access revocation tools are not connected here.</p></Card><Card className="panel">
        <h3>Case Trash</h3>
        <p className="muted">Deleted cases remain in the audit trail and can be restored by an administrator.</p>
        {trash.length ? <div className="simple-list">{trash.map((item) => <div className="list-row" key={item.id}><span><strong>{item.case_code}</strong> · {new Date(item.deleted_at).toLocaleString()}</span><button type="button" disabled={busyId === item.id} onClick={() => restoreCase(item.id)}>Restore</button></div>)}</div> : <p className="muted">Trash is empty.</p>}
      </Card></>}

      {section === "permissions" && <PermissionMatrix />}

      {/* Audit Trail Card */}
      {section === "audit" && <Card className="panel">
        <h3>Recorded administrative activity</h3>
        <p className="muted">This is the API-provided recent audit window, not a complete historical archive. Filters search loaded events only.</p>
        <label>Filter audit events<input value={auditFilter} onChange={e => setAuditFilter(e.target.value)} placeholder="Action or date" /></label>
        <div className="simple-list">
          {!loading && audit.filter(item => `${item.action} ${new Date(item.created_at).toLocaleString()}`.toLowerCase().includes(auditFilter.toLowerCase())).length === 0 && <p>No matching audit events in the loaded window.</p>}
          {audit.filter(item => `${item.action} ${new Date(item.created_at).toLocaleString()}`.toLowerCase().includes(auditFilter.toLowerCase())).slice(0, showAllAudit ? undefined : 10).map((item) => (
            <div className="list-row" key={item.id}>
              <span>{item.action.replaceAll("_", " ")}</span>
              <time>{new Date(item.created_at).toLocaleString()}</time>
            </div>
          ))}
        </div>
        {audit.length > 10 && <button type="button" onClick={() => setShowAllAudit(v => !v)}>{showAllAudit ? "Show ten events" : `Show all loaded events (${audit.length})`}</button>}
      </Card>}
    </div>
  );
}
