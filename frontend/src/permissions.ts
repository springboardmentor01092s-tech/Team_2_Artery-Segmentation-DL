export const CASE_ROLES = ["admin", "doctor", "clinician", "researcher", "technician", "viewer"];
export const CASE_CREATORS = ["admin", "doctor", "clinician", "researcher", "technician"];
export const MODEL_ROLES = ["admin", "researcher", "ml_engineer"];
export const EXPORT_ROLES = ["admin", "doctor", "clinician", "researcher"];

export const canReadCases = (role?: string) => !!role && CASE_ROLES.includes(role);
export const canCreateCases = (role?: string, permissions?: string[]) => permissions ? permissions.includes("case:create") : !!role && CASE_CREATORS.includes(role);
export const canViewModels = (role?: string) => !!role && MODEL_ROLES.includes(role);
export const canExportReports = (role?: string) => !!role && EXPORT_ROLES.includes(role);

/** Navigation policy mirrors backend capabilities; never grants API access. */
export function canOpenSection(view: string, role?: string, permissions?: string[]): boolean {
  if (view === "overview" || view === "account") return !!role;
  if (["admin", "permissions", "access", "audit"].includes(view)) return role === "admin";
  if (view === "reviews") return role === "doctor" || role === "clinician" || role === "admin";
  if (view === "uploads") return role === "researcher" || role === "technician" || role === "admin";
  if (view === "models") return canViewModels(role);
  if (!["cases", "analysis", "reports"].includes(view)) return false;
  if (role === "viewer") return view === "cases";
  if (role === "admin") return true;
  return canReadCases(role);
}
