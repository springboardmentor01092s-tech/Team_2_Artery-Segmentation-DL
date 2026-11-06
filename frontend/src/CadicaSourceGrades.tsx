type Props = { taskId: string; records: unknown[] };

export default function CadicaSourceGrades({ taskId, records }: Props) {
  if (taskId !== 'cadica_grade_aware') return null;
  const grades = records.flatMap((value, index) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return [];
    const row = value as Record<string, unknown>;
    if (typeof row.source_class !== 'string' || !row.source_class.trim()) return [];
    const box = Array.isArray(row.bbox_xyxy) && row.bbox_xyxy.length === 4 && row.bbox_xyxy.every(v => typeof v === 'number' && Number.isFinite(v)) ? row.bbox_xyxy : null;
    return [{ id: typeof row.candidate_id === 'string' ? row.candidate_id : `Candidate ${index + 1}`,
      grade: row.source_class, box, score: typeof row.raw_score === 'number' && Number.isFinite(row.raw_score) && row.raw_score >= 0 && row.raw_score <= 1 ? row.raw_score : null }];
  });
  return <section aria-label="CADICA source-grade classification">
    <h4>CADICA source grades · separate research classification</h4>
    <p>Labels use the preserved checkpoint's CADICA vocabulary. They are separate from clinician-protocol categories and reviewed diameter reduction.</p>
    {grades.length ? <table><thead><tr><th>Candidate</th><th>Source grade</th><th>Raw model score</th><th>Image bounds (xyxy)</th></tr></thead>
      <tbody>{grades.map((row, index) => <tr key={`${row.id}-${index}`}><td>{row.id}</td><td>{row.grade}</td><td>{row.score === null ? 'Unavailable' : row.score.toFixed(4)}</td><td>{row.box?.map(v => v.toFixed(1)).join(', ') || 'Unavailable'}</td></tr>)}</tbody></table>
      : <p>No source-grade candidates were saved for this run. This does not establish absence of stenosis.</p>}
  </section>;
}
