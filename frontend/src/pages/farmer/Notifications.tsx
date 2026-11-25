import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Banner, Empty, PageHeader, Spinner } from "../../components/common/ui";
import { api } from "../../services/api";
import type { NotificationItem } from "../../types";
import { dateShort } from "../../utils/format";

export default function Notifications() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["notifications"], queryFn: () => api<NotificationItem[]>("/analytics/notifications") });
  const read = useMutation({ mutationFn: (id: string) => api(`/analytics/notifications/${id}/read`, { method: "POST" }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["notifications"] }); qc.invalidateQueries({ queryKey: ["dashboard"] }); } });
  return (
    <>
      <PageHeader title="Notifications" />
      {isLoading ? <Spinner /> : error ? <Banner kind="error">{(error as Error).message}</Banner> : !data?.length ? <Empty title="You're all caught up" /> : (
        <ul className="divide-y divide-forest/10 border-y border-forest/10">
          {data.map((n) => (
            <li key={n.id} className={`flex items-start justify-between gap-4 px-1 py-4 ${n.is_read ? "opacity-60" : ""}`}>
              <div><p className="font-semibold">{n.title}</p><p className="text-sm text-muted">{n.message}</p><p className="mt-1 text-xs text-muted">{dateShort(n.created_at)}</p></div>
              {!n.is_read && <button type="button" aria-busy={read.isPending} disabled={read.isPending} className="btn-quiet shrink-0 !px-3 !py-1.5" onClick={() => read.mutate(n.id)}>Mark read</button>}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
