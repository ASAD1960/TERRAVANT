import { forwardRef, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from "react";

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-forest sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}

export function Banner({ kind = "info", children }: { kind?: "info" | "warn" | "error"; children: ReactNode }) {
  const tone = kind === "error" ? "border-danger bg-danger/10 text-danger" : kind === "warn" ? "border-amber bg-amber/15 text-charcoal" : "border-leaf bg-soft text-forest";
  return <div role={kind === "error" ? "alert" : "status"} className={`rounded-md border-l-4 px-4 py-3 text-sm ${tone}`}>{children}</div>;
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return <div role="status" aria-live="polite" className="py-10 text-center text-sm text-muted">{label}…</div>;
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return <div className="rounded-md border border-dashed border-forest/30 px-6 py-10 text-center"><p className="font-semibold">{title}</p>{children && <div className="mt-2 text-sm text-muted">{children}</div>}</div>;
}

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> { label: string; error?: string; hint?: string }
export const TextField = forwardRef<HTMLInputElement, FieldProps>(function TextField({ label, error, hint, id, ...rest }, ref) {
  const fid = id ?? `f-${label.replace(/\W+/g, "-").toLowerCase()}`;
  return (
    <div>
      <label htmlFor={fid} className="label">{label}</label>
      <input id={fid} ref={ref} className="input" aria-invalid={!!error} aria-describedby={error ? `${fid}-e` : hint ? `${fid}-h` : undefined} {...rest} />
      {error ? <p id={`${fid}-e`} className="err">{error}</p> : hint ? <p id={`${fid}-h`} className="hint">{hint}</p> : null}
    </div>
  );
});

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> { label: string; error?: string; options: { value: string; label: string }[] }
export const SelectField = forwardRef<HTMLSelectElement, SelectProps>(function SelectField({ label, error, options, id, "aria-describedby": describedBy, ...rest }, ref) {
  const fid = id ?? `s-${label.replace(/\W+/g, "-").toLowerCase()}`;
  const errorId = `${fid}-e`;
  const describedByValue = [describedBy, error ? errorId : undefined].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label htmlFor={fid} className="label">{label}</label>
      <select id={fid} ref={ref} className="input" aria-invalid={!!error} aria-describedby={describedByValue} {...rest}>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      {error && <p id={errorId} className="err">{error}</p>}
    </div>
  );
});

export function ConfidenceBar({ value, label }: { value: number; label: string }) {
  const w = Math.round(value * 100);
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm"><span>{label}</span><span className="font-semibold tabular-nums">{w}%</span></div>
      <div className="h-2 overflow-hidden rounded-full bg-soft" role="progressbar" aria-valuenow={w} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className="h-full rounded-full bg-forest" style={{ width: `${w}%` }} />
      </div>
    </div>
  );
}

export function Limitations({ items, source, version }: { items: string[]; source: string; version: string }) {
  return (
    <div className="mt-6 space-y-2 border-t border-forest/15 pt-4 text-xs text-muted">
      {source.startsWith("synthetic") && <Banner kind="warn"><strong>Demonstration model.</strong> Trained on synthetic data, not real agronomic data. Do not use for real decisions.</Banner>}
      <ul className="list-disc space-y-1 pl-5">{items.map((l) => <li key={l}>{l}</li>)}</ul>
      <p>Model version {version} · data: {source}</p>
    </div>
  );
}
