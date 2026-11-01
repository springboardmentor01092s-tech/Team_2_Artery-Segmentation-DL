import { useEffect, useState } from "react";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";
import type { User } from "./AccountPanel";
import { canCreateCases, canReadCases, canViewModels } from "./permissions";
import { request } from "./api";
import RoleWorkspace from "./RoleWorkspace";
import CorovisionLibraryDashboard from "./components/watermelon/corovision-library-dashboard";
import type { SidebarView } from "./components/watermelon/macos-sidebar";

type CaseSummary = {
  id: string;
  case_code: string;
  status: string;
  created_at: string;
  images: { id: string }[];
  latest_review?: { id: string } | null;
};

type Activity = { id: string; action: string; case_id: string | null; created_at: string };
type CaseTask = { case_id: string; case_code: string; title: string; view: string; workflow_status: string };
type DashboardAnalytics = {
  total_cases: number;
  cases_analyzed: number;
  analysis_runs: number;
  model_flagged_cases: number;
  cases_without_model_flag: number;
  clinician_severity_distribution: Record<string, number>;
  processing_status: Record<string, number>;
  validation_performance: Record<string, { validation_dice: number; validation_images: number }>;
  recent_analyses: { id: string; case_id: string; case_code: string; image_name: string; model_version: string; created_at: string; stenosis_pixels: number; model_flagged_region: boolean; stenosis_mask_components: number }[];
};

