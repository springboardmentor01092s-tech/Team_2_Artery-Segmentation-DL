/** Actor-specific form labels; historical author identities are never relabelled. */
export function reviewLabels(role?: string) {
  const name = role === "clinician" ? "Clinician" : role === "doctor" ? "Doctor" : "Clinical Reviewer";
  return {
    title: `${name} Review & Decision`,
    decision: `${name}’s Decision`,
    severity: `${name}-assessed stenosis severity (optional)`,
    notes: `${name}’s Review Notes & Annotations`,
    submit: `Record ${name}’s Review`,
  };
}
