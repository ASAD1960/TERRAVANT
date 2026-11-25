export const pct = (v: number) => `${Math.round(v * 100)}%`;
export const titleCase = (s: string) => s.replace(/[_-]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
export const dateShort = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
export const num = (v: number | null | undefined, digits = 1) => (v === null || v === undefined || Number.isNaN(v) ? "—" : v.toFixed(digits));
