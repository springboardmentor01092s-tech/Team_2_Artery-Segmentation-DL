import { useSyncExternalStore } from "react";

export const designOptions = [
  { id: "existing", label: "Existing" },
  { id: "apple", label: "Apple-inspired" },
  { id: "editorial", label: "Editorial Focus" },
  { id: "journal", label: "Journal" },
  { id: "paper", label: "Paper" },
  { id: "atlas", label: "Atlas" },
] as const;
export type DesignVariant = typeof designOptions[number]["id"];
const requested = new URLSearchParams(window.location.search).get("design");
export let designVariant: DesignVariant = designOptions.find(option => option.id === requested)?.id || "existing";
const eventName = "corovision-design-change";
const preferenceKey = (userId: string) => `corovision-design:${userId}`;
export function applyDesign(design: DesignVariant) {
designVariant = design;
// Reuse the isolated accessible layout foundation for alternate designs.
document.documentElement.dataset.design = designVariant === "existing" ? "existing" : "apple";
document.documentElement.dataset.preview = designVariant;
document.documentElement.dataset.editorial = ["editorial", "journal", "paper", "atlas"].includes(designVariant) ? "true" : "false";
window.dispatchEvent(new Event(eventName));
}
applyDesign(designVariant);
export function restoreUserDesign(userId?: string) {
  const preview = new URLSearchParams(window.location.search).get("design");
  if (designOptions.some(option => option.id === preview)) {
    applyDesign(preview as DesignVariant);
    return;
  }
  let saved: string | null = null;
  try { if (userId) saved = localStorage.getItem(preferenceKey(userId)); } catch { /* Storage may be disabled. */ }
  applyDesign(designOptions.find(option => option.id === saved)?.id || "existing");
}
export function saveUserDesign(userId: string, design: DesignVariant) {
  localStorage.setItem(preferenceKey(userId), design);
  const url = new URL(window.location.href);
  url.searchParams.delete("design");
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  applyDesign(design);
}
function subscribe(listener: () => void) {
  window.addEventListener(eventName, listener);
  return () => window.removeEventListener(eventName, listener);
}
export function useDesignVariant() {
  return useSyncExternalStore(subscribe, () => designVariant);
}
export function designPreviewUrl(design: DesignVariant) {
  const url = new URL(window.location.href);
  url.searchParams.set("design", design);
  return `${url.pathname}${url.search}${url.hash}`;
}
