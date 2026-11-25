import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import type { z } from "zod";
import { Banner, ConfidenceBar, Limitations, PageHeader, SelectField, TextField } from "../../components/common/ui";
import { useFields } from "../../hooks/queries";
import { api } from "../../services/api";
import type { CropResult } from "../../types";
import { titleCase } from "../../utils/format";
import { cropSchema } from "../../utils/schemas";

type Form = z.input<typeof cropSchema> & { field_id?: string };

const FIELDS: { k: keyof z.input<typeof cropSchema>; label: string; hint: string }[] = [
  { k: "nitrogen", label: "Nitrogen (N)", hint: "0–300" }, { k: "phosphorus", label: "Phosphorus (P)", hint: "0–300" }, { k: "potassium", label: "Potassium (K)", hint: "0–300" },
  { k: "temperature", label: "Temperature (°C)", hint: "Seasonal mean" }, { k: "humidity", label: "Humidity (%)", hint: "0–100" },
  { k: "ph", label: "Soil pH", hint: "3–11" }, { k: "rainfall", label: "Rainfall (mm)", hint: "Seasonal total" },
];

export default function CropRecommendation() {
  const qc = useQueryClient();
  const fields = useFields();
  const { register, handleSubmit, formState: { errors } } = useForm<Form>({ resolver: zodResolver(cropSchema) });
  const m = useMutation({
    mutationFn: (v: Form) => api<CropResult>("/predictions/crop", { json: { ...v, field_id: v.field_id || null } }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["dashboard"] }); },
  });
  const r = m.data;
  return (
    <>
      <PageHeader title="Crop recommendation" subtitle="Enter soil and climate readings to see which crops they most resemble." />
      <form onSubmit={handleSubmit((v) => m.mutate(v))} aria-busy={m.isPending} className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" noValidate>
        {FIELDS.map((f) => <TextField key={f.k} label={f.label} hint={f.hint} type="number" step="any" {...register(f.k)} error={errors[f.k]?.message as string | undefined} />)}
        <SelectField label="Link to field (optional)" {...register("field_id")} options={[{ value: "", label: "None" }, ...(fields.data ?? []).map((f) => ({ value: f.id, label: f.field_name }))]} />
        <div className="flex items-end"><button type="submit" className="btn w-full" disabled={m.isPending}>{m.isPending ? "Analysing…" : "Get recommendation"}</button></div>
      </form>

      <div className="mt-10" aria-live="polite">
        {m.error && <Banner kind={(m.error as { status?: number }).status === 503 ? "warn" : "error"}>{(m.error as Error).message}</Banner>}
        {r && (
          <section className="section-rule">
            <p className="text-sm text-muted">Best match</p>
            <p className="text-4xl font-extrabold text-forest">{titleCase(r.predicted_crop)}</p>
            <p className="mt-1 text-sm text-muted">Model confidence {Math.round(r.confidence * 100)}% — an estimate by the model, not a guarantee.</p>
            <div className="mt-6 grid gap-8 md:grid-cols-2">
              <div className="space-y-4"><h2 className="font-bold">Top three</h2>{r.alternatives.map((a) => <ConfidenceBar key={a.label} label={titleCase(a.label)} value={a.probability} />)}</div>
              <div><h2 className="font-bold">What mattered most</h2><p className="text-xs text-muted">{r.explanation.method}</p>
                <ul className="mt-2 divide-y divide-forest/10 text-sm">{r.explanation.top_factors.map((f) => (
                  <li key={f.feature} className="flex justify-between py-2"><span>{titleCase(f.feature)} <span className="text-muted">({f.value})</span></span><span className="tabular-nums text-muted">weight {f.importance.toFixed(2)}</span></li>))}</ul></div>
            </div>
            <Limitations items={r.limitations} source={r.data_source} version={r.model_version} />
          </section>
        )}
      </div>
    </>
  );
}
