import { useEffect, useRef, useState, type PointerEvent } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, Play, FileText, Eye, GitBranch, Layers3, ScanLine, Sparkles } from "lucide-react";
import type { AnalysisResult, CaseRecord, ImageRecord } from "./caseTypes";
import AnalysisHistory from "./AnalysisHistory";
import ResultEvidence from "./ResultEvidence";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";
import { ContextualAIBar } from "./components/watermelon/contextual-ai-bar";
import { QuickSwitcher } from "./components/watermelon/quick-switcher";
import { SelectAIAgent, type AIAgent } from "./components/watermelon/select-ai-agent";
import { apiUrl } from "./api";

type Props = {
  token: string;
  cases: CaseRecord[];
  selectedCase?: CaseRecord;
  selectedImage?: ImageRecord;
  processedPreview: string;
  overlay: string;
  analysis: AnalysisResult | null;
  history: AnalysisResult[];
  modelsReady: boolean;
  analysisBusy: boolean;
  jobStatus?: string;
  canRunAnalysis: boolean;
  onCaseChange: (id: string) => void;
  onImageChange: (id: string) => void;
  onRun: () => void;
  onSelectAnalysis: (result: AnalysisResult) => void;
  onUpload: () => void;
  onReports: () => void;
};

export default function AnalysisWorkbench({ token, cases, selectedCase, selectedImage, processedPreview, overlay, analysis, history, modelsReady, analysisBusy, jobStatus, canRunAnalysis, onCaseChange, onImageChange, onRun, onSelectAnalysis, onUpload, onReports }: Props) {
  const [mode, setMode] = useState<"source" | "processed" | "overlay" | "attention" | "artery_probability" | "probability" | "gradcam" | "centerline">("overlay");
  const [opacity, setOpacity] = useState(80);
  const [showCandidates, setShowCandidates] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [source, setSource] = useState("");
  const [sourceError, setSourceError] = useState("");
  const [xaiLayers, setXaiLayers] = useState<Record<string, string>>({});
  const [evidenceGuide, setEvidenceGuide] = useState("");
  const drag = useRef<{ x: number; y: number; left: number; top: number } | null>(null);

  useEffect(() => { setZoom(1); setOffset({ x: 0, y: 0 }); setMode("overlay"); }, [selectedImage?.id]);
  useEffect(() => {
    setSource("");
    setSourceError("");
    if (!selectedImage || !/\.(png|jpe?g|webp|gif|bmp)$/i.test(selectedImage.original_name)) return;
    let active = true;
    let url = "";
    fetch(apiUrl(selectedImage.source_url || `/api/images/${selectedImage.id}/source`), { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => { if (!response.ok) throw new Error("Original image unavailable"); return response.blob(); })
      .then((blob) => { url = URL.createObjectURL(blob); if (active) setSource(url); })
      .catch((cause: Error) => { if (active) setSourceError(cause.message); });
    return () => { active = false; if (url) URL.revokeObjectURL(url); };
  }, [selectedImage?.id, token]);

  useEffect(() => {
    setXaiLayers({});
    if (!analysis || !token) return;
    let active = true;
    const urls: string[] = [];
    const entries = [
      ["attention", analysis.attention_map_url],
      ["artery_probability", analysis.artery_probability_url],
      ["probability", analysis.stenosis_probability_url],
      ["gradcam", analysis.gradcam_url],
      ["centerline", analysis.centerline_url],
    ] as const;
    Promise.all(entries.map(async ([key, path]) => {
      if (!path) return;
      const response = await fetch(apiUrl(path), { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) return;
      const url = URL.createObjectURL(await response.blob());
      if (active) { urls.push(url); setXaiLayers((previous) => ({ ...previous, [key]: url })); }
      else URL.revokeObjectURL(url);
    })).catch(() => undefined);
    return () => { active = false; urls.forEach((url) => URL.revokeObjectURL(url)); };
  }, [analysis?.id, token]);

  function updateZoom(next: number) { setZoom(Math.min(5, Math.max(1, next))); if (next <= 1) setOffset({ x: 0, y: 0 }); }
  function onPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (zoom <= 1) return;
    drag.current = { x: event.clientX, y: event.clientY, left: offset.x, top: offset.y };
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function onPointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!drag.current) return;
    setOffset({ x: drag.current.left + event.clientX - drag.current.x, y: drag.current.top + event.clientY - drag.current.y });
  }
  const canAnalyze = !!selectedImage && selectedCase?.modality === "XCA" && modelsReady;
  const renderedImage = mode === "source" ? (source || processedPreview)
    : mode === "overlay" ? (overlay || processedPreview)
      : mode === "attention" || mode === "artery_probability" || mode === "probability" || mode === "gradcam" || mode === "centerline"
        ? (xaiLayers[mode] || processedPreview) : processedPreview;
  const evidenceAgents: AIAgent[] = [
    { id: "segmentation", name: "Segmentation", icon: <ScanLine size={20} aria-hidden="true" /> },
    { id: "stenosis", name: "Stenosis", icon: <Eye size={20} aria-hidden="true" /> },
    { id: "vessel_graph", name: "Vessel graph", icon: <GitBranch size={20} aria-hidden="true" /> },
  ];

  function showEvidenceGuide(question: string, lens = "segmentation") {
    if (!analysis) { setEvidenceGuide("Run or select a saved analysis before reviewing explainability evidence."); return; }
    const context = question ? ` Your question: “${question}”` : "";
    if (lens === "stenosis") {
      setMode("probability");
      setEvidenceGuide(`Stenosis evidence comes from the saved mask and raw score layer, when available. The current mask contains ${analysis.stenosis_pixels.toLocaleString()} predicted pixels. Inspect it against the original image; it is not a diagnosis or calibrated confidence score.${context}`);
    } else if (lens === "vessel_graph") {
      setMode("centerline");
      setEvidenceGuide(`Vessel-graph evidence comes from the saved artery mask and its derived centerline. Measurements and branch candidates are approximate 2D mask outputs; verify graph continuity visually.${context}`);
    } else {
      setMode("overlay");
      setEvidenceGuide(`Segmentation evidence uses the saved artery overlay (${analysis.artery_pixels.toLocaleString()} predicted pixels). Compare the mask edge with the source and processed layers before relying on it.${context}`);
    }
  }

  return <div className="workbench-page">
    {jobStatus && <p role="status">Analysis job: {jobStatus}. You may revisit this image to recover its saved job status.</p>}
    <div className="page-heading"><div><p className="eyebrow">CORONARY IMAGING</p><h2>AI Analysis Workbench</h2></div><span className="stage-badge">Research only</span></div>
    <div className="workbench-selectors">
      <label>Case<select value={selectedCase?.id || ""} onChange={(event) => onCaseChange(event.target.value)}><option value="">Select a case</option>{cases.map((item) => <option value={item.id} key={item.id}>{item.case_code} · {item.status}</option>)}</select></label>
      <label>Study image<select value={selectedImage?.id || ""} onChange={(event) => onImageChange(event.target.value)} disabled={!selectedCase?.images.length}><option value="">Select an image</option>{selectedCase?.images.map((item) => <option value={item.id} key={item.id}>{item.original_name}</option>)}</select></label>
    </div>
    {!selectedImage ? <Card className="panel"><p className="muted">Select a case image to inspect the processed image and AI overlay.</p><Button type="button" className="primary" onClick={onUpload}>Open cases</Button></Card> : <>
      <div className="workbench-grid">
        <Card className="panel workbench-viewer-panel">
          <div className="viewer-heading"><h3>Angiography viewer</h3><span>{selectedImage.width} × {selectedImage.height} source pixels</span></div>
          <div className="workbench-layer-tabs" role="group" aria-label="Image layer">
            {(["source", "processed", "overlay", "centerline", "artery_probability", "probability", "attention", "gradcam"] as const).map((item) => <button key={item} type="button" aria-pressed={mode === item} className={mode === item ? "active" : ""} onClick={() => setMode(item)}>{item === "source" ? "Original" : item === "processed" ? "Processed" : item === "overlay" ? "AI overlay" : item === "centerline" ? "Centerline graph" : item === "artery_probability" ? "Artery probability" : item === "attention" ? "Attention" : item === "probability" ? "Stenosis probability" : "Grad-CAM"}</button>)}
          </div>
          <div className="workbench-canvas" onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }}>
            {processedPreview ? <div className="workbench-image-stack" style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})` }}>
              {mode === "overlay" ? <><img src={processedPreview} alt="Preprocessed angiography image" draggable={false} />{overlay && <img className="workbench-overlay" src={overlay} alt="AI artery and suspected stenosis overlay" style={{ opacity: opacity / 100 }} draggable={false} />}</> : <img src={renderedImage} alt={mode === "source" ? "Original uploaded study" : mode === "processed" ? "Preprocessed angiography image" : mode === "centerline" ? "Algorithmic centerline paths, branch nodes, and endpoints" : mode === "attention" ? "Attention gate visualization" : mode === "artery_probability" ? "Uncalibrated artery pixel probability heatmap" : mode === "probability" ? "Uncalibrated stenosis pixel probability heatmap" : "Grad-CAM saliency map for stenosis segmentation output"} draggable={false} />}
              {mode === "overlay" && showCandidates && !!analysis?.structured_result?.candidates.length &&
                <svg viewBox="0 0 512 512" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Saved stenosis candidate bounds and uncalibrated scores"
                  style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
                  <title>Model candidates, not confirmed lesions. Scores are uncalibrated.</title>
                  {analysis.structured_result.candidates.map((candidate, index) => {
                    const box = candidate.bbox_prepared_xyxy;
                    if (!box || box.length !== 4 || !box.every(Number.isFinite)) return null;
                    const [x1, y1, x2, y2] = box;
                    const color = ["#ffe156", "#80ff9e", "#ffffff"][index % 3];
                    const tx = Math.min(335, x2 + 8), ty = Math.max(18, Math.min(495, y1 + index * 22));
                    return <g key={candidate.candidate_id}>
                      <rect x={x1} y={y1} width={Math.max(0, x2-x1)} height={Math.max(0, y2-y1)} fill="none" stroke={color} strokeWidth={1.5} strokeDasharray={index ? "5 3" : undefined} />
                      <line x1={(x1+x2)/2} y1={(y1+y2)/2} x2={tx} y2={ty} stroke={color} strokeWidth={.8} />
                      <text x={tx} y={ty} fill={color} fontSize={11} stroke="#111827" strokeWidth={3} paintOrder="stroke" strokeLinejoin="round">
                        {candidate.candidate_id} · raw {candidate.model_score?.toFixed(3) ?? "unavailable"}
                      </text>
                    </g>;
                  })}
                </svg>}
            </div> : <p>Loading image…</p>}
          </div>
          <div className="workbench-toolbar" role="group" aria-label="Viewer controls">
            <button type="button" aria-label="Zoom out" onClick={() => updateZoom(zoom - .25)} disabled={zoom <= 1}><ZoomOut size={18} /></button>
            <span aria-live="polite">{Math.round(zoom * 100)}%</span>
            <button type="button" aria-label="Zoom in" onClick={() => updateZoom(zoom + .25)} disabled={zoom >= 5}><ZoomIn size={18} /></button>
            <button type="button" aria-label="Reset view" onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }}><RotateCcw size={18} /></button>
            <button type="button" aria-label="Fit image to screen" onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }}><Maximize2 size={18} /></button>
          </div>
          {mode === "source" && !source && <p className="caption">{sourceError || "Original DICOM/TIFF cannot be displayed by this browser; showing its processed preview."}</p>}
          {mode === "overlay" && !overlay && <p className="caption">No saved AI overlay for this image yet. Run analysis to create one.</p>}
          {["attention", "artery_probability", "probability", "gradcam", "centerline"].includes(mode) && !xaiLayers[mode] && <p className="caption">This map is unavailable. Run analysis with a supported segmentation checkpoint first.</p>}
          {mode === "overlay" && overlay && <label className="workbench-opacity">Overlay opacity <input type="range" min="0" max="100" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /> <output>{opacity}%</output></label>}
          {mode === "overlay" && !!analysis?.structured_result?.candidates.length && <label className="caption"><input type="checkbox" checked={showCandidates} onChange={(event) => setShowCandidates(event.target.checked)} /> Show saved candidate bounds and raw scores. Overlapping candidates may represent the same region.</label>}
          <p className="caption">{mode === "overlay" ? "Cyan marks predicted artery pixels; coral marks predicted stenosis pixels. Colors are model output, not verified anatomy." : mode === "centerline" ? "The artery mask is shown faintly under cyan traced paths; yellow labels mark grouped junctions; green dots mark endpoints. Nodes are graph candidates, not confirmed anatomical branches." : mode === "attention" ? "Attention gates show where the model weights skip features; this visualization is not a faithful or clinically validated explanation." : mode === "artery_probability" || mode === "probability" ? "Pixel probabilities are uncalibrated model scores; color intensity is not a patient-level confidence score." : mode === "gradcam" ? "Grad-CAM highlights features that influence the stenosis segmentation logits. It is a research saliency map, not a clinical explanation." : "Review all model outputs against the original study."}</p>
        </Card>
        <Card className="panel workbench-findings">
          <p className="eyebrow">MODEL OUTPUT</p><h3>{analysis ? "Analysis complete" : "Ready for analysis"}</h3>
          <p className="muted">{selectedCase?.case_code} · {selectedImage.original_name}</p>
          <div className="metadata"><div><span>Model</span><strong>{analysis?.model_version || "Not run"}</strong></div><div><span>Study modality</span><strong>{selectedCase?.modality}</strong></div><div><span>Pixel spacing</span><strong>{selectedImage.spacing_mm || "Unavailable"}</strong></div></div>
          {canRunAnalysis ? <Button type="button" className="primary" disabled={!canAnalyze || analysisBusy} onClick={onRun}><Play size={16} aria-hidden="true" /> {analysisBusy ? "Processing…" : analysis ? "Run again" : "Run AI analysis"}</Button> : <p className="caption">Your role can inspect saved analyses but cannot start a model run.</p>}
          {!modelsReady && <p className="caption">Models are unavailable. Install the verified research artifacts and inference dependencies.</p>}
          {selectedCase?.modality !== "XCA" && <p className="caption">The current models accept X-ray coronary angiography only.</p>}
          {analysis && <><div className="metadata"><div><span>Artery mask</span><strong>{analysis.artery_pixels.toLocaleString()} px</strong></div><div><span>Suspected stenosis mask</span><strong>{analysis.stenosis_pixels.toLocaleString()} px</strong></div><div><span>Run time</span><strong>{new Date(analysis.created_at).toLocaleString()}</strong></div><div><span>Mean artery pixel score</span><strong>{analysis.model_scores?.artery_foreground_mean_probability == null ? "Unavailable" : `${(analysis.model_scores.artery_foreground_mean_probability * 100).toFixed(1)}%`}</strong></div><div><span>Mean stenosis pixel score</span><strong>{analysis.model_scores?.stenosis_foreground_mean_probability == null ? "Unavailable" : `${(analysis.model_scores.stenosis_foreground_mean_probability * 100).toFixed(1)}%`}</strong></div></div><p className="caption">{analysis.interpretation} Mean foreground scores are uncalibrated pixel probabilities, not diagnostic confidence.</p></>}
          {analysis && <section className="explainability-guide" aria-labelledby="explainability-guide-title"><div><p className="eyebrow">EXPLAINABILITY</p><h4 id="explainability-guide-title">Evidence guide</h4><p className="caption">Choose a stored evidence lens. This helper only directs you to saved model outputs and does not use an external AI service.</p></div><SelectAIAgent agents={evidenceAgents} placeholder="Ask about the displayed evidence" contextLabel="Saved analysis only · research use" onSendMessage={(question, lens) => showEvidenceGuide(question, lens)} /><ContextualAIBar musicIcon={<Layers3 size={18} aria-hidden="true" />} sparkleIcon={<Sparkles size={18} aria-hidden="true" />} tools={[<button type="button" aria-label="Show AI overlay" onClick={() => { setMode("overlay"); setEvidenceGuide("Showing the saved segmentation overlay. Compare its edges with the original image."); }}><Layers3 size={18} aria-hidden="true" /></button>, <button type="button" aria-label="Show Grad-CAM" onClick={() => { setMode("gradcam"); setEvidenceGuide("Showing the saved Grad-CAM layer when available. It is a research saliency map, not a clinical explanation."); }}><Sparkles size={18} aria-hidden="true" /></button>]} placeholder="Ask how to inspect this evidence" compactLabel="Evidence layers" expandedLabel="Ask about stored evidence" onSubmit={(question) => showEvidenceGuide(question, "segmentation")} /><QuickSwitcher askIcon={<Eye size={20} aria-hidden="true" />} generateIcon={<GitBranch size={20} aria-hidden="true" />} askLabel="Inspect saliency" generateLabel="Inspect vessel graph" onActionClick={(action, question) => showEvidenceGuide(question, action === "ask" ? "stenosis" : "vessel_graph")} />{evidenceGuide && <p className="message success" role="status">{evidenceGuide}</p>}</section>}
          {analysis?.vessel_analysis && <>
            <div className="metadata"><div><span>Centerline length</span><strong>{analysis.vessel_analysis.centerline_length.toLocaleString()} {analysis.vessel_analysis.diameter_unit}</strong></div><div><span>Mean diameter</span><strong>{analysis.vessel_analysis.mean_diameter == null ? "Unavailable" : `${analysis.vessel_analysis.mean_diameter} ${analysis.vessel_analysis.diameter_unit}`}</strong></div><div><span>Diameter range (10–90%)</span><strong>{analysis.vessel_analysis.minimum_diameter == null || analysis.vessel_analysis.maximum_diameter == null ? "Unavailable" : `${analysis.vessel_analysis.minimum_diameter}–${analysis.vessel_analysis.maximum_diameter} ${analysis.vessel_analysis.diameter_unit}`}</strong></div><div><span>Projected mask area</span><strong>{analysis.vessel_analysis.projected_mask_area?.toLocaleString() ?? "Unavailable"} {analysis.vessel_analysis.area_unit}</strong></div><div><span>Cross-sectional area</span><strong>{analysis.vessel_analysis.cross_section_area == null ? "Needs 3D scan" : `${analysis.vessel_analysis.cross_section_area} ${analysis.vessel_analysis.area_unit}`}</strong></div><div><span>Branch points / endpoints</span><strong>{analysis.vessel_analysis.branching_points ?? "—"} / {analysis.vessel_analysis.endpoints ?? "—"}</strong></div><div><span>Continuity / tortuosity</span><strong>{analysis.vessel_analysis.continuity_ratio?.toFixed(2) ?? "Unavailable"} / {analysis.vessel_analysis.tortuosity?.toFixed(2) ?? "Unavailable"}</strong></div><div><span>Connected candidates</span><strong>{analysis.vessel_analysis.connected_components}</strong></div><div><span>Boundary length</span><strong>{analysis.vessel_analysis.boundary_length?.toLocaleString() ?? "Unavailable"} {analysis.vessel_analysis.diameter_unit}</strong></div><div><span>Diameter variation (CV)</span><strong>{analysis.vessel_analysis.diameter_cv?.toFixed(3) ?? "Unavailable"}</strong></div></div>
            <div className="metadata"><div><span>Centerline paths</span><strong>{analysis.vessel_analysis.centerline_paths?.length ?? "Unavailable"}</strong></div><div><span>Topology review</span><strong>{analysis.vessel_analysis.quality_status?.replaceAll("_", " ") ?? "Unavailable"}</strong></div><div><span>Near-threshold pixels</span><strong>{analysis.vessel_analysis.uncertain_pixel_fraction == null ? "Unavailable" : `${(analysis.vessel_analysis.uncertain_pixel_fraction * 100).toFixed(1)}%`}</strong></div></div>
            {analysis.vessel_analysis.threshold_sensitivity?.evaluations?.length ? <div className="vessel-candidates"><strong>Centerline threshold sensitivity · reference {analysis.vessel_analysis.threshold_sensitivity.reference_threshold.toFixed(2)}</strong><ul>{analysis.vessel_analysis.threshold_sensitivity.evaluations.map((row) => <li key={row.threshold}>Threshold {row.threshold.toFixed(2)} · mask Dice {row.mask_dice_vs_selected.toFixed(2)} · {row.path_count} paths · {row.branch_points} junctions</li>)}</ul><p className="caption">Status: {analysis.vessel_analysis.threshold_sensitivity.status.replaceAll("_", " ")}. The Dice comparison is against the selected-threshold mask, not a ground-truth score.</p></div> : null}
            {!!analysis.vessel_analysis.vessel_candidates?.length && <div className="vessel-candidates"><strong>Largest connected vessel candidates</strong><ul>{analysis.vessel_analysis.vessel_candidates.slice(0, 5).map((candidate) => <li key={candidate.candidate_id}>Candidate {candidate.candidate_id}: {candidate.mask_pixels.toLocaleString()} mask px · {candidate.centerline_length} {candidate.length_unit} centerline</li>)}</ul></div>}
            {!!analysis.vessel_analysis.centerline_paths?.length && <div className="vessel-candidates"><strong>Extracted path segments</strong><ul>{analysis.vessel_analysis.centerline_paths.slice(0, 8).map((path) => <li key={path.path_id}>{path.path_id} · {path.start_node || path.path_type} → {path.end_node || path.path_type} · {path.length} {path.length_unit}</li>)}</ul></div>}
            {!!analysis.vessel_analysis.quality_flags?.length && <div className="vessel-candidates"><strong>Segmentation and graph quality checks</strong><ul>{analysis.vessel_analysis.quality_flags.map((flag) => <li key={flag.code}>{flag.message}</li>)}</ul></div>}
          </>}
          <p className="privacy-note">Connected components are candidate regions, not validated anatomical artery identities. Branching, continuity, tortuosity, boundary, projected area, and diameter are approximate measurements from a 2D predicted mask. Cross-sectional area needs a 3D scan; physical units require valid source spacing.</p>
          <Button type="button" variant="outline" onClick={onReports}><FileText size={16} aria-hidden="true" /> View report</Button>
        </Card>
      </div>
      {analysis && <Card><ResultEvidence result={analysis.structured_result} /></Card>}
      <AnalysisHistory imageId={selectedImage.id} token={token} history={history} onSelect={onSelectAnalysis} />
    </>}
  </div>;
}
