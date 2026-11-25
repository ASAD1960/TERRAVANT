import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Banner, PageHeader, Spinner } from "../../components/common/ui";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import type { User } from "../../types";
import { dateShort } from "../../utils/format";

interface Models { artifacts_present: Record<string, boolean>; versions: { id: string; model_name: string; version: string; model_type: string; data_source: string | null; deployment_status: string; metrics: Record<string, unknown> | null }[] }
interface Audit { id: string; action: string; resource: string | null; user_id: string | null; created_at: string; details: Record<string, unknown> | null }
const TABS = ["Users", "Models", "Audit log"] as const;

export default function Admin() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const tabs = isAdmin ? TABS : (["Models"] as const);
  const [tab, setTab] = useState<(typeof TABS)[number]>(tabs[0]);
  return (
    <>
      <PageHeader title="Administration" subtitle="Users, deployed models and security activity." />
      <div role="tablist" className="mb-8 flex gap-6 border-b border-forest/15">
        {tabs.map((t) => <button type="button" key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)} className={`-mb-px border-b-2 pb-2 text-sm font-semibold ${tab === t ? "border-forest text-forest" : "border-transparent text-muted hover:text-charcoal"}`}>{t}</button>)}
      </div>
      {tab === "Users" && <Users />}{tab === "Models" && <ModelsTab isAdmin={isAdmin} />}{tab === "Audit log" && <AuditTab />}
    </>
  );
}

function Users() {
  const qc = useQueryClient();
  const { user: me } = useAuth();
  const { data, isLoading, error } = useQuery({ queryKey: ["admin-users"], queryFn: () => api<User[]>("/admin/users") });
  const setStatus = useMutation({ mutationFn: ({ id, status }: { id: string; status: string }) => api(`/admin/users/${id}/status`, { method: "PATCH", json: { status } }), onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }) });
  if (isLoading) return <Spinner />;
  if (error) return <Banner kind="error">{(error as Error).message}</Banner>;
  return (
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs text-muted"><tr><th className="py-2 font-medium">Name</th><th className="font-medium">Email</th><th className="font-medium">Roles</th><th className="font-medium">Joined</th><th className="font-medium">Status</th></tr></thead>
      <tbody className="divide-y divide-forest/10">{data?.map((u) => (
        <tr key={u.id}><td className="py-3 font-semibold">{u.full_name}</td><td>{u.email}</td><td>{u.role_names.join(", ")}</td><td>{dateShort(u.created_at)}</td>
          <td>{u.id === me?.id ? <span className="text-muted">You</span> : <button type="button" aria-busy={setStatus.isPending} disabled={setStatus.isPending} className="btn-quiet !px-3 !py-1" onClick={() => setStatus.mutate({ id: u.id, status: u.status === "active" ? "suspended" : "active" })}>{u.status === "active" ? "Suspend" : "Reactivate"}</button>}</td></tr>))}</tbody></table>
      {setStatus.error && <p className="err">{(setStatus.error as Error).message}</p>}</div>
  );
}

function ModelsTab({ isAdmin }: { isAdmin: boolean }) {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["admin-models"], queryFn: () => api<Models>("/admin/models") });
  const setSt = useMutation({ mutationFn: ({ id, s }: { id: string; s: string }) => api(`/admin/models/${id}`, { method: "PATCH", json: { deployment_status: s } }), onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-models"] }) });
  if (isLoading) return <Spinner />;
  if (error || !data) return <Banner kind="error">{(error as Error | null)?.message ?? "Could not load models."}</Banner>;
  return (
    <div className="space-y-6">
      <ul className="flex flex-wrap gap-x-8 gap-y-2 text-sm">{Object.entries(data.artifacts_present).map(([k, v]) => <li key={k}><span className={v ? "text-forest" : "text-danger"}>{v ? "● deployed" : "○ missing"}</span> {k.replace("_", " ")}</li>)}</ul>
      <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs text-muted"><tr><th className="py-2 font-medium">Model</th><th className="font-medium">Version</th><th className="font-medium">Type</th><th className="font-medium">Data</th><th className="font-medium">Status</th></tr></thead>
        <tbody className="divide-y divide-forest/10">{data.versions.map((v) => (
          <tr key={v.id}><td className="py-3 font-semibold">{v.model_name}</td><td>{v.version}</td><td>{v.model_type}</td>
            <td className={v.data_source?.startsWith("synthetic") ? "font-semibold text-amber" : ""}>{v.data_source ?? "—"}</td>
            <td>{isAdmin ? <select aria-label={`Status of ${v.model_name}`} className="input !w-auto !py-1" value={v.deployment_status} onChange={(e) => setSt.mutate({ id: v.id, s: e.target.value })}>{["staged", "active", "retired"].map((s) => <option key={s}>{s}</option>)}</select> : v.deployment_status}</td></tr>))}</tbody></table></div>
    </div>
  );
}

function AuditTab() {
  const { data, isLoading, error } = useQuery({ queryKey: ["admin-audit"], queryFn: () => api<Audit[]>("/admin/audit-logs?limit=100") });
  if (isLoading) return <Spinner />;
  if (error) return <Banner kind="error">{(error as Error).message}</Banner>;
  return (
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs text-muted"><tr><th className="py-2 font-medium">When</th><th className="font-medium">Action</th><th className="font-medium">Resource</th><th className="font-medium">Details</th></tr></thead>
      <tbody className="divide-y divide-forest/10">{data?.map((a) => <tr key={a.id}><td className="whitespace-nowrap py-2">{new Date(a.created_at).toLocaleString()}</td><td className="font-semibold">{a.action}</td><td>{a.resource ?? "—"}</td><td className="max-w-xs truncate text-xs text-muted">{a.details ? JSON.stringify(a.details) : ""}</td></tr>)}</tbody></table></div>
  );
}
