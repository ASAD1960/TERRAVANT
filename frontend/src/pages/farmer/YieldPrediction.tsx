import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import type { z } from "zod";
import { Banner, Limitations, PageHeader, SelectField, TextField } from "../../components/common/ui";
import { useCrops, useFields } from "../../hooks/queries";
import { api } from "../../services/api";
import type { YieldResult } from "../../types";
import { titleCase } from "../../utils/format";
import { yieldSchema } from "../../utils/schemas";

type Form = z.input<typeof yieldSchema> & { field_id?: string };

export default function YieldPrediction() {
  const qc = useQueryClient();
  const crops = useCrops();
  const fields = useFields();
  const { register, handleSubmit, formState: { errors } } = useForm<Form>({ resolver: zodResolver(yieldSchema), defaultValues: { irrigated: true, soil_ph: 7.5 } });
  const m = useMutation({ mutationFn: (v: Form) => api<YieldResult>("/predictions/yield", { json: { ...v, field_id: v.field_id || null } }), onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboard"] }) });
  const r = m.data;
  const err = (k: keyof Form) => errors[k]?.message as string | undefined;
  return (
    <>
      <PageHeader title="Yield prediction" subtitle="A rough per-hectare estimate for planning. Real yields depend on weather, pests and management." />
      <form onSubmit={handleSubmit((v) => m.mutate(v))} aria-busy={m.isPending} className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" noValidate>
        <SelectField label="Crop" {...register("crop_name")} error={err("crop_name")} options={[{ value: "", label: "Choose a crop" }, ...(crops.data ?? []).map((c) => ({ value: c.crop_name, label: titleCase(c.crop_name) }))]} />
        <TextField label="Area (hectares)" type="number" step="any" {...register("area_ha")} error={err("area_ha")} />
        <TextField label="Season rainfall (mm)" type="number" step="any" {...register("rainfall")} error={err("rainfall")} />
        <TextField label="Mean temperature (°C)" type="number" step="any" {...register("temperature")} error={err("temperature")} />
        <TextField label="Fertilizer applied (kg/ha)" type="number" step="any" {...register("fertilizer_kg_ha")} error={err("fertilizer_kg_ha")} />
        <TextField label="Soil pH" type="number" step="any" {...register("soil_ph")} error={err("soil_ph")} />
        <SelectField label="Link to field (optional)" {...register("field_id")} options={[{ value: "", label: "None" }, ...(fields.data ?? []).map((f) => ({ value: f.id, label: f.field_name }))]} />
        <label className="flex items-center gap-2 self-end pb-3 text-sm font-semibold"><input type="checkbox" className="h-4 w-4 accent-forest" {...register("irrigated")} /> Irrigated</label>
        <div className="flex items-end"><button type="submit" className="btn w-full" disabled={m.isPending}>{m.isPending ? "Estimating…" : "Estimate yield"}</button></div>
      </form>
      <div className="mt-10" aria-live="polite">
        {m.error && <Banner kind={(m.error as { status?: number }).status === 503 ? "warn" : "error"}>{(m.error as Error).message}</Banner>}
        {r && (
          <section className="section-rule">
            <p className="text-sm text-muted">{titleCase(r.crop_name)}, estimated</p>
            <p className="text-4xl font-extrabold tabular-nums text-forest">{r.yield_per_ha.toFixed(2)} <span className="text-lg font-semibold">{r.yield_unit}</span></p>
            <p className="mt-1 text-sm">Likely range {r.yield_low.toFixed(2)}–{r.yield_high.toFixed(2)} {r.yield_unit} · Total about <strong>{r.total_production.toFixed(1)} t</strong></p>
            <p className="mt-2 text-xs text-muted">{r.interval_note}</p>
            <Limitations items={r.limitations} source={r.data_source} version={r.model_version} />
          </section>
        )}
      </div>
    </>
  );
}
