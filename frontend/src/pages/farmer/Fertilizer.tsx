import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import type { z } from "zod";
import { Banner, PageHeader, SelectField, TextField } from "../../components/common/ui";
import { useCrops, useFields } from "../../hooks/queries";
import { api } from "../../services/api";
import type { FertilizerResult } from "../../types";
import { titleCase } from "../../utils/format";
import { fertilizerSchema } from "../../utils/schemas";

type Form = z.input<typeof fertilizerSchema>;
const TONE: Record<string, string> = { low: "bg-amber/25 text-charcoal", adequate: "bg-soft text-forest", high: "bg-danger/15 text-danger" };

export default function Fertilizer() {
  const crops = useCrops();
  const fields = useFields();
  const { register, handleSubmit, formState: { errors } } = useForm<Form>({ resolver: zodResolver(fertilizerSchema) });
  const m = useMutation({ mutationFn: (v: Form) => api<FertilizerResult>("/recommendations/fertilizer", { json: Object.fromEntries(Object.entries(v).map(([k, x]) => [k, x === "" ? null : x])) }) });
  const r = m.data;
  const err = (k: keyof Form) => errors[k]?.message as string | undefined;
  return (
    <>
      <PageHeader title="Fertilizer guidance" subtitle="Reads your soil test and says which nutrients look low or high. It does not give application rates." />
      <form onSubmit={handleSubmit((v) => m.mutate(v))} aria-busy={m.isPending} className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" noValidate>
        <SelectField
          label="Field (optional)"
          {...register("field_id")}
          options={[
            { value: "", label: "No field selected" },
            ...(fields.data ?? []).map((f) => ({
              value: f.id,
              label: f.field_name,
            })),
          ]}
        />
        <SelectField label="Crop" {...register("crop_name")} error={err("crop_name")} options={[{ value: "", label: "Choose a crop" }, ...(crops.data ?? []).map((c) => ({ value: c.crop_name, label: titleCase(c.crop_name) }))]} />
        <TextField label="Nitrogen (mg/kg)" hint="Leave blank if not tested" type="number" step="any" {...register("nitrogen")} error={err("nitrogen")} />
        <TextField label="Phosphorus (mg/kg)" type="number" step="any" {...register("phosphorus")} error={err("phosphorus")} />
        <TextField label="Potassium (mg/kg)" type="number" step="any" {...register("potassium")} error={err("potassium")} />
        <TextField label="Soil pH" type="number" step="any" {...register("ph")} error={err("ph")} />
        <SelectField
          label="Growth stage (optional)"
          {...register("growth_stage")}
          options={[
            { value: "", label: "Choose growth stage" },
            { value: "sowing", label: "Sowing" },
            { value: "vegetative", label: "Vegetative" },
            { value: "flowering", label: "Flowering" },
            { value: "fruiting", label: "Fruiting" },
            { value: "maturity", label: "Maturity" },
            { value: "harvest", label: "Harvest" },
          ]}
/>
        <div className="sm:col-span-2 lg:col-span-3"><button type="submit" className="btn" disabled={m.isPending}>{m.isPending ? "Checking…" : "Get guidance"}</button></div>
      </form>
      <div className="mt-10" aria-live="polite">
        {m.error && <Banner kind="error">{(m.error as Error).message}</Banner>}
        {r && (
          <section className="section-rule space-y-6">
            {r.needs_lab_test && <Banner kind="warn"><strong>Get a laboratory soil test before acting.</strong><ul className="mt-1 list-disc pl-5">{r.lab_test_reasons.map((x) => <li key={x}>{x}</li>)}</ul></Banner>}
            {Object.keys(r.nutrient_status).length > 0 && (
              <dl className="grid grid-cols-3 gap-4">
                {Object.entries(r.nutrient_status).map(([k, v]) => (
                  <div key={k}><dt className="text-sm text-muted">{titleCase(k)}</dt><dd className="mt-1 text-2xl font-extrabold tabular-nums">{v.value}</dd><dd><span className={`mt-1 inline-block rounded px-2 py-0.5 text-xs font-bold ${TONE[v.status]}`}>{titleCase(v.status)}</span></dd></div>
                ))}
              </dl>
            )}
            <div><h2 className="font-bold">Guidance for {titleCase(r.crop_name)}</h2><ul className="mt-2 list-disc space-y-2 pl-5 text-sm">{r.guidance.map((g) => <li key={g}>{g}</li>)}</ul></div>
            <p className="border-t border-forest/15 pt-4 text-xs text-muted">{r.disclaimer} Rules v{r.ruleset_version}.</p>
          </section>
        )}
      </div>
    </>
  );
}
