import { Card } from "./components/prismui/card";
const rows = [
  ["Create a case", "Separate grant", "Authorized scope", "Research scope", "Intake scope", "—", "—"],
  ["Upload case images", "Grant + edit assignment", "Owner / edit assignment", "Owner / edit assignment", "Owner / edit assignment", "—", "—"],
  ["Read medical cases", "Owner / assignment only", "Owner / assignment only", "Owner / assignment only", "Owner / assignment only", "—", "Read-only assignment"],
  ["Run AI analysis", "Grant + owner/review/edit", "Owner / review / edit", "Owner / review / edit", "Grant + owner/review/edit", "Test jobs not connected", "—"],
  ["Create clinical review", "—", "Owner / review / edit", "—", "—", "—", "—"],
  ["Approve clinical report", "—", "Separate approval grant", "—", "—", "—", "—"],
  ["Export case results", "Separate grant + case access", "Case access", "Research case access", "—", "—", "—"],
  ["Read model registry", "Yes", "Relevant version only", "Read-only", "—", "Read-only", "—"],
  ["Activate research checkpoint", "Audited action", "—", "—", "—", "—", "—"],
  ["Production model approval", "Workflow not implemented", "—", "—", "—", "Submission not implemented", "—"],
  ["Train / monitor compute", "Not connected", "—", "Not connected", "—", "Not connected · paused", "—"],
  ["Manage users and roles", "Audited administration", "—", "—", "—", "—", "—"],
];
export default function PermissionMatrix() {
  return <Card className="panel"><h3>Operational permission matrix</h3><p className="muted">A role is a maximum, not access to every record. Case ownership, assignment level, account status and separate grants are checked on the server. A read-only assignment cannot run analysis.</p><div className="table-scroll"><table><thead><tr>{["Action", "Administrator", "Doctor / Clinical Reviewer", "Researcher", "Technician", "ML Engineer", "Standard User / Viewer"].map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{rows.map(([name, ...cells]) => <tr key={name}><th scope="row">{name}</th>{cells.map((cell, index) => <td key={index}>{cell}</td>)}</tr>)}</tbody></table></div><p className="caption">The Institutional Researcher demo account currently uses Researcher permissions. Institution membership, institution-specific datasets and shared-resource grants are not implemented, and no organization-wide access is implied.</p></Card>;
}
