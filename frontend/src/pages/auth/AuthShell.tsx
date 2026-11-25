
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../../components/common/Brand";

export default function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <main className="tv-auth-scene">
      <div className="tv-auth-backdrop" />
      <div className="tv-auth-atmosphere" />
      <div className="tv-auth-grain" />

      <div className="tv-auth-content">
        <header className="tv-auth-header">
          <Link to="/" className="tv-auth-brand">
            <Logo light size={36} />
          </Link>
          <span className="tv-auth-edition">
            FIELD INTELLIGENCE PLATFORM
          </span>
        </header>

        <section className="tv-auth-card">
          <div className="tv-auth-glass-highlight" />

          <div className="tv-auth-heading">
            <span className="tv-auth-eyebrow">
              <span className="tv-auth-live-dot" />
              AGRICULTURE · INTELLIGENCE · PRECISION
            </span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>

          <div className="tv-auth-form">{children}</div>
          <div className="tv-auth-footer">{footer}</div>

          <div className="tv-auth-bottom">
            <span>SECURE ACCESS</span>
            <span>© TERRAVANT 2026</span>
          </div>
        </section>

        <footer className="tv-auth-tagline">
          <span>GROW WITH CLARITY.</span>
          <span>LEAD WITH INTELLIGENCE.</span>
        </footer>
      </div>
    </main>
  );
}
