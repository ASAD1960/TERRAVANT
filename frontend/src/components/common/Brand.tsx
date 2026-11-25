export function Logo({ light = false, size = 28 }: { light?: boolean; size?: number }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="14" fill={light ? "#6FAF76" : "#163B2C"} />
        <path d="M32 50V26M32 26c0-8 6-13 14-13 0 8-5 13-14 13ZM32 34c0-6-5-10-12-10 0 6 4 10 12 10Z" fill="none" stroke={light ? "#10291F" : "#6FAF76"} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className={`text-lg font-extrabold tracking-[0.12em] ${light ? "text-white" : "text-forest"}`}>TERRAVANT</span>
    </span>
  );
}

/** Furrow contour lines — the one decorative motif, used only on public/auth pages. */
export function Furrows({ className = "" }: { className?: string }) {
  const rows = Array.from({ length: 16 }, (_, i) => i);
  return (
    <svg className={className} viewBox="0 0 400 320" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {rows.map((i) => (
        <path key={i} d={`M-20 ${20 + i * 20} C 90 ${-10 + i * 20 + (i % 3) * 8}, 210 ${60 + i * 20 - (i % 4) * 6}, 420 ${12 + i * 20}`}
          fill="none" stroke="#6FAF76" strokeOpacity={0.18 + (i % 4) * 0.07} strokeWidth="1.5" />
      ))}
    </svg>
  );
}
