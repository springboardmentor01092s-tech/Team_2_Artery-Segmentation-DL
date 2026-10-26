import { Activity, Database, FlaskConical, FolderOpen, ScanLine, GitBranch, Crosshair, Gauge, Sparkles, BarChart3, FileText, Stethoscope, ClipboardCheck, ShieldCheck, Users, KeyRound, ScrollText, Server, Cpu, Boxes, Rocket, PauseCircle, type LucideIcon } from "lucide-react";
import type { SidebarView } from "./components/watermelon/macos-sidebar";
import { Card } from "./components/prismui/card";
import { Button } from "./components/prismui/button";

type Module = { title: string; description: string; icon: LucideIcon; view?: SidebarView; status?: string };
const moduleItem = (title: string, description: string, icon: LucideIcon, view?: SidebarView, status?: string): Module => ({ title, description, icon, view, status });
const research: Module[] = [
  moduleItem("Dataset Library", "Dataset versions, permissions, annotations and split checks need a connected, access-controlled registry.", Database, undefined, "Registry not connected"),
  moduleItem("Institutional Collaboration", "Shared datasets, access requests and team results require verified institution membership and resource grants. An account name grants no institutional access.", Users, undefined, "Institution scope not configured"),
  moduleItem("Research Projects", "Create and prepare de-identified research cases you own or have permission to access.", FolderOpen, "cases"),
  moduleItem("Artery Segmentation", "Inspect saved artery masks in the shared analysis viewer.", ScanLine, "analysis"),
  moduleItem("Vessel Analysis", "Inspect derived centerlines and available 2D measurements with calibration limitations.", GitBranch, "analysis"),
  moduleItem("Stenosis Detection", "Explore model-flagged regions; pixel scores are not calibrated clinical confidence.", Crosshair, "analysis"),
  moduleItem("Severity Assessment", "Severity is entered by doctors. Validated automated grading is not available.", Gauge, undefined, "Doctor-assessed only"),
  moduleItem("Explainability Viewer", "Compare saved overlays, attribution maps and evidence layers in the shared viewer.", Sparkles, "analysis"),
  moduleItem("Evaluation & Experiments", "Read recorded model metrics and comparisons. Researcher access does not permit activation.", BarChart3, "models"),
  moduleItem("Reports & Exports", "Review and export reports within your authorized research scope.", FileText, "reports"),
  moduleItem("Audit & Provenance", "Inspect the recorded preparation and review history of your authorized research cases.", ScrollText, "cases"),
];
const clinical: Module[] = [
  moduleItem("Assigned Cases", "Open cases you own or have an explicit review assignment for.", FolderOpen, "cases"),
  moduleItem("Image Viewer", "Inspect original images and saved segmentation overlays.", ScanLine, "analysis"),
  moduleItem("Vessel Measurements", "Read available geometric measurements, units and calibration warnings.", GitBranch, "analysis"),
  moduleItem("Stenosis Findings", "Review candidate regions against the source image; AI output is not a diagnosis.", Crosshair, "analysis"),
  moduleItem("AI Evidence & Explainability", "Inspect stored saliency maps and known limitations in the shared viewer.", Sparkles, "analysis"),
  moduleItem("Human Review & Annotations", "Record your assessment and notes when the case grants review permission.", ClipboardCheck, "cases"),
  moduleItem("Review Reports", "Submit or review permitted reports. Approval requires a separate grant.", FileText, "reports"),
];
const preparation: Module[] = [
  moduleItem("Assigned Cases", "Open cases you own or have been assigned to prepare.", FolderOpen, "cases"),
  moduleItem("Image Upload & Import", "Upload supported, authorized case images. Source files are retained and exact duplicate uploads are checked.", ScanLine, "cases"),
  moduleItem("Image Quality Check", "Check the prepared preview, validation feedback and preprocessing record.", ClipboardCheck, "cases"),
  moduleItem("Metadata & Modality Validation", "Review source spacing, frame selection and supported image modality before analysis.", Database, "cases"),
  moduleItem("Case Preparation", "Prepare a study and flag quality problems through case notes. Clinical sign-off is not permitted.", FolderOpen, "cases"),
  moduleItem("Upload History", "Inspect the source image list and recorded preprocessing steps for an authorized case.", ScrollText, "cases"),
];
const generalClinical: Module[] = [
  moduleItem("My Assigned Cases", "Review cases you own or have an explicit assignment for.", FolderOpen, "cases"),
  moduleItem("Patient / Case Overview", "Read the permitted de-identified case context and recorded history.", ClipboardCheck, "cases"),
  moduleItem("Image Viewer & AI Findings", "Inspect saved source images and preliminary model overlays.", ScanLine, "analysis"),
  moduleItem("Vessel Measurements", "Review available geometric outputs with their units and limitations.", GitBranch, "analysis"),
  moduleItem("Severity & Review Notes", "Severity is a doctor-entered assessment, not an automated validated estimate.", Stethoscope, "cases"),
  moduleItem("Case Follow-up", "Record follow-up review decisions and notes within your assigned scope.", ClipboardCheck, "cases"),
  moduleItem("Reviewed Reports", "Read and submit review records. Final approval requires a separate grant.", FileText, "reports"),
];
const ml: Module[] = [
  moduleItem("Dataset Registry", "Provenance and dataset-grant management need a connected registry. No patient-case access is granted.", Database, undefined, "Registry not connected"),
  moduleItem("Training Jobs", "Training is paused at the user's request. No jobs are started from this screen.", PauseCircle, undefined, "Paused · Job controls not connected"),
  moduleItem("Compute & GPU Monitor", "Live resource monitoring requires a connected compute agent; no simulated usage is shown.", Cpu, undefined, "Monitor not connected"),
  moduleItem("Model Registry", "Inspect recorded weights, versions, task provenance and checkpoint fingerprints.", Boxes, "models"),
  moduleItem("Evaluation Lab & Model Comparison", "Review recorded validation, held-out results and architecture comparisons.", BarChart3, "models"),
  moduleItem("Segmentation Experiments", "Inspect recorded segmentation experiments; launching runs is not yet connected.", FlaskConical, "models"),
  moduleItem("Detection & Severity Experiments", "Recorded stenosis-mask experiments are available; automated severity is not validated.", Crosshair, "models"),
  moduleItem("Severity Model Experiments", "Severity-labelled data and validated measurement methods are required before severity training can be enabled.", Gauge, undefined, "Validated severity workflow unavailable"),
  moduleItem("Explainability Tests", "Automated explanation-fidelity and artifact tests still need an experiment workflow.", Sparkles, undefined, "Not implemented"),
  moduleItem("Deployment Candidates", "Import experimental candidates and submit them for independent administrator review. Approval never activates a checkpoint.", Rocket, "models"),
  moduleItem("Experiment Logs & Reports", "Inspect the experiments and reports recorded in the model workspace.", ScrollText, "models"),
];
const admin: Module[] = [
  moduleItem("User Management", "Inspect account status and manage active, suspended or pending accounts.", Users, "admin"),
  moduleItem("Roles & Permissions", "Apply trusted, audited role changes. Clinical approval is a separate grant.", KeyRound, "admin"),
  moduleItem("Access Requests & Approvals", "Review submitted requests and record eligibility verification before granting elevated access.", ClipboardCheck, "admin"),
  moduleItem("Dataset Governance", "Dataset-specific grants, retention and licence enforcement need a dedicated registry.", Database, undefined, "Not implemented"),
  moduleItem("Institution Management", "Verified membership and institution-specific data boundaries need a dedicated governance workflow.", Users, undefined, "Not implemented"),
  moduleItem("Model Governance", "Inspect the registry and authorize research checkpoint activation. Clinical deployment is not configured.", ShieldCheck, "models"),
  moduleItem("System & API Health", "Live service monitoring and resource metrics need an operational monitor.", Server, undefined, "Monitor not connected"),
  moduleItem("Audit Logs", "Read authorized platform audit events; no audit-editing action is available.", ScrollText, "admin"),
  moduleItem("Security & Configuration", "Manage accounts and permissions. Secrets and environment configuration are not exposed here.", ShieldCheck, "admin"),
  moduleItem("System Reports", "Infrastructure and governance reporting needs a dedicated reporting service.", FileText, undefined, "Not implemented"),
  moduleItem("Storage & Usage", "Live storage accounting is not connected. No simulated capacity or usage values are shown.", Database, undefined, "Monitor not connected"),
];

