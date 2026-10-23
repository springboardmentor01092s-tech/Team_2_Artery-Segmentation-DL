import ResultEvidence from "./ResultEvidence";
import { useEffect, useState } from "react";
import { Download, Printer } from "lucide-react";
import { apiUrl, request } from "./api";
import type { AnalysisResult, CaseRecord, ImageRecord } from "./caseTypes";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";
import { canExportReports } from "./permissions";

type Props = {
  token: string;
  role: string;
  cases: CaseRecord[];
  selectedCase?: CaseRecord;
  selectedImage?: ImageRecord;
  analysis: AnalysisResult | null;
  preview: string;
  overlay: string;
  onCaseChange: (id: string) => void;
  onImageChange: (id: string) => void;
  onAnalysis: () => void;
};

function download(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const csv = (value: unknown) => `"${String(value ?? "").replaceAll('"', '""')}"`;

export default function ReportsPage({ token, role, cases, selectedCase, selectedImage, analysis, preview, overlay, onCaseChange, onImageChange, onAnalysis }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [source, setSource] = useState("");
  const [explanationMaps, setExplanationMaps] = useState<Record<string, string>>({});
  const reviewed = selectedCase?.latest_review;
  const allowed = !!selectedCase?.permissions?.can_export && canExportReports(role);

  useEffect(() => {
    setSource("");
    if (!selectedImage || !/\.(png|jpe?g|webp|gif|bmp)$/i.test(selectedImage.original_name)) return;
    let active = true;
    let url = "";
    fetch(apiUrl(selectedImage.source_url || `/api/images/${selectedImage.id}/source`), { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => { if (!response.ok) throw new Error("Original image unavailable"); return response.blob(); })
      .then((blob) => { url = URL.createObjectURL(blob); if (active) setSource(url); })
      .catch(() => {});
    return () => { active = false; if (url) URL.revokeObjectURL(url); };
  }, [selectedImage?.id, token]);

  useEffect(() => {
    setExplanationMaps({});
    if (!analysis) return;
    let active = true;
    const created: string[] = [];
    const entries = [
      ["Centerline graph", analysis.centerline_url],
      ["Stenosis probability / explainability", analysis.stenosis_probability_url],
      ["Grad-CAM saliency", analysis.gradcam_url],
      ["Attention map", analysis.attention_map_url],
    ].filter((entry): entry is [string, string] => Boolean(entry[1]));
    Promise.all(entries.map(async ([label, url]) => {
      const response = await fetch(apiUrl(url), { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) return [label, ""] as const;
      const blobUrl = URL.createObjectURL(await response.blob());
      created.push(blobUrl);
      return [label, blobUrl] as const;
    })).then((items) => { if (active) setExplanationMaps(Object.fromEntries(items.filter(([, url]) => url))); })
      .catch(() => {});
    return () => { active = false; created.forEach(URL.revokeObjectURL); };
  }, [analysis?.id, token]);

  async function exportReport(format: "json" | "csv" | "pdf") {
    if (!selectedCase || !allowed) return;
    setBusy(true);
    setError("");
    try {
      const exported = await request<{ export_metadata: object; case: CaseRecord }>(`/api/cases/${selectedCase.id}/export`, token);
      const report = { ...exported, generated_at: new Date().toISOString(), selected_image: selectedImage || null,
        analysis: analysis || null, clinician_review: reviewed || null,
        caveat: "AI-assisted research output, not a standalone clinical diagnosis. Binary mask pixels do not quantify stenosis severity or narrowing. Disconnected mask components are not confirmed lesion counts. Model probabilities are uncalibrated and must not be interpreted as clinical confidence." };
      const safeName = selectedCase.case_code.replace(/[^a-z0-9_-]/gi, "_");
      if (format === "json") download(`${safeName}-report.json`, JSON.stringify(report, null, 2), "application/json");
      if (format === "csv") {
        const columns = ["case_code", "study_date", "modality", "status", "image_name", "model_version", "analysis_time", "artery_pixels", "stenosis_pixels", "stenosis_region_flag", "narrowing_percent", "ai_severity", "ai_confidence", "centerline_length", "mean_diameter", "projected_mask_area", "branching_points", "endpoints", "continuity_ratio", "tortuosity", "review_decision", "clinician_assessed_severity", "quality_flags"];
        const values = [selectedCase.case_code, selectedCase.scan_date, selectedCase.modality, selectedCase.status,
          selectedImage?.original_name, analysis?.model_version, analysis?.created_at, analysis?.artery_pixels,
          analysis?.stenosis_pixels,
          analysis?.stenosis_pixels ? "model flagged; review required" : "no mask pixels; not a normal diagnosis",
          "not estimated", "not inferred by model",
          analysis?.model_scores?.calibration === "uncalibrated_pixel_probabilities" ? "not calibrated" : "not available",
          analysis?.vessel_analysis?.centerline_length, analysis?.vessel_analysis?.mean_diameter,
          analysis?.vessel_analysis?.projected_mask_area, analysis?.vessel_analysis?.branching_points,
          analysis?.vessel_analysis?.endpoints, analysis?.vessel_analysis?.continuity_ratio,
          analysis?.vessel_analysis?.tortuosity,
          reviewed?.decision, reviewed?.stenosis_severity, analysis?.vessel_analysis?.quality_flags?.map((flag) => flag.code).join("; ")];
        download(`${safeName}-report.csv`, `${columns.join(",")}\n${values.map(csv).join(",")}\n`, "text/csv;charset=utf-8");
      }
      if (format === "pdf") window.print();
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }

  return <div className="reports-page">
    <div className="page-heading"><div><p className="eyebrow">RESULTS & EXPORT</p><h2>Reports</h2></div><span className="stage-badge">{selectedCase ? selectedCase.report_status.replaceAll("_", " ") : "Select a case"}</span></div>
    <div className="report-actions">
      <label>Case<select value={selectedCase?.id || ""} onChange={(event) => onCaseChange(event.target.value)}><option value="">Select a case</option>{cases.map((item) => <option key={item.id} value={item.id}>{item.case_code}</option>)}</select></label>
      <label>Image<select value={selectedImage?.id || ""} onChange={(event) => onImageChange(event.target.value)} disabled={!selectedCase?.images.length}><option value="">Select an image</option>{selectedCase?.images.map((item) => <option key={item.id} value={item.id}>{item.original_name}</option>)}</select></label>
      {allowed && selectedCase && <div className="report-export-buttons"><Button type="button" variant="outline" disabled={busy} onClick={() => exportReport("json")}><Download size={16} /> JSON</Button><Button type="button" variant="outline" disabled={busy} onClick={() => exportReport("csv")}><Download size={16} /> CSV</Button><Button type="button" variant="outline" disabled={busy} onClick={() => exportReport("pdf")}><Printer size={16} /> Save PDF</Button></div>}
    </div>
    {error && <p className="message error" role="alert">{error}</p>}
    {!selectedCase ? <Card className="panel"><p className="muted">Choose a case to view its research report.</p></Card> : <Card className="panel report-sheet">
      <div className="report-heading"><div><p className="eyebrow">COROVISION AI · RESEARCH REPORT</p><h3>{selectedCase.case_code}</h3></div><strong>{selectedCase.report_status.replaceAll("_", " ")} · v{selectedCase.report_version || 0}</strong></div>
      <p className="muted">Workflow: {selectedCase.workflow_status.replaceAll("_", " ")} · Processing: {selectedCase.processing_status.replaceAll("_", " ")}{selectedCase.report_approved_at ? ` · Approved ${new Date(selectedCase.report_approved_at).toLocaleString()}` : ""}</p>
      <div className="report-facts"><div><span>Study date</span><strong>{selectedCase.scan_date || "Not provided"}</strong></div><div><span>Modality</span><strong>{selectedCase.modality}</strong></div><div><span>Case status</span><strong>{selectedCase.status}</strong></div><div><span>Image</span><strong>{selectedImage?.original_name || "None selected"}</strong></div></div>
      {selectedImage && <div className="report-images"><figure>{(source || preview) && <img src={source || preview} alt={source ? "Original uploaded study" : "Processed angiography preview"} />}<figcaption>{source ? "Original uploaded image" : "Processed preview (original format not browser-displayable)"}</figcaption></figure><figure>{overlay ? <img src={overlay} alt="AI vessel overlay" /> : <div className="image-empty">No AI overlay yet</div>}<figcaption>AI segmentation overlay</figcaption></figure></div>}
      <div className="report-facts"><div><span>Model version</span><strong>{analysis?.model_version || "Not analyzed"}</strong></div><div><span>Analysis time</span><strong>{analysis ? new Date(analysis.created_at).toLocaleString() : "Not available"}</strong></div><div><span>Predicted artery pixels</span><strong>{analysis?.artery_pixels.toLocaleString() || "Not available"}</strong></div><div><span>Predicted stenosis pixels</span><strong>{analysis?.stenosis_pixels.toLocaleString() || "Not available"}</strong></div></div>
      {analysis && <div className="report-facts"><div><span>Model stenosis flag</span><strong>{analysis.stenosis_pixels > 0 ? "Region flagged for review" : "No mask pixels flagged"}</strong></div><div><span>Disconnected mask components</span><strong>{analysis.vessel_analysis?.stenosis_mask_components ?? "Unavailable"}</strong></div><div><span>Estimated narrowing</span><strong>Not estimated</strong></div><div><span>AI severity grade</span><strong>Not inferred</strong></div><div><span>Model confidence</span><strong>{analysis.model_scores?.calibration === "uncalibrated_pixel_probabilities" ? "Uncalibrated; unavailable" : "Unavailable"}</strong></div></div>}
      {analysis?.vessel_analysis && <div className="report-facts"><div><span>Centerline length</span><strong>{analysis.vessel_analysis.centerline_length} {analysis.vessel_analysis.diameter_unit}</strong></div><div><span>Mean diameter</span><strong>{analysis.vessel_analysis.mean_diameter ?? "Unavailable"} {analysis.vessel_analysis.diameter_unit}</strong></div><div><span>Projected mask area</span><strong>{analysis.vessel_analysis.projected_mask_area?.toLocaleString() ?? "Unavailable"} {analysis.vessel_analysis.area_unit}</strong></div><div><span>Boundary length</span><strong>{analysis.vessel_analysis.boundary_length?.toLocaleString() ?? "Unavailable"} {analysis.vessel_analysis.diameter_unit}</strong></div><div><span>Branch points / endpoints</span><strong>{analysis.vessel_analysis.branching_points ?? "—"} / {analysis.vessel_analysis.endpoints ?? "—"}</strong></div><div><span>Continuity</span><strong>{analysis.vessel_analysis.continuity_ratio?.toFixed(2) ?? "Unavailable"}</strong></div><div><span>Tortuosity</span><strong>{analysis.vessel_analysis.tortuosity?.toFixed(2) ?? "Unavailable"}</strong></div><div><span>Cross-sectional area</span><strong>{analysis.vessel_analysis.cross_section_area == null ? "Requires 3D scan" : analysis.vessel_analysis.cross_section_area}</strong></div></div>}
      {Object.entries(explanationMaps).length > 0 && <div className="report-explanations"><h4>Vessel geometry & model explanation</h4><div className="report-images">{Object.entries(explanationMaps).map(([label, url]) => <figure key={label}><img src={url} alt={label} /><figcaption>{label}</figcaption></figure>)}</div></div>}
      {analysis?.vessel_analysis?.quality_flags?.length ? <div className="report-review"><h4>Image / segmentation quality flags</h4><ul>{analysis.vessel_analysis.quality_flags.map((flag) => <li key={flag.code}><strong>{flag.severity.toUpperCase()}</strong> · {flag.message}</li>)}</ul><p>Review these flags alongside the source image and the selected model explanation.</p></div> : null}
      {analysis && <ResultEvidence result={analysis.structured_result} />}
      {reviewed && <div className="report-review"><h4>Doctor review</h4><p>Decision: <strong>{reviewed.decision.replaceAll("_", " ")}</strong> · Doctor assessed severity: <strong>{reviewed.stenosis_severity || "Unspecified"}</strong></p>{reviewed.notes && <p>{reviewed.notes}</p>}<small>Recorded {new Date(reviewed.created_at).toLocaleString()}</small></div>}
      <p className="privacy-note">AI-assisted research output, not a standalone clinical diagnosis. Mask pixel counts do not measure stenosis severity or narrowing; disconnected mask components are not confirmed lesion counts. Model probabilities are uncalibrated, not clinical confidence. Only the doctor review above, when present, represents a human assessment.</p>
      {!analysis && selectedImage && <Button type="button" className="primary report-analysis-link" onClick={onAnalysis}>Open AI analysis</Button>}
    </Card>}
  </div>;
}
