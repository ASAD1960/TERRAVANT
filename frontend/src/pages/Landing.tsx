
import { Link } from "react-router-dom";
import { Logo } from "../components/common/Brand";

const CAPABILITIES = [
  {
    number: "01",
    category: "01 / PLANNING",
    title: "Crop intelligence",
    description:
      "Compare suitable crops using soil and climate inputs. Understand the conditions and factors behind each recommendation.",
    status: "AVAILABLE",
    symbol: "◈",
  },
  {
    number: "02",
    category: "02 / MONITORING",
    title: "Field weather",
    description:
      "Follow seven-day forecasts for your fields, with attention to heat, frost and heavy rainfall.",
    status: "AVAILABLE",
    symbol: "☼",
  },
  {
    number: "03",
    category: "03 / PRODUCTIVITY",
    title: "Yield estimation",
    description:
      "Explore per-hectare yield estimates alongside uncertainty ranges and model limitations.",
    status: "AVAILABLE",
    symbol: "↗",
  },
  {
    number: "04",
    category: "04 / NUTRITION",
    title: "Fertilizer guidance",
    description:
      "Review nutrient requirements and growth-stage guidance informed by available soil information.",
    status: "AVAILABLE",
    symbol: "✳",
  },
  {
    number: "05",
    category: "05 / CROP HEALTH",
    title: "Disease detection",
    description:
      "Image-based crop disease analysis is in development and is not yet available for decisions.",
    status: "IN DEVELOPMENT",
    symbol: "⌁",
  },
  {
    number: "06",
    category: "06 / OPERATIONS",
    title: "Farm records",
    description:
      "Organize farms, fields, soil tests and agricultural activities in one accessible workspace.",
    status: "AVAILABLE",
    symbol: "▤",
  },
];

const WORKFLOW = [
  {
    number: "01",
    tag: "FIELD RECORDS",
    title: "Know your field",
    description: "Location, field area and soil information",
  },
  {
    number: "02",
    tag: "FIELD ANALYSIS",
    title: "Understand conditions",
    description: "Soil readings, rainfall and temperature",
  },
  {
    number: "03",
    tag: "CROP INTELLIGENCE",
    title: "Explore your options",
    description: "Crop recommendations and supporting factors",
  },
  {
    number: "04",
    tag: "FIELD PLANNING",
    title: "Plan with context",
    description: "Weather, yield estimates and fertilizer guidance",
  },
];

function ArrowIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M4 10h12m-5-5 5 5-5 5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function FieldIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.35"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="h-5 w-5"
    >
      <path d="M3 20h18M5 20V9l7-5 7 5v11M9 20v-6h6v6" />
      <path d="M9 10h.01M15 10h.01" />
    </svg>
  );
}

function SectionEyebrow({ children }: { children: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="h-px w-8 bg-[#91a47a]" />
      <p className="text-[9px] font-bold tracking-[0.22em] text-[#788b68]">
        {children}
      </p>
    </div>
  );
}

