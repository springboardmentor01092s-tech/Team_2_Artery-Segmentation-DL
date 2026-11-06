import type { AnalysisResult } from './caseTypes';

export type SavedRunPin = { imageId: string; runId: string };

// A requested historical run must never silently become a different result.
export function savedRunForImage(items: AnalysisResult[], imageId: string, runId: string | null) {
  return items.find(item => item.image_id === imageId && (!runId || item.id === runId)) || null;
}

export function pinnedRunForImage(items: AnalysisResult[], imageId: string, pin: SavedRunPin | null) {
  return savedRunForImage(items, imageId, pin?.imageId === imageId ? pin.runId : null);
}

export function savedImageForRequest<T extends { id: string }>(images: T[], imageId: string | null, runId: string | null) {
  // A historical run link needs an explicit image. Legacy case-only links may
  // still open the newest image, but never substitute for a missing image ID.
  return imageId ? images.find(item => item.id === imageId) : runId ? undefined : images.at(-1);
}

export function clearAnalysisLocation(href: string) {
  const url = new URL(href);
  for (const key of ['case_id', 'image_id', 'run_id']) url.searchParams.delete(key);
  return url.pathname + url.search + url.hash;
}

export function analysisLocation(href: string, caseId: string, imageId: string, runId: string) {
  const url = new URL(href);
  url.searchParams.set('case_id', caseId);
  url.searchParams.set('image_id', imageId);
  url.searchParams.set('run_id', runId);
  return url.pathname + url.search + url.hash;
}
