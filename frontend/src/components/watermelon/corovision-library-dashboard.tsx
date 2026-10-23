// Adapted from Watermelon library-dashboard's header / metrics / actions /
// circulation and collection composition. No template demo data is used.
import { useState, type ReactNode } from "react";
import { Activity, ArrowUpRight, ClipboardCheck, FileImage, FileText, FolderOpen, Plus, ScanLine, Search } from "lucide-react";
import { Button } from "../prismui/button";
import { Input } from "../prismui/input";
import "./corovision-library-dashboard.css";

type Study = { id: string; case_code: string; status: string; created_at: string; images: { id: string }[]; latest_review?: { id: string } | null };
type Props = {
  hero: ReactNode; cases: Study[];
  canCreate: boolean; canRead: boolean; canViewModels: boolean;
  analyzed: number; pending: number; runs: number | null;
  onNewCase: () => void; onViewCases: () => void; onViewAnalysis: () => void;
  onViewReports: () => void; onViewModels: () => void; onOpenCase: (id: string) => void;
};

export default function CorovisionLibraryDashboard(props: Props) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const count = props.cases.length;
  const images = props.cases.reduce((sum, c) => sum + c.images.length, 0);
  const reviewed = props.cases.filter(c => !!c.latest_review).length;
  const awaiting = props.cases.filter(c => !c.latest_review && c.status === "analyzed").length;
  const preparation = count - reviewed - awaiting;
  const segments = [{ label: "Reviewed", count: reviewed }, { label: "Awaiting review", count: awaiting }, { label: "Other / preparation", count: preparation }];
  let angle = 0;
  const gradient = segments.map((s, i) => { const from = angle; angle += count ? s.count / count * 100 : 0; return `var(--library-segment-${i}) ${from}% ${angle}%`; }).join(",");
  const days = Array.from({ length: 7 }, (_, i) => { const date = new Date(); date.setHours(0, 0, 0, 0); date.setDate(date.getDate() - 6 + i); return date; });
  const points = days.map(day => props.cases.filter(c => { const date = new Date(c.created_at); return date.toDateString() === day.toDateString(); }).length);
  const maximum = Math.max(1, ...points);
  const visible = props.cases.filter(c => c.case_code.toLowerCase().includes(query.toLowerCase()) && (status === "all" || (status === "reviewed" ? !!c.latest_review : status === "pending" ? !c.latest_review && c.status === "analyzed" : !c.latest_review && c.status !== "analyzed"))).sort((a,b) => b.created_at.localeCompare(a.created_at));
  const metrics = [{ title: "Research cases", value: count, note: "Visible to your account", icon: FolderOpen }, { title: "Images uploaded", value: images, note: "Across accessible studies", icon: FileImage }, { title: "Cases analyzed", value: props.analyzed, note: props.runs === null ? "From available case status" : `${props.runs} recorded analysis runs`, icon: ScanLine }, { title: "Pending review", value: props.pending, note: "Awaiting a recorded review", icon: ClipboardCheck }];
  const actions = [
    ...(props.canCreate ? [{ title: "Create a case", note: "Register a de-identified study", icon: Plus, action: props.onNewCase }] : []),
    ...(props.canRead ? [{ title: "Browse studies", note: "Open your case workspace", icon: FolderOpen, action: props.onViewCases }, { title: "Review analysis", note: "Inspect saved masks and overlays", icon: ScanLine, action: props.onViewAnalysis }, { title: "Reports & exports", note: "View permitted research reports", icon: FileText, action: props.onViewReports }] : []),
    ...(props.canViewModels ? [{ title: "Model evaluation", note: "Recorded metrics and model versions", icon: Activity, action: props.onViewModels }] : [])
  ];
  return <section className="cv-library-dashboard" aria-label="CoroVision workspace overview">
    {props.hero}

    {props.canRead && <section aria-labelledby="cv-metrics-title"><div className="cv-library-section-head"><h2 id="cv-metrics-title">Your workspace at a glance</h2><span>Accessible case records</span></div><div className="cv-library-metrics">{metrics.map(m => <article key={m.title}><div><m.icon size={20} aria-hidden="true"/><span>{m.title}</span></div><strong>{m.value.toLocaleString()}</strong><small>{m.note}</small></article>)}</div></section>}
    <section aria-labelledby="cv-actions-title"><div className="cv-library-section-head"><h2 id="cv-actions-title">Quick actions</h2><span>Tools available for your role</span></div><div className="cv-library-actions">{actions.map(a => <button key={a.title} type="button" onClick={a.action}><span className="cv-library-action-icon"><a.icon size={21} aria-hidden="true"/></span><span><strong>{a.title}</strong><small>{a.note}</small></span><ArrowUpRight size={17} aria-hidden="true"/></button>)}</div></section>
    {props.canRead && <>
      <div className="cv-library-insights">
        <section className="cv-library-panel" aria-labelledby="cv-intake-title"><div className="cv-library-section-head"><div><h2 id="cv-intake-title">Study intake</h2><p>Case creation over the last seven days</p></div><span>7 days</span></div>
          <div className="cv-library-bars" role="img" aria-label={days.map((d,i) => `${d.toLocaleDateString()}: ${points[i]} cases`).join("; ")}>{days.map((day, i) => <div key={day.toISOString()}><strong>{points[i]}</strong><div className="cv-library-bar-track"><i style={{height: `${points[i] / maximum * 100}%`}}/></div><small>{day.toLocaleDateString(undefined,{weekday:"short"})}</small></div>)}</div>
          <p className="cv-library-footnote">Counts describe visible cases, not patients or clinical outcomes.</p>
        </section>
        <section className="cv-library-panel" aria-labelledby="cv-distribution-title"><div className="cv-library-section-head"><h2 id="cv-distribution-title">Case overview</h2><FolderOpen size={19} aria-hidden="true"/></div><div className="cv-library-collection"><div className="cv-library-donut" style={{background: count ? `conic-gradient(${gradient})` : "var(--theme-line)"}} aria-hidden="true"><div><strong>{count}</strong><span>cases</span></div></div><ul>{segments.map((s,i) => <li key={s.label}><i style={{background:`var(--library-segment-${i})`}}/><span>{s.label}</span><strong>{s.count}</strong><small>{count ? Math.round(s.count / count * 100) : 0}%</small></li>)}</ul></div></section>
      </div>
      <section className="cv-library-panel" aria-labelledby="cv-studies-title"><div className="cv-library-section-head"><div><h2 id="cv-studies-title">Study library</h2><p>Find a case and continue where you left off.</p></div><Button variant="ghost" onClick={props.onViewCases}>View all <ArrowUpRight size={16} aria-hidden="true"/></Button></div>
        <div className="cv-library-tools"><label><Search size={17} aria-hidden="true"/><span className="sr-only">Search study library</span><Input value={query} placeholder="Search by case code" onChange={e => setQuery(e.target.value)}/></label><div role="group" aria-label="Filter study library">{[["all","All cases"],["pending","Awaiting review"],["reviewed","Reviewed"],["preparation","Other / preparation"]].map(([id,label]) => <button key={id} type="button" aria-pressed={status===id} onClick={() => setStatus(id)}>{label}</button>)}</div></div>
        <div className="cv-library-study-list">{visible.length ? visible.slice(0,6).map(c => <button key={c.id} onClick={() => props.onOpenCase(c.id)}><span className="cv-library-action-icon"><FolderOpen size={20} aria-hidden="true"/></span><span><strong>{c.case_code}</strong><small>{c.images.length} images · Created {new Date(c.created_at).toLocaleDateString()}</small></span><span className="cv-library-status">{c.status.replaceAll("_"," ")}</span><ArrowUpRight size={17} aria-hidden="true"/></button>) : <p className="cv-library-empty">{count ? "No cases match these filters." : "No accessible studies yet. Cases will appear here when created or shared with you."}</p>}</div>
      </section>
    </>}
    <p className="cv-library-footnote">Research prototype · Model outputs require expert review and are not a clinical diagnosis.</p>
  </section>;
}