function DashboardPreview() {
  return (
    <div className="relative mx-auto w-full max-w-[540px]">
      <div className="absolute -inset-8 rounded-full bg-[#c4d2a9]/10 blur-3xl" />

      <div className="relative overflow-hidden rounded-[22px] border border-white/50 bg-[#f7f7f0] shadow-[0_35px_100px_rgba(0,0,0,0.32)]">
        <div className="flex items-center justify-between border-b border-[#e2e6dc] px-5 py-5 sm:px-7">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#294d35] text-white">
              <FieldIcon />
            </div>
            <div>
              <p className="text-[10px] font-bold tracking-[0.19em] text-[#294631]">
                TERRAVANT
              </p>
              <p className="mt-1 text-[9px] tracking-[0.14em] text-[#849080]">
                FIELD INTELLIGENCE
              </p>
            </div>
          </div>

          <span className="rounded-full border border-[#d8e1d1] bg-[#edf2e9] px-3 py-1.5 text-[8px] font-bold tracking-[0.12em] text-[#4c6948]">
            WORKFLOW OVERVIEW
          </span>
        </div>

        <div className="px-5 pb-6 pt-7 sm:px-7 sm:pt-8">
          <div>
            <p className="text-[9px] font-bold tracking-[0.2em] text-[#8a9684]">
              A CONNECTED APPROACH TO AGRICULTURE
            </p>
            <h3 className="mt-3 text-[27px] font-semibold leading-tight tracking-[-0.05em] text-[#294631] sm:text-[32px]">
              From field
              <br />
              to decision.
            </h3>
            <p className="mt-3 max-w-sm text-xs leading-6 text-[#788276]">
              A practical process for turning agricultural information into
              more informed decisions.
            </p>
          </div>

          <div className="mt-7 border-t border-[#e3e7de] pt-3">
            <div className="relative">
              <div className="absolute bottom-9 left-[17px] top-8 w-px bg-[#d7e0d1]" />

              {WORKFLOW.map((step) => (
                <div
                  key={step.number}
                  className="relative flex gap-4 py-4"
                >
                  <div className="relative z-10 grid h-9 w-9 shrink-0 place-items-center rounded-full border border-[#cedbc5] bg-[#edf2e9] text-[9px] font-bold text-[#4a6747]">
                    {step.number}
                  </div>

                  <div className="min-w-0 flex-1 border-b border-[#e8ebe4] pb-4 last:border-0 last:pb-0">
                    <p className="text-[8px] font-bold tracking-[0.17em] text-[#849477]">
                      {step.tag}
                    </p>
                    <h4 className="mt-1.5 text-sm font-semibold text-[#304b35]">
                      {step.title}
                    </h4>
                    <p className="mt-1 text-[10px] leading-5 text-[#818b7e]">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-5 border-l-[3px] border-[#81966b] bg-[#eaf0e5] px-4 py-4 sm:px-5">
            <p className="text-[8px] font-bold tracking-[0.19em] text-[#718365]">
              THE TERRAVANT PRINCIPLE
            </p>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#304c35]">
              Understand the conditions behind a recommendation, not just
              the result.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-[#e1e6dc] bg-[#eff1e9] px-5 py-3 sm:px-7">
          <p className="text-[9px] leading-5 text-[#818b7d]">
            Illustrative workflow. Not live farm data or model output.
          </p>
          <span className="shrink-0 text-[8px] font-bold tracking-[0.13em] text-[#819075]">
            TV / 01
          </span>
        </div>
      </div>

      <div className="absolute -bottom-7 -left-3 hidden rounded-lg border border-white/20 bg-[#f5f5ed] px-4 py-3 shadow-xl sm:block lg:-left-9">
        <p className="text-[8px] font-bold tracking-[0.17em] text-[#839078]">
          DESIGNED AROUND
        </p>
        <p className="mt-1 text-xs font-semibold text-[#304b35]">
          The realities of the field.
        </p>
      </div>
    </div>
  );
}

function CapabilityCard({
  item,
}: {
  item: (typeof CAPABILITIES)[number];
}) {
  const available = item.status === "AVAILABLE";

  return (
    <article className="group relative flex min-h-[280px] flex-col overflow-hidden bg-[#f7f7f0] p-7 transition-colors duration-300 hover:bg-white sm:p-8">
      <div className="flex items-start justify-between">
        <span className="text-[9px] font-bold tracking-[0.17em] text-[#899582]">
          {item.category}
        </span>

        <span
          className={`rounded-full px-2.5 py-1 text-[8px] font-bold tracking-[0.1em] ${
            available
              ? "bg-[#e8eee3] text-[#52704c]"
              : "bg-[#f1eadb] text-[#927445]"
          }`}
        >
          {item.status}
        </span>
      </div>

      <div className="mt-9 flex items-center justify-between">
        <span className="text-2xl font-light text-[#849875]">
          {item.symbol}
        </span>
        <span className="text-[10px] font-semibold tracking-widest text-[#a0aa98]">
          {item.number}
        </span>
      </div>

      <h3 className="mt-5 text-xl font-semibold tracking-[-0.025em] text-[#294631]">
        {item.title}
      </h3>

      <p className="mt-3 text-[13px] leading-6 text-[#758073]">
        {item.description}
      </p>

      <div className="mt-auto flex items-center justify-between pt-7">
        <span className="text-[8px] font-bold tracking-[0.15em] text-[#9aa392]">
          TERRAVANT / FIELD SYSTEMS
        </span>
        <span className="w-5 text-[#718567] transition-transform duration-300 group-hover:translate-x-1">
          <ArrowIcon />
        </span>
      </div>

      <div className="absolute bottom-0 left-0 h-[2px] w-0 bg-[#82966d] transition-all duration-300 group-hover:w-full" />
    </article>
  );
}

export default function Landing() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#f5f5ed] text-[#243b2c]">
      {/* Navigation */}
      <header className="relative z-20 border-b border-[#dce2d5] bg-[#f5f5ed]">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-5 py-4 sm:px-10 lg:px-16">
          <Link to="/" aria-label="TERRAVANT home">
            <Logo />
          </Link>

          <nav className="flex items-center gap-3 text-sm font-semibold">
            <Link
              to="/login"
              className="px-3 py-2 text-[#36533c] transition-colors hover:text-[#81966b]"
            >
              Sign in
            </Link>

            <Link
              to="/register"
              className="inline-flex items-center gap-2 rounded-md bg-[#294d35] px-4 py-3 text-xs font-bold text-white transition-colors hover:bg-[#3b6546] sm:px-5"
            >
              Get started
              <span>↗</span>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative isolate overflow-hidden bg-[#173522] text-white">
        <img
          src="https://info.jetpress.com/hs-fs/hubfs/shutterstock_1494272252.jpg?height=1334&name=shutterstock_1494272252.jpg&width=2000"
          alt="Agricultural machinery working through a cultivated field"
          className="absolute inset-0 -z-20 h-full w-full object-cover object-center"
          fetchPriority="high"
        />

        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-[#10291b]/95 via-[#173522]/80 to-[#173522]/25" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-t from-[#10291b]/75 via-transparent to-[#10291b]/15" />

        <div className="relative mx-auto grid min-h-[720px] max-w-[1440px] items-center gap-16 px-5 py-20 sm:px-10 lg:min-h-[790px] lg:grid-cols-[1.05fr_0.95fr] lg:px-16 lg:py-24">
          <div className="max-w-[680px]">
            <div className="mb-9 flex items-center gap-3">
              <span className="h-px w-10 bg-[#b6c99c]" />
              <span className="text-[9px] font-bold tracking-[0.24em] text-[#d4dfc3] sm:text-[10px]">
                AGRICULTURAL INTELLIGENCE / PAKISTAN
              </span>
            </div>

            <p className="mb-6 text-[10px] font-bold uppercase tracking-[0.2em] text-[#c5d4b4]">
              Agriculture deserves better decisions.
            </p>

            <h1 className="max-w-[720px] text-[45px] font-semibold leading-[1.06] tracking-[-0.06em] sm:text-6xl lg:text-[78px]">
              See your fields.
              <span className="mt-3 block font-normal italic text-[#c5d5a9]">
                Understand what comes next.
              </span>
            </h1>

            <p className="mt-8 max-w-[510px] text-sm leading-7 text-white/75 sm:text-base sm:leading-8">
              From crop planning to field conditions, TERRAVANT brings
              agricultural data and machine-learning decision support into
              one clear view — with the context to understand its limitations.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              <Link
                to="/register"
                className="group inline-flex min-h-12 items-center gap-4 rounded-md bg-[#d0ddaf] px-6 py-3 text-sm font-bold text-[#203d29] transition-colors hover:bg-white"
              >
                Explore TERRAVANT
                <span className="w-5 transition-transform group-hover:translate-x-1">
                  <ArrowIcon />
                </span>
              </Link>

              <Link
                to="/login"
                className="inline-flex min-h-12 items-center rounded-md border border-white/35 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white hover:bg-white/10"
              >
                Sign in
              </Link>
            </div>

            <div className="mt-14 grid max-w-lg grid-cols-3 gap-5 border-t border-white/20 pt-6">
              <div>
                <p className="text-[9px] font-bold tracking-[0.17em] text-[#c5d4b4]">
                  BUILT FOR
                </p>
                <p className="mt-2 text-xs leading-5 text-white/85">
                  Farmers &amp; agribusinesses
                </p>
              </div>

              <div>
                <p className="text-[9px] font-bold tracking-[0.17em] text-[#c5d4b4]">
                  FOCUS
                </p>
                <p className="mt-2 text-xs leading-5 text-white/85">
                  Punjab, Pakistan
                </p>
              </div>

              <div>
                <p className="text-[9px] font-bold tracking-[0.17em] text-[#c5d4b4]">
                  APPROACH
                </p>
                <p className="mt-2 text-xs leading-5 text-white/85">
                  Evidence-led decisions
                </p>
              </div>
            </div>
          </div>

          <div className="relative z-10 py-6 lg:pl-4">
            <DashboardPreview />
          </div>

          <div className="absolute bottom-8 right-8 hidden items-center gap-3 text-[9px] font-semibold tracking-[0.2em] text-white/55 lg:flex">
            <span className="h-px w-8 bg-white/40" />
            GROW WITH CLARITY
          </div>
        </div>
      </section>

      {/* Introduction */}
      <section className="mx-auto grid max-w-[1440px] gap-12 px-5 py-24 sm:px-10 lg:grid-cols-[0.9fr_1.1fr] lg:px-16 lg:py-32">
        <div>
          <SectionEyebrow>A DIFFERENT WAY TO FARM</SectionEyebrow>

          <h2 className="mt-7 max-w-md text-3xl font-semibold leading-[1.15] tracking-[-0.045em] sm:text-4xl lg:text-[48px]">
            Better decisions start with better information.
          </h2>
        </div>

        <div className="max-w-2xl lg:ml-auto lg:pt-8">
          <p className="text-base leading-8 text-[#667365]">
            Agricultural decisions are connected. Soil conditions influence
            crop choices. Weather changes field requirements. Farm records
            provide context for the next season.
          </p>

          <p className="mt-5 text-base leading-8 text-[#667365]">
            TERRAVANT brings these elements together, helping farmers and
            agricultural businesses make more informed decisions without
            treating a model prediction as a guarantee.
          </p>

          <div className="mt-9 flex items-center gap-4 border-t border-[#dce2d5] pt-6">
            <span className="h-9 w-[3px] bg-[#81966b]" />
            <p className="text-xs font-semibold leading-5 text-[#53684e]">
              Information connected to real agricultural decisions.
            </p>
          </div>
        </div>
      </section>

      {/* Platform capabilities */}
      <section className="border-y border-[#dfe4d9] bg-[#ecefe5]">
        <div className="mx-auto max-w-[1440px] px-5 py-24 sm:px-10 lg:px-16 lg:py-32">
          <div className="flex flex-wrap items-end justify-between gap-8">
            <div>
              <SectionEyebrow>THE PLATFORM</SectionEyebrow>
              <h2 className="mt-6 max-w-xl text-3xl font-semibold leading-tight tracking-[-0.045em] sm:text-4xl lg:text-[48px]">
                Intelligence across your operation.
              </h2>
            </div>

            <p className="max-w-sm text-sm leading-7 text-[#788276]">
              A growing set of practical tools for understanding and
              managing agricultural operations.
            </p>
          </div>

          <div className="mt-16 grid gap-px overflow-hidden border border-[#d9e0d3] bg-[#d9e0d3] sm:grid-cols-2 lg:grid-cols-3">
            {CAPABILITIES.map((item) => (
              <CapabilityCard key={item.number} item={item} />
            ))}
          </div>

          <p className="mt-5 text-[9px] leading-5 text-[#899386]">
            Availability reflects the current development state of each
            capability. Model estimates should be interpreted with their
            limitations.
          </p>
        </div>
      </section>

      {/* Product philosophy */}
      <section className="bg-[#f5f5ed]">
        <div className="mx-auto max-w-[1440px] px-5 py-24 sm:px-10 lg:px-16 lg:py-32">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <SectionEyebrow>THE THINKING BEHIND TERRAVANT</SectionEyebrow>
              <h2 className="mt-7 max-w-md text-3xl font-semibold leading-[1.16] tracking-[-0.045em] sm:text-4xl lg:text-[46px]">
                Agricultural intelligence should mean more than a prediction.
              </h2>
            </div>

            <div className="grid gap-8 sm:grid-cols-3 lg:pt-5">
              <div className="border-t border-[#d5ddce] pt-5">
                <span className="text-[10px] font-bold tracking-widest text-[#849477]">
                  01 / CONTEXT
                </span>
                <h3 className="mt-5 text-lg font-semibold text-[#304b35]">
                  Understand the field
                </h3>
                <p className="mt-3 text-sm leading-6 text-[#788276]">
                  Agricultural information becomes useful when it is
                  considered in its local context.
                </p>
              </div>

              <div className="border-t border-[#d5ddce] pt-5">
                <span className="text-[10px] font-bold tracking-widest text-[#849477]">
                  02 / EVIDENCE
                </span>
                <h3 className="mt-5 text-lg font-semibold text-[#304b35]">
                  Examine the factors
                </h3>
                <p className="mt-3 text-sm leading-6 text-[#788276]">
                  Recommendations should be considered alongside their
                  inputs and supporting information.
                </p>
              </div>

              <div className="border-t border-[#d5ddce] pt-5">
                <span className="text-[10px] font-bold tracking-widest text-[#849477]">
                  03 / JUDGEMENT
                </span>
                <h3 className="mt-5 text-lg font-semibold text-[#304b35]">
                  Decide responsibly
                </h3>
                <p className="mt-3 text-sm leading-6 text-[#788276]">
                  Technology can inform a decision. Local expertise and
                  practical judgement remain essential.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Transparency */}
      <section className="relative overflow-hidden bg-[#203d2a] text-white">
        <div className="pointer-events-none absolute -right-40 -top-40 h-[500px] w-[500px] rounded-full border border-white/[0.07]" />
        <div className="pointer-events-none absolute -right-20 -top-20 h-[340px] w-[340px] rounded-full border border-white/[0.07]" />

        <div className="relative mx-auto grid max-w-[1440px] gap-12 px-5 py-24 sm:px-10 lg:grid-cols-2 lg:items-center lg:px-16 lg:py-32">
          <div>
            <div className="flex items-center gap-3">
              <span className="h-px w-8 bg-[#b6c99c]" />
              <p className="text-[9px] font-bold tracking-[0.22em] text-[#c1d2aa]">
                TRANSPARENCY MATTERS
              </p>
            </div>

            <h2 className="mt-7 max-w-xl text-3xl font-semibold leading-[1.15] tracking-[-0.045em] sm:text-5xl">
              Technology should support judgement, not replace it.
            </h2>

            <p className="mt-6 max-w-md text-sm leading-7 text-white/60">
              Agricultural intelligence is useful only when its limitations
              are understood.
            </p>
          </div>

          <div className="max-w-xl lg:ml-auto">
            <p className="text-sm leading-7 text-white/75 sm:text-base">
              A useful prediction is more than a number. It needs relevant
              inputs, understandable context and honest limitations.
              TERRAVANT is designed to help users understand the information
              behind agricultural recommendations.
            </p>

            <div className="mt-8 border-t border-white/20">
              {[
                "Understand the inputs behind recommendations.",
                "Consider uncertainty in yield estimates.",
                "Use local agricultural expertise for important decisions.",
              ].map((item, index) => (
                <div
                  key={item}
                  className="flex items-center gap-5 border-b border-white/10 py-5"
                >
                  <span className="text-[10px] font-bold tracking-widest text-[#c5d5a9]">
                    0{index + 1}
                  </span>
                  <span className="text-sm leading-6 text-white/85">
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="bg-[#f5f5ed]">
        <div className="mx-auto max-w-[1440px] px-5 py-24 sm:px-10 lg:px-16 lg:py-32">
          <div className="relative overflow-hidden rounded-[20px] bg-[#dfe7d6] px-7 py-16 sm:px-14 sm:py-20 lg:px-20">
            <div className="pointer-events-none absolute -right-24 -top-32 h-[420px] w-[420px] rounded-full border border-[#b8c9a9]/60" />
            <div className="pointer-events-none absolute -right-8 -top-16 h-[300px] w-[300px] rounded-full border border-[#b8c9a9]/60" />
            <div className="pointer-events-none absolute -bottom-44 right-24 h-[330px] w-[330px] rounded-full border border-[#b8c9a9]/40" />

            <div className="relative max-w-2xl">
              <SectionEyebrow>
                YOUR NEXT GROWING SEASON STARTS WITH INFORMATION
              </SectionEyebrow>

              <h2 className="mt-7 text-3xl font-semibold leading-[1.12] tracking-[-0.045em] text-[#26432f] sm:text-5xl lg:text-[58px]">
                Bring your agricultural decisions into focus.
              </h2>

              <p className="mt-6 max-w-lg text-sm leading-7 text-[#657361]">
                Create your TERRAVANT account and start organizing your
                agricultural information in one place.
              </p>

              <Link
                to="/register"
                className="group mt-9 inline-flex items-center gap-4 rounded-md bg-[#294d35] px-6 py-4 text-sm font-bold text-white transition-colors hover:bg-[#3b6546]"
              >
                Get started
                <span className="w-5 transition-transform group-hover:translate-x-1">
                  <ArrowIcon />
                </span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#dce2d5] bg-[#f5f5ed]">
        <div className="mx-auto grid max-w-[1440px] gap-8 px-5 py-10 sm:px-10 md:grid-cols-[1fr_auto] md:items-center lg:px-16">
          <div>
            <Logo />
            <p className="mt-3 text-[9px] font-semibold tracking-[0.2em] text-[#859080]">
              INTELLIGENCE THAT GROWS.
            </p>
          </div>

          <div className="flex flex-wrap gap-6 text-xs font-semibold text-[#60715e]">
            <Link to="/login" className="transition hover:text-[#294d35]">
              Sign in
            </Link>
            <Link to="/register" className="transition hover:text-[#294d35]">
              Create account
            </Link>
          </div>
        </div>

        <div className="border-t border-[#e1e5dc]">
          <div className="mx-auto flex max-w-[1440px] flex-col gap-3 px-5 py-5 text-[10px] text-[#899386] sm:px-10 md:flex-row md:items-center md:justify-between lg:px-16">
            <p>
              © {new Date().getFullYear()} TERRAVANT. All rights reserved.
            </p>

            <p className="font-semibold tracking-wide text-[#60715e]">
              An agricultural intelligence platform by Asad Yar.
            </p>
          </div>
        </div>

        <div className="border-t border-[#e1e5dc] px-5 py-4 text-center text-[10px] leading-5 text-[#899386]">
          Predictions are decision-support tools, not a diagnosis or
          guarantee. Confirm important decisions with a qualified local
          agricultural advisor.
        </div>
      </footer>
    </main>
  );
}
