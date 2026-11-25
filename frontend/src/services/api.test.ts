import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, tokens } from "./api";

const respond = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("api client", () => {
  afterEach(() => { vi.restoreAllMocks(); tokens.clear(); sessionStorage.clear(); });

  it("turns FastAPI validation errors into readable messages", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respond(422, { detail: [{ loc: ["body", "ph"], msg: "Input should be <= 11" }] })));
    await expect(api("/x", { json: {} })).rejects.toMatchObject({ status: 422, message: "ph: Input should be <= 11" });
  });
  it("does not leak server internals on 500", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respond(500, { detail: "Internal server error" })));
    await expect(api("/x")).rejects.toBeInstanceOf(ApiError);
  });
  it("refreshes once on 401 and retries", async () => {
    sessionStorage.setItem("tv_refresh", "old-refresh");
    const f = vi.fn()
      .mockResolvedValueOnce(respond(401, { detail: "expired" }))
      .mockResolvedValueOnce(respond(200, { access_token: "new-a", refresh_token: "new-r" }))
      .mockResolvedValueOnce(respond(200, { ok: true }));
    vi.stubGlobal("fetch", f);
    await expect(api("/farms")).resolves.toEqual({ ok: true });
    expect(f).toHaveBeenCalledTimes(3);
    expect((f.mock.calls[2][1] as RequestInit).headers).toMatchObject({ Authorization: "Bearer new-a" });
  });
  it("reports network failure clearly", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fail")));
    await expect(api("/x")).rejects.toMatchObject({ status: 0 });
  });
});
