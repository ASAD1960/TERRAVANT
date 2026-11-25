import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as auth from "../hooks/useAuth";
import { RequireAuth } from "./Guards";

const mockUser = (roles: string[] | null, loading = false) =>
  vi.spyOn(auth, "useAuth").mockReturnValue({
    user: roles ? ({ id: "1", full_name: "T", email: "t@x.com", role_names: roles } as never) : null,
    loading, login: vi.fn(), logout: vi.fn(), hasRole: (...r: string[]) => !!roles && r.some((x) => roles.includes(x)),
  });

const renderAt = (path: string) => render(
  <MemoryRouter initialEntries={[path]}>
    <Routes>
      <Route path="/login" element={<p>login page</p>} />
      <Route element={<RequireAuth />}><Route path="/app" element={<p>private area</p>} /></Route>
      <Route element={<RequireAuth roles={["admin"]} />}><Route path="/admin" element={<p>admin area</p>} /></Route>
    </Routes>
  </MemoryRouter>,
);

describe("RequireAuth", () => {
  beforeEach(() => vi.restoreAllMocks());
  it("redirects anonymous visitors to login", () => { mockUser(null); renderAt("/app"); expect(screen.getByText("login page")).toBeInTheDocument(); });
  it("lets signed-in users through", () => { mockUser(["farmer"]); renderAt("/app"); expect(screen.getByText("private area")).toBeInTheDocument(); });
  it("blocks users without the role", () => { mockUser(["farmer"]); renderAt("/admin"); expect(screen.queryByText("admin area")).not.toBeInTheDocument(); });
  it("allows admins", () => { mockUser(["admin"]); renderAt("/admin"); expect(screen.getByText("admin area")).toBeInTheDocument(); });
  it("waits while the session is restored", () => { mockUser(null, true); renderAt("/app"); expect(screen.queryByText("login page")).not.toBeInTheDocument(); });
});
