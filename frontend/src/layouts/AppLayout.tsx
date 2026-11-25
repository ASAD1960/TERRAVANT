import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard, Tractor, CloudSun, Sprout, ScanLine,
  ChartNoAxesCombined, FlaskConical, Bell, Settings, LogOut,
} from "lucide-react";
import { Logo } from "../components/common/Brand";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import type { Dashboard } from "../types";

const navigation = [
  {
    title: "YOUR LAND",
    items: [
      { to: "/app", label: "Overview", icon: LayoutDashboard },
      { to: "/app/farms", label: "Farms & fields", icon: Tractor },
      { to: "/app/weather", label: "Weather", icon: CloudSun },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      { to: "/app/crops", label: "Crop recommendation", icon: Sprout },
      { to: "/app/disease", label: "Disease detection", icon: ScanLine },
      { to: "/app/yield", label: "Yield prediction", icon: ChartNoAxesCombined },
      { to: "/app/fertilizer", label: "Fertilizer guidance", icon: FlaskConical },
    ],
  },
  {
    title: "MANAGEMENT",
    items: [
      { to: "/app/notifications", label: "Notifications", icon: Bell },
      { to: "/app/admin", label: "Administration", icon: Settings, roles: ["admin", "operator"] },
    ],
  },
];

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<Dashboard>("/analytics/dashboard"),
    refetchInterval: 60_000,
  });

  const activeItem = navigation
    .flatMap((group) => group.items)
    .find((item) =>
      item.to === "/app"
        ? location.pathname === "/app"
        : location.pathname.startsWith(item.to),
    );

  const sidebar = (
    <div className="tv-sidebar-nav">
      <div className="tv-sidebar-brand">
        <Logo light />
        <span className="tv-sidebar-edition">FIELD INTELLIGENCE</span>
      </div>

      <div className="tv-sidebar-workspace">
        <span className="tv-workspace-mark">T</span>
        <span className="tv-workspace-copy">
          <strong>My workspace</strong>
          <small>Agricultural operations</small>
        </span>
        <span className="tv-workspace-status">Active</span>
      </div>

      <nav aria-label="Main navigation" className="tv-navigation-groups">
        {navigation.map((group) => {
          const items = group.items.filter(
            (item) => !("roles" in item) || !item.roles || hasRole(...item.roles),
          );

          if (!items.length) return null;

          return (
            <section className="tv-navigation-group" key={group.title}>
              <p className="tv-navigation-label">{group.title}</p>
              <ul>
                {items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <li key={item.to}>
                      <NavLink
                        to={item.to}
                        end={item.to === "/app"}
                        onClick={() => setMobileOpen(false)}
                        className={({ isActive }) =>
                          `tv-navigation-link ${isActive ? "is-active" : ""}`
                        }
                      >
                        <Icon
                          className="tv-navigation-icon"
                          size={18}
                          strokeWidth={1.8}
                          aria-hidden="true"
                        />
                        <span className="tv-navigation-text">{item.label}</span>
                        {item.to === "/app/notifications" &&
                          !!data?.unread_notifications && (
                            <span
                              className="tv-notification-count"
                              aria-label={`${data.unread_notifications} unread`}
                            >
                              {data.unread_notifications}
                            </span>
                          )}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </section>
          );
        })}
      </nav>

      <div className="tv-sidebar-bottom">
        <div className="tv-sidebar-user">
          <div className="tv-user-avatar">
            {user?.full_name?.charAt(0)?.toUpperCase() ?? "U"}
          </div>
          <div className="tv-user-details">
            <strong>{user?.full_name ?? "User"}</strong>
            <span>{user?.email}</span>
          </div>
        </div>
        <button
          className="tv-signout"
          onClick={async () => {
            await logout();
            navigate("/login");
          }}
          type="button"
        >
          <LogOut size={17} strokeWidth={1.8} aria-hidden="true" />
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <div className="tv-app-shell">
      <aside className="tv-sidebar">{sidebar}</aside>

      <div className="tv-mobile-header">
        <Logo light size={24} />
        <button
          className="tv-mobile-toggle"
          aria-expanded={mobileOpen}
          aria-controls="mobile-navigation"
          onClick={() => setMobileOpen((open) => !open)}
          type="button"
        >
          {mobileOpen ? "Close" : "Menu"}
        </button>
      </div>

      {mobileOpen && (
        <div id="mobile-navigation" className="tv-mobile-navigation">
          {sidebar}
        </div>
      )}

      <div className="tv-app-main">
        <header className="tv-topbar">
          <div>
            <span className="tv-topbar-overline">TERRAVANT / WORKSPACE</span>
            <p>{activeItem?.label ?? "Field intelligence"}</p>
          </div>
          <div className="tv-topbar-right">
            <div className="tv-topbar-avatar">
              {user?.full_name?.charAt(0)?.toUpperCase() ?? "U"}
            </div>
          </div>
        </header>

        <main className="tv-page-content">
          <Outlet />
          <footer className="tv-app-footer">
            <span>© {new Date().getFullYear()} TERRAVANT · ASAD YAR</span>
            <span>AGRICULTURAL INTELLIGENCE</span>
          </footer>
        </main>
      </div>
    </div>
  );
}

