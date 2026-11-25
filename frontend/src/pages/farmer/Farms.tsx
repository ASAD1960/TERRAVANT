import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import type { z } from "zod";
import { Banner, Empty, PageHeader, SelectField, Spinner, TextField } from "../../components/common/ui";
import { api } from "../../services/api";
import type { Farm } from "../../types";
import { farmSchema } from "../../utils/schemas";

type Form = z.input<typeof farmSchema>;

export default function Farms() {
  const qc = useQueryClient();
  const [adding, setAdding] = useState(false);
  const { data, isLoading, error } = useQuery({ queryKey: ["farms"], queryFn: () => api<Farm[]>("/farms") });
  const { register, handleSubmit, reset, formState: { errors } } = useForm<Form>({ resolver: zodResolver(farmSchema), defaultValues: { area_unit: "acre" } });
  const create = useMutation({
    mutationFn: (v: Form) => api<Farm>("/farms", { json: { ...v, location: v.location || null, area: v.area ?? null } }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["farms"] }); qc.invalidateQueries({ queryKey: ["dashboard"] }); reset(); setAdding(false); },
  });

  return (
    <>
      <PageHeader title="Farms and fields" subtitle="Register farms, divide them into fields and keep soil tests and activities per field."
        action={<button type="button" className="btn" onClick={() => setAdding((a) => !a)} aria-expanded={adding} aria-controls="farm-create-form">{adding ? "Cancel" : "Add farm"}</button>} />
      {adding && (
        <form id="farm-create-form" onSubmit={handleSubmit((v) => create.mutate(v))} aria-busy={create.isPending} className="mb-10 grid gap-5 border-b border-forest/15 pb-8 sm:grid-cols-2" noValidate>
          {create.error && <div className="sm:col-span-2"><Banner kind="error">{(create.error as Error).message}</Banner></div>}
          <TextField label="Farm name" {...register("farm_name")} error={errors.farm_name?.message} />
          <TextField label="Location" placeholder="Village, tehsil, district" {...register("location")} />
          <TextField label="Total area" type="number" step="any" {...register("area")} error={errors.area?.message as string | undefined} />
          <SelectField label="Unit" {...register("area_unit")} error={errors.area_unit?.message} options={["acre", "hectare", "kanal", "marla"].map((v) => ({ value: v, label: v }))} />
          <div className="sm:col-span-2"><button type="submit" className="btn" disabled={create.isPending}>{create.isPending ? "Saving…" : "Save farm"}</button></div>
        </form>
      )}
      {isLoading ? <Spinner /> : error ? <Banner kind="error">{(error as Error).message}</Banner> : !data?.length ? (
        <Empty title="No farms yet">Add a farm to start recording fields and soil tests.</Empty>
      ) : (
        <ul className="divide-y divide-forest/10 border-y border-forest/10">
          {data.map((f) => (
            <li key={f.id}>
              <Link to={`/app/farms/${f.id}`} className="flex items-center justify-between gap-4 px-1 py-4 hover:bg-soft">
                <span><span className="block font-bold text-forest">{f.farm_name}</span><span className="text-sm text-muted">{f.location ?? "No location set"}</span></span>
                <span className="text-sm tabular-nums">{f.area ? `${f.area} ${f.area_unit}` : "—"}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
