/** The API stores UTC timestamps without a zone suffix; treat those as UTC so the browser shows local time. */
export function utcDate(value: string | number | Date | null | undefined): Date {
  if (value instanceof Date || typeof value === "number") return new Date(value);
  if (!value) return new Date(NaN);
  return new Date(/[zZ]$|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`);
}
