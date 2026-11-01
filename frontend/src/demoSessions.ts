import type { User } from "./AccountPanel";

export const KEY = "corovision-local-demo-accounts";

export type SavedAccount = { id: string; name: string; email: string; role: string; token: string; label?: string };

/** Keep Doctor and Clinician distinct; deduplicate demo choices within each role only. */
export function demoAccountChoices(accounts: SavedAccount[], currentRole?: string): SavedAccount[] {
  const canonical = (role: string) => role;
  const seen = new Set<string>();
  if (currentRole) seen.add(canonical(currentRole));
  return [...accounts].sort((a, b) => Number(b.email === "doctor.demo@example.com") - Number(a.email === "doctor.demo@example.com"))
    .filter(account => {
      if (/demo institutional/i.test(account.name)) return false;
      if (!/\.demo@example\.com$/i.test(account.email)) return true;
      const role = canonical(account.role);
      if (seen.has(role)) return false;
      seen.add(role);
      return true;
    });
}

export const localDemo =
  typeof window !== "undefined" &&
  (["localhost", "127.0.0.1", "0.0.0.0", "::1"].includes(window.location.hostname) ||
    window.location.hostname.startsWith("192.168.") ||
    window.location.hostname.startsWith("10.") ||
    window.location.hostname.endsWith(".local") ||
    window.location.port === "5173" ||
    window.location.port === "8000");


export function savedAccounts(): SavedAccount[] {
  if (!localDemo) return [];
  try {
    const items: unknown = JSON.parse(localStorage.getItem(KEY) || "[]");
    if (!Array.isArray(items)) return [];
    return items.filter((item): item is SavedAccount =>
      !!item && typeof item === "object" &&
      typeof item.id === "string" && typeof item.token === "string" &&
      typeof item.email === "string" && typeof item.role === "string" && typeof item.name === "string");
  } catch { return []; }
}

export function saveDemoAccounts(accounts: SavedAccount[]): SavedAccount[] {
  if (!localDemo) return [];
  const existing = savedAccounts();
  const map = new Map(existing.map((a) => [a.email, a]));
  for (const acc of accounts) {
    if (!map.has(acc.email)) {
      existing.push(acc);
      map.set(acc.email, acc);
    }
  }
  localStorage.setItem(KEY, JSON.stringify(existing));
  return existing;
}

export function saveAccount(user: User, token: string): SavedAccount[] {
  if (!localDemo) return [];
  const next = savedAccounts().filter((item) => item.id !== user.id);
  next.push({ id: user.id, name: user.display_name || user.username || user.email, email: user.email, role: user.role, token });
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export function forgetAccount(token: string): SavedAccount[] {
  if (!localDemo) return [];
  const next = savedAccounts().filter((item) => item.token !== token);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