export default function OverviewPanel({
  token, user, cases, onNewCase, onViewCases, onOpenCase, onOpenTask, onViewAnalysis, onViewReports, onViewModels, onOpenWorkspace,
}: {
  token: string;
  user: User;
  cases: CaseSummary[];
  onNewCase: () => void;
  onViewCases: () => void;
  onOpenCase: (id: string) => void;
  onOpenTask: (id: string, view: string) => void;
  onViewAnalysis: () => void;
  onViewReports: () => void;
  onViewModels: () => void;
  onOpenWorkspace: (view: SidebarView) => void;
}) {
  const [activity, setActivity] = useState<Activity[]>([]);
  const [tasks, setTasks] = useState<CaseTask[]>([]);
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  useEffect(() => {
    let active = true;
    async function refresh() {
      const [activityResult, taskResult, analyticsResult] = await Promise.allSettled([
        request<Activity[]>("/api/auth/audit", token),
        request<CaseTask[]>("/api/tasks", token),
        canReadCases(user.role) ? request<DashboardAnalytics>("/api/dashboard/analytics", token) : Promise.resolve(null),
      ]);
      if (!active) return;
      if (activityResult.status === "fulfilled") setActivity(activityResult.value.slice(0, 5));
      if (taskResult.status === "fulfilled") setTasks(taskResult.value);
      if (analyticsResult.status === "fulfilled" && analyticsResult.value) setAnalytics(analyticsResult.value);
    }
    refresh();
    const interval = window.setInterval(() => { if (document.visibilityState === "visible") refresh(); }, 5000);
    return () => { active = false; window.clearInterval(interval); };
  }, [token, user.role]);

  const imageCount = cases.reduce((sum, item) => sum + item.images.length, 0);
  const analyzedOrReviewedCases = analytics?.cases_analyzed ?? cases.filter((item) => item.status.includes("analyzed") || item.status.includes("reviewed")).length;
  const pendingReviews = cases.filter((item) => item.status === "analyzed" && !item.latest_review).length;

  const isDoctor = user.role === "doctor" || user.role === "clinician";
  const isTechnician = user.role === "technician";
  const isResearcher = user.role === "researcher";
  const isML = user.role === "ml_engineer";
  const isAdmin = user.role === "admin";
  const isViewer = user.role === "viewer";

  const roleTitle = isDoctor
    ? (user.role === "clinician" ? "Clinician" : "Doctor")
    : isTechnician
    ? "Technician / Data Operator"
    : isResearcher
    ? "Medical Researcher"
    : isML
    ? "ML Engineer"
    : isAdmin
    ? "System Administrator"
    : "Viewer / Student";

  const heroHeadline = isDoctor
    ? "Coronary Findings, Expert Review"
    : isTechnician
    ? "Prepare Images for Vessel Analysis"
    : isResearcher
    ? "Coronary Artery Analysis"
    : isML
    ? "Evaluate Models. Trace Results."
    : isAdmin
    ? "Manage Access with Confidence"
    : "Explore Assigned Coronary Studies";

  const heroDescription = isDoctor
    ? "Inspect artery overlays and model-flagged regions in authorized studies. Add your assessment and review notes while keeping AI findings separate from clinical judgment."
    : isTechnician
    ? "Upload de-identified angiography images, select the required preprocessing options, and check image quality before passing a case on for analysis."
    : isResearcher
    ? "Prepare de-identified angiography images, explore artery segmentation and model-flagged stenosis regions, and review recorded evaluation results—all in one research workflow."
    : isML
    ? "Inspect registered model versions and recorded validation metrics. Compare documented performance without extending access to clinical cases."
    : isAdmin
    ? "Manage accounts and role-based permissions, review audit activity, and oversee registered models to keep the research workflow accountable."
    : "View the studies shared with you, inspect available artery overlays, and read analysis summaries without changing images or review records.";

  const canCreate = canCreateCases(user.role, user.permissions);
  const canRead = canReadCases(user.role);

  const dashboardHero = (
      <section className="overview-hero overview-hero-solo" aria-labelledby="overview-title">
        <div className="overview-hero-grid" aria-hidden="true" />
        <div className="overview-hero-main">
          <div className="overview-tagline">{isDoctor ? "AI-assisted exploration. Doctor-led interpretation." : isTechnician ? "Every analysis begins with a well-prepared image." : isML ? "Reproducible evaluation for coronary imaging research." : isAdmin ? "Responsible oversight, from accounts to audit trails." : isViewer ? "A clearer view of the research shared with you." : "From angiography to evidence, one study at a time."}</div>
          <h1 id="overview-title">{heroHeadline}</h1>
          <p>{heroDescription}</p>
          <div className="overview-actions">
            {canCreate && (
              <Button onClick={onNewCase}>Create a case <span aria-hidden="true">↗</span></Button>
            )}
            {canRead && <Button variant={canCreate ? "outline" : "default"} onClick={onViewCases}>{isViewer ? "View assigned cases" : "View cases"}</Button>}
            {canRead && <Button variant="outline" onClick={onViewAnalysis}>AI Analysis</Button>}
            {canRead && <Button variant="outline" onClick={onViewReports}>Reports</Button>}
            {canViewModels(user.role) && <Button variant="outline" onClick={onViewModels}>Model Evaluation</Button>}
          </div>
        </div>
      </section>
  );

  return (
    <div className="overview-page">
      <CorovisionLibraryDashboard hero={dashboardHero}
        cases={cases} canCreate={canCreate} canRead={canRead} canViewModels={canViewModels(user.role)}
        analyzed={analyzedOrReviewedCases} pending={pendingReviews} runs={analytics?.analysis_runs ?? null}
        onNewCase={onNewCase} onViewCases={onViewCases} onViewAnalysis={onViewAnalysis} onViewReports={onViewReports}
        onViewModels={onViewModels} onOpenCase={onOpenCase} />



      {canRead && analytics && <>
        <div className="overview-section-heading"><div><p className="eyebrow">ANALYSIS SNAPSHOT</p><h2>Research findings & processing</h2></div><span>Authorized cases only</span></div>
        <div className="overview-stats overview-stats-compact">
          <Card><span>Cases with model-flagged region</span><strong>{analytics.model_flagged_cases}</strong><small>Binary mask present; requires human review</small></Card>
          <Card><span>No model region flagged</span><strong>{analytics.cases_without_model_flag}</strong><small>Does not establish a normal result</small></Card>
            </div>
        <div className="overview-analytics-grid">
          <Card className="panel"><div className="viewer-heading"><h3>Doctor-assessed severity</h3><span>Latest review per case</span></div>
            {Object.entries(analytics.clinician_severity_distribution).map(([label, count]) => <div className="analytics-bar-row" key={label}><span>{label.replaceAll("_", " ")}</span><div><i style={{ width: `${Math.min(100, count / Math.max(1, ...Object.values(analytics.clinician_severity_distribution)) * 100)}%` }} /></div><b>{count}</b></div>)}
            <small className="caption">Severity values are entered by clinical reviewers; the model does not assign grades.</small>
          </Card>
          {canViewModels(user.role) && <Card className="panel"><div className="viewer-heading"><h3>Model validation</h3><span>ARCADE validation split</span></div>
            {Object.entries(analytics.validation_performance).length ? Object.entries(analytics.validation_performance).map(([task, metric]) => <div className="performance-row" key={task}><span>{task === "syntax" ? "Artery segmentation" : task === "stenosis" ? "Stenosis mask" : task}</span><strong>Dice {metric.validation_dice.toFixed(3)}</strong><small>{metric.validation_images} images</small></div>) : <p className="muted">No validation report is available.</p>}
            <small className="caption">Research metrics only; not a per-case confidence estimate or clinical validation.</small>
          </Card>}
        </div>
        <div className="overview-analytics-grid">
          <Card className="panel"><div className="viewer-heading"><h3>Recent analyses</h3><span>{analytics.recent_analyses.length} latest runs</span></div>
            {analytics.recent_analyses.length ? analytics.recent_analyses.map((item) => <button className="analysis-feed-row" key={item.id} type="button" onClick={() => onOpenCase(item.case_id)}><span><strong>{item.case_code}</strong><small>{item.image_name} · {item.model_version}</small></span><span className={item.model_flagged_region ? "flagged" : "not-flagged"}>{item.stenosis_mask_components > 1 ? `${item.stenosis_mask_components} disconnected model regions` : item.model_flagged_region ? "Review flag" : "No mask pixels"}<small>{new Date(item.created_at).toLocaleString()}</small></span></button>) : <p className="muted">No completed model runs yet.</p>}
          </Card>
          <Card className="panel"><div className="viewer-heading"><h3>Processing status</h3><span>Cases</span></div>
            {Object.entries(analytics.processing_status).length ? Object.entries(analytics.processing_status).map(([status, count]) => <div className="processing-row" key={status}><span>{status.replaceAll("_", " ")}</span><strong>{count}</strong></div>) : <p className="muted">No case processing records yet.</p>}
          </Card>
        </div>
      </>}

      {(isResearcher || isDoctor || isTechnician) && <RoleWorkspace role={user.role} onOpen={onOpenWorkspace} />}
      <div className="overview-queues">
        <Card className="panel overview-task-list"><div className="viewer-heading"><h3>My next steps</h3><span>{tasks.length} task{tasks.length === 1 ? "" : "s"}</span></div>{tasks.length ? tasks.map((item) => <button key={item.case_id} type="button" onClick={() => onOpenTask(item.case_id, item.view)}><strong>{item.case_code}</strong><span>{item.title}</span><small>{item.workflow_status.replaceAll("_", " ")}</small></button>) : <p className="muted">No action is waiting for your role.</p>}</Card>
      </div>
      <Card className="panel overview-activity"><div className="viewer-heading"><h3>Recent activity</h3><span>Your account actions</span></div>{activity.length ? <ul>{activity.map((item) => <li key={item.id}><span>{item.action.replaceAll("_", " ")}</span><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></li>)}</ul> : <p className="muted">No recorded activity yet.</p>}</Card>

    </div>
  );
}
