import type { StructuredResearchResult } from "./caseTypes";

export default function ResultEvidence({ result }: { result?: StructuredResearchResult | null }) {
  if (!result) return <p className="caption">This historical analysis has no versioned explanation document. Its original measurements remain unchanged.</p>;
  return <section aria-label="Saved analysis evidence" className="vessel-candidates">
    <h3>Saved analysis evidence</h3>
    <p className="caption">{result.schema_version} · result {result.result_id} · {result.explanation.method.replaceAll("_", " ")}</p>
    <ul>{Object.entries(result.stages).map(([stage, value]) => <li key={stage}>
      <strong>{stage.replaceAll("_", " ")}: {value.status.replaceAll("_", " ")}</strong> — {value.reason}
    </li>)}</ul>
    <h4>Model-detected candidates</h4>
    {result.candidates.length ? <ul>{result.candidates.map((candidate) => <li key={candidate.candidate_id}>
      <strong>{candidate.candidate_id}</strong> · raw score {candidate.model_score == null ? "Unavailable" : candidate.model_score.toFixed(4)}
      <br />Prepared-image mask bounds (x1,y1,x2,y2): {candidate.bbox_prepared_xyxy?.join(", ") || "Unavailable"}
      <br />Source-image bounds: {candidate.bbox_source_xyxy?.map((x) => x.toFixed(2)).join(", ") || "Unavailable"}
      {candidate.coordinate_warning && <p>{candidate.coordinate_warning}</p>}
      <p>Vessel-segment association: {candidate.association_status?.replaceAll("_", " ") || "Not assessed"}. Candidate scores are not patient disease probabilities.</p>
    </li>)}</ul> : <p>No localized candidate list is available. Read the saved detection explanation below.</p>}
    <h4>Severity: Not assessed — insufficient evidence</h4><p>{result.severity.reason}</p>
    {result.explanation.sections.map((section) => <div key={section.title}>
      <h4>{section.title}</h4><p>{section.text}</p><small>Evidence fields: {section.source_refs.join(", ")}</small>
    </div>)}
  </section>;
}
