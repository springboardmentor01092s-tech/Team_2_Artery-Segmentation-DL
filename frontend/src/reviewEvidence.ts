import type { AnalysisResult, ClinicalReviewRecord } from './caseTypes';

export function runForImage(imageId: string | undefined, result: AnalysisResult | null) {
  return result?.image_id === imageId ? result : null;
}

export function reviewsForRun(reviews: ClinicalReviewRecord[], runId?: string) {
  return runId ? reviews.filter(review => review.analysis_event_id === runId) : [];
}

export function candidateViewport(box: number[] | undefined, width: number, height: number) {
  if (!box || box.length !== 4 || !box.every(Number.isFinite) || width <= 0 || height <= 0) return null;
  const [x1, y1, x2, y2] = box;
  if (x1 < 0 || y1 < 0 || x2 > 512 || y2 > 512 || x2 <= x1 || y2 <= y1) return null;
  const zoom = Math.min(5, Math.max(2, 280 / Math.max(x2 - x1, y2 - y1)));
  const scale = Math.min(width, height) / 512;
  return { zoom, offset: { x: (256 - (x1+x2)/2)*scale*zoom, y: (256 - (y1+y2)/2)*scale*zoom } };
}
