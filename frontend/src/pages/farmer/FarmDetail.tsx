import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { z } from "zod";
import { Banner, Empty, PageHeader, Spinner, TextField } from "../../components/common/ui";
import { api } from "../../services/api";
import type { FarmDetail as FD } from "../../types";
import { dateShort, num } from "../../utils/format";
import { fieldSchema } from "../../utils/schemas";

type Form = z.input<typeof fieldSchema>;
interface Soil { id: string; nitrogen: number | null; phosphorus: number | null; potassium: number | null; ph: number | null; recorded_at: string }

function SoilPanel({ fieldId }: { fieldId: string }) {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["soil", fieldId], queryFn: () => api<Soil[]>(`/fields/${fieldId}/soil`) });
  const [vals, setVals] = useState({ nitrogen: "", phosphorus: "", potassium: "", ph: "" });
  const add = useMutation({
    mutationFn: () => api(`/fields/${fieldId}/soil`, { json: Object.fromEntries(Object.entries(vals).map(([k, v]) => [k, v === "" ? null : Number(v)])) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["soil", fieldId] }); setVals({ nitrogen: "", phosphorus: "", potassium: "", ph: "" }); },
  });
  return (
    <div className="mt-4 border-l-2 border-leaf pl-4">
      <p className="text-sm font-semibold">Soil tests</p>
      {data?.length ? (
        <table className="mt-2 w-full text-sm"><thead className="text-left text-xs text-muted"><tr><th className="py-1 font-medium">Date</th><th className="font-medium">N</th><th className="font-medium">P</th><th className="font-medium">K</th><th className="font-medium">pH</th></tr></thead>
          <tbody>{data.slice(0, 3).map((s) => <tr key={s.id} className="tabular-nums"><td className="py-1">{dateShort(s.recorded_at)}</td><td>{num(s.nitrogen)}</td><td>{num(s.phosphorus)}</td><td>{num(s.potassium)}</td><td>{num(s.ph, 2)}</td></tr>)}</tbody></table>
      ) : <p className="text-sm text-muted">No soil tests recorded.</p>}
      <form className="mt-3 grid grid-cols-2 items-end gap-3 sm:grid-cols-5" aria-busy={add.isPending} onSubmit={(e) => { e.preventDefault(); add.mutate(); }}>
        {(["nitrogen", "phosphorus", "potassium", "ph"] as const).map((k) => (
          <TextField key={k} label={k === "ph" ? "pH" : k[0].toUpperCase() + k.slice(1)} type="number" step="any" min={0} value={vals[k]} onChange={(e) => setVals({ ...vals, [k]: e.target.value })} id={`${fieldId}-${k}`} />
        ))}
        <button type="submit" className="btn-quiet" disabled={add.isPending || Object.values(vals).every((v) => v === "")}>Add test</button>
      </form>
      {add.error && <p className="err">{(add.error as Error).message}</p>}
      <p className="hint">N, P, K in mg/kg from a laboratory report.</p>
    </div>
  );
}

export default function FarmDetail() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["farm", id], queryFn: () => api<FD>(`/farms/${id}`) });
  const { register, handleSubmit, reset, formState: { errors } } = useForm<Form>({ resolver: zodResolver(fieldSchema) });
  const addField = useMutation({
    mutationFn: (v: Form) => api("/fields", { json: { farm_id: id, ...v, soil_type: v.soil_type || null, area: v.area ?? null, latitude: v.latitude ?? null, longitude: v.longitude ?? null } }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["farm", id] }); qc.invalidateQueries({ queryKey: ["fields"] }); reset(); },
  });
  const del = useMutation({ mutationFn: () => api(`/farms/${id}`, { method: "DELETE" }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["farm", id] }); qc.invalidateQueries({ queryKey: ["farms"] }); qc.invalidateQueries({ queryKey: ["dashboard"] }); nav("/app/farms"); } });

  if (isLoading) return <Spinner />;
  if (error || !data) return <Banner kind="error">{(error as Error | null)?.message ?? "Farm not found."}</Banner>;
  return (
    <>
      <p className="mb-3 text-sm"><Link className="font-semibold text-forest underline" to="/app/farms">← All farms</Link></p>
      <PageHeader title={data.farm_name} subtitle={[data.location, data.area ? `${data.area} ${data.area_unit}` : null].filter(Boolean).join(" · ")}
        action={<button type="button" aria-busy={del.isPending} disabled={del.isPending} className="btn-quiet !border-danger !text-danger hover:!bg-danger/10" onClick={() => { if (window.confirm(`Delete ${data.farm_name} and all its fields? This cannot be undone.`)) del.mutate(); }}>Delete farm</button>} />
      <h2 className="mb-3 text-lg font-bold">Fields</h2>
      {data.fields.length === 0 ? <Empty title="No fields yet">Add a field below. Add coordinates to get a field-specific weather forecast.</Empty> : (
        <ul className="space-y-8">
          {data.fields.map((f) => (
            <li key={f.id}>
              <div className="flex flex-wrap items-baseline justify-between gap-2"><span className="font-bold text-forest">{f.field_name}</span>
                <span className="text-sm text-muted">{[f.area ? `${f.area} area units` : null, f.soil_type, f.latitude != null ? `${f.latitude}, ${f.longitude}` : "no coordinates"].filter(Boolean).join(" · ")}</span></div>
              <SoilPanel fieldId={f.id} />
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={handleSubmit((v) => addField.mutate(v))} aria-busy={addField.isPending} className="section-rule mt-10 grid gap-5 sm:grid-cols-2" noValidate>
        <h2 className="text-lg font-bold sm:col-span-2">Add a field</h2>
        {addField.error && <div className="sm:col-span-2"><Banner kind="error">{(addField.error as Error).message}</Banner></div>}
        <TextField label="Field name" {...register("field_name")} error={errors.field_name?.message} />
        <TextField label="Area" type="number" step="any" {...register("area")} error={errors.area?.message as string | undefined} />
        <TextField label="Soil type" placeholder="e.g. loam, clay loam" {...register("soil_type")} />
        <div className="grid grid-cols-2 gap-3">
          <TextField label="Latitude" type="number" step="any" {...register("latitude")} error={errors.latitude?.message as string | undefined} />
          <TextField label="Longitude" type="number" step="any" {...register("longitude")} error={errors.longitude?.message as string | undefined} />
        </div>
        <div className="sm:col-span-2"><button type="submit" className="btn" disabled={addField.isPending}>Save field</button></div>
      </form>
    </>
  );
}
