// Access token lives in memory only. The refresh token is kept in sessionStorage (cleared when the tab closes).
// Trade-off: an httpOnly-cookie refresh flow is stronger against XSS and is recommended for production hardening.
const BASE = "/api/v1";
const RT_KEY = "tv_refresh";

let accessToken: string | null = null;
let onAuthLost: (() => void) | null = null;

export const tokens = {
  set(access: string, refresh: string) { accessToken = access; try { sessionStorage.setItem(RT_KEY, refresh); } catch { /* storage may be blocked */ } },
  clear() { accessToken = null; try { sessionStorage.removeItem(RT_KEY); } catch { /* ignore */ } },
  refresh(): string | null { try { return sessionStorage.getItem(RT_KEY); } catch { return null; } },
  hasAccess: () => accessToken !== null,
};
export const setAuthLostHandler = (fn: () => void) => { onAuthLost = fn; };

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

function messageFrom(body: unknown, status: number): string {
  const d = (body as { detail?: unknown } | null)?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    const first = d[0] as { loc?: unknown[]; msg?: string };
    return `${(first.loc ?? []).slice(1).join(".") || "Input"}: ${first.msg ?? "invalid"}`;
  }
  return status >= 500 ? "Something went wrong on our side. Try again shortly." : "Request failed";
}

let refreshing: Promise<boolean> | null = null;
async function tryRefresh(): Promise<boolean> {
  const rt = tokens.refresh();
  if (!rt) return false;
  refreshing ??= fetch(`${BASE}/auth/refresh`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) })
    .then(async (r) => {
      if (!r.ok) return false;
      const t: unknown = await r.json();

      if (
        typeof t !== "object" ||
        t === null ||
        !("access_token" in t) ||
        !("refresh_token" in t) ||
        typeof t.access_token !== "string" ||
        !t.access_token ||
        typeof t.refresh_token !== "string" ||
        !t.refresh_token
      ) return false;

      tokens.set(t.access_token, t.refresh_token);
      return true;
    })
    .catch(() => false)
    .finally(() => { refreshing = null; });
  return refreshing;
}

export async function api<T>(path: string, opts: { method?: string; json?: unknown; form?: FormData; blob?: boolean } = {}, retried = false): Promise<T> {
  const headers: Record<string, string> = {};
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (opts.json !== undefined) headers["Content-Type"] = "application/json";
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      method: opts.method ?? (opts.json !== undefined || opts.form ? "POST" : "GET"), headers,
      body: opts.form ?? (opts.json !== undefined ? JSON.stringify(opts.json) : undefined),
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check your connection and try again.");
  }
  if (res.status === 401 && !retried && !path.startsWith("/auth/") && (await tryRefresh())) return api<T>(path, opts, true);
  if (res.status === 401 && !path.startsWith("/auth/")) { tokens.clear(); onAuthLost?.(); }
  if (!res.ok) throw new ApiError(res.status, messageFrom(await res.json().catch(() => null), res.status));
  if (opts.blob) return (await res.blob()) as unknown as T;
  return (await res.json()) as T;
}
