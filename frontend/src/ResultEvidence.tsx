import type { StructuredResearchResult } from "./caseTypes";

function record(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
function text(value: unknown): string { return typeof value === 'string' && value.trim() ? value : 'Not recorded'; }
function threshold(value: unknown): string { return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 ? String(value) : 'Not recorded'; }

export default function ResultEvidence({ result }: { result?: StructuredResearchResult | null }) {
  if (!result) return <p className="caption">This historical analysis has no versioned explanation document. Its original measurements remain unchanged.</p>;
  const operatingPoint = record(result.models?.operating_point);
  const methods = record(result.models?.explainability);
  function downloadCandidates() {
    if (!result) return;
    const blob = new Blob([JSON.stringify({ schema_version: 'corovision.stenosis-candidates.v1',
      result_id: result.result_id, model: result.models, coordinate_convention: 'pixel_edges_xyxy_half_open',
      candidates: result.candidates, interpretation: 'Model candidates; scores are not clinical severity.' }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = 'stenosis-candidates.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section aria-label="Saved analysis evidence" className="vessel-candidates">
    <h3>Saved analysis evidence</h3>
    <p className="caption">{result.schema_version} · result {result.result_id} · {result.explanation.method.replaceAll("_", " ")}</p>
    <ul>{Object.entries(result.stages).map(([stage, value]) => <li key={stage}>
      <strong>{stage.replaceAll("_", " ")}: {value.status.replaceAll("_", " ")}</strong> — {value.reason}
    </li>)}</ul>
    <h4>Model-detected candidates</h4>
    <button type="button" onClick={downloadCandidates} disabled={!result.candidates.length}>Download candidate locations</button>
    {result.candidates.length ? <ul>{result.candidates.map((candidate) => <li key={candidate.candidate_id}>
      <strong>{candidate.candidate_id}</strong> · raw score {candidate.model_score == null ? "Unavailable" : candidate.model_score.toFixed(4)}
      <br />Prepared-image mask bounds (x1,y1,x2,y2): {candidate.bbox_prepared_xyxy?.join(", ") || "Unavailable"}
      <br />Source-image bounds: {candidate.bbox_source_xyxy?.map((x) => x.toFixed(2)).join(", ") || "Unavailable"}
      {candidate.coordinate_warning && <p>{candidate.coordinate_warning}</p>}
      <p>Vessel-segment association: {candidate.association_status?.replaceAll("_", " ") || "Not assessed"}. Candidate scores are not patient disease probabilities.</p>
    </li>)}</ul> : <p>No localized candidate list is available. Read the saved detection explanation below.</p>}
    <h4>Detection operating point</h4>
    <p>Profile: {text(operatingPoint.profile)} · Detection score threshold: {threshold(operatingPoint.stenosis_score_threshold)} · Mask threshold: {threshold(operatingPoint.stenosis_mask_threshold)}</p>
    <p className="caption">Saved application settings apply to this run. A research comparison with a different operating point does not establish performance for this profile.</p>
    <h4>Explainable AI evidence</h4>
    {Object.keys(methods).length ? <ul>{Object.entries(methods).map(([name, raw]) => {
      const method = record(raw);
      return <li key={name}><strong>{name}: {text(method.status)}</strong>
        <p>Method: {text(method.method)} · Target: {text(method.target)} · Layer: {text(method.layer)}</p>
        <p>{text(method.reason)}</p>
        <small>Faithfulness evidence: {method.faithfulness_validated === true ? 'Recorded as validated; inspect the linked method evidence.' : 'Not validated for this saved result.'}</small>
      </li>;
    })}</ul> : <p>No method-specific attribution evidence was saved. A probability overlay alone does not establish an explanation.</p>}
    <h4>Severity: Not assessed — insufficient evidence</h4><p>{result.severity.reason}</p>
    {result.explanation.sections.map((section) => <div key={section.title}>
      <h4>{section.title}</h4><p>{section.text}</p><small>Evidence fields: {section.source_refs.join(", ")}</small>
    </div>)}
  </section>;
}
