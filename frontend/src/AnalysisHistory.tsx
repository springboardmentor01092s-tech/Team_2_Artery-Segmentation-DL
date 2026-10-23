import { useEffect, useState } from "react";
import { request } from "./api";
import type { AnalysisResult } from "./caseTypes";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";

type Comparison = {
  left: AnalysisResult;
  right: AnalysisResult;
  difference: { artery_pixels: number; stenosis_pixels: number };
  interpretation: string;
};

export default function AnalysisHistory({ imageId, token, history, onSelect }: {
  imageId: string;
  token: string;
  history: AnalysisResult[];
  onSelect: (result: AnalysisResult) => void;
}) {
  const [leftId, setLeftId] = useState("");
  const [rightId, setRightId] = useState("");
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setLeftId(history[1]?.id || history[0]?.id || "");
    setRightId(history[0]?.id || "");
    setComparison(null);
    setError("");
  }, [imageId, history.length]);

  async function compare() {
    if (!leftId || !rightId || leftId === rightId) return;
    setBusy(true);
    setError("");
    try {
      const result = await request<Comparison>(`/api/images/${imageId}/analysis/compare?left_id=${encodeURIComponent(leftId)}&right_id=${encodeURIComponent(rightId)}`, token);
      setComparison(result);
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }

  return <Card className="panel analysis-history">
    <div className="viewer-heading"><h3>Analysis history</h3><span>{history.length} run{history.length === 1 ? "" : "s"}</span></div>
    {history.length === 0 ? <p className="muted">Run analysis to start this image’s history.</p> : <>
      <div className="history-list">{history.map((item) => <div className="history-row" key={item.id}>
        <div><strong>{new Date(item.created_at).toLocaleString()}</strong><small>{item.model_version} · artery {item.artery_pixels.toLocaleString()} px · stenosis {item.stenosis_pixels.toLocaleString()} px</small></div>
        <Button type="button" variant="outline" onClick={() => onSelect(item)}>View overlay</Button>
      </div>)}</div>
      {history.length >= 2 && <div className="compare-controls">
        <label>Earlier run<select value={leftId} onChange={(event) => setLeftId(event.target.value)}>{history.map((item) => <option key={item.id} value={item.id}>{new Date(item.created_at).toLocaleString()} · {item.model_version}</option>)}</select></label>
        <label>Later run<select value={rightId} onChange={(event) => setRightId(event.target.value)}>{history.map((item) => <option key={item.id} value={item.id}>{new Date(item.created_at).toLocaleString()} · {item.model_version}</option>)}</select></label>
        <Button type="button" variant="outline" onClick={compare} disabled={busy || leftId === rightId}>{busy ? "Comparing…" : "Compare runs"}</Button>
      </div>}
      {error && <p className="message error" role="alert">{error}</p>}
      {comparison && <div className="comparison-result" role="status">
        <strong>Difference from earlier to later run</strong>
        <p>Artery mask: {comparison.difference.artery_pixels >= 0 ? "+" : ""}{comparison.difference.artery_pixels.toLocaleString()} pixels · Stenosis mask: {comparison.difference.stenosis_pixels >= 0 ? "+" : ""}{comparison.difference.stenosis_pixels.toLocaleString()} pixels</p>
        <small>{comparison.interpretation}</small>
      </div>}
    </>}
  </Card>;
}