export default function RoleWorkspace({ role, onOpen }: { role: string; onOpen: (view: SidebarView) => void }) {
  const doctor = role === "doctor" || role === "clinician";
  const doctorModules = [...clinical, ...generalClinical.filter(item => ["Patient / Case Overview", "Case Follow-up"].includes(item.title))];
  const modules = role === "admin" ? [...admin, ...doctorModules] : role === "ml_engineer" ? ml : role === "technician" ? preparation : doctor ? doctorModules : research;
  const Icon = role === "admin" ? ShieldCheck : role === "ml_engineer" ? Cpu : role === "technician" ? ClipboardCheck : doctor ? Stethoscope : FlaskConical;
  const title = role === "admin" ? "System governance" : role === "ml_engineer" ? "Model lifecycle & evaluation" : role === "technician" ? "Image preparation & quality" : doctor ? (role === "clinician" ? "Clinician workspace" : "Doctor workspace") : "Research engines & projects";
  return <section className="role-workspace" aria-labelledby="role-workspace-title">
    <div className="role-workspace-heading"><Icon size={28} aria-hidden="true" /><div>{role === "admin" || role === "ml_engineer" ? <h1 id="role-workspace-title">{title}</h1> : <h2 id="role-workspace-title">{title}</h2>}<p className="muted">Role-specific tools. Every case action still requires server-side authorization. Unconnected capabilities are explicitly marked.</p></div></div>
    <div className="role-module-grid">{modules.map(({ title: name, description, icon: ModuleIcon, view, status }) => <Card className="panel role-module" key={name}>
      <ModuleIcon size={24} aria-hidden="true" /><h3>{name}</h3><p className="muted">{description}</p>
      {view ? <Button type="button" variant="outline" onClick={() => onOpen(view)}>Open {view === "analysis" ? "shared viewer" : view === "models" ? "model workspace" : view === "admin" ? "administration" : view === "cases" ? "cases" : "reports"}</Button> : <small className="role-module-status">{status}</small>}
    </Card>)}</div>
    <p className="caption"><Activity size={14} aria-hidden="true" /> Research prototype. No automated clinical grading, clinical deployment or live compute control is implied.</p>
  </section>;
}
