import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Banner, Spinner } from "../../components/common/ui";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import type { Dashboard as DashboardData } from "../../types";
import { dateShort, num, titleCase } from "../../utils/format";

export default function Dashboard() {
  const { user } = useAuth();

  const {
    data,
    isLoading,
    error,
  } = useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: () => api<DashboardData>("/analytics/dashboard"),
  });

  const report = useMutation<Blob, Error>({
    mutationFn: () => api<Blob>("/analytics/reports", { blob: true }),
    onSuccess: (file) => {
      const url = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = url;
      link.download = "terravant_farms.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    },
  });

  if (isLoading) return <Spinner />;

  if (error || !data) {
    return (
      <Banner kind="error">
        {error?.message ?? "Could not load your overview."}
      </Banner>
    );
  }

  const counts = [
    { name: "Crop", value: data.prediction_counts.crop },
    { name: "Disease", value: data.prediction_counts.disease },
    { name: "Yield", value: data.prediction_counts.yield },
  ];

  const totalPredictions = counts.reduce(
    (total, item) => total + item.value,
    0,
  );

  const firstName = user?.full_name?.split(" ")[0] ?? "there";

  const stats = [
    {
      label: "Registered farms",
      value: String(data.total_farms),
      detail: "Your farm locations",
      number: "01",
    },
    {
      label: "Registered fields",
      value: String(data.total_fields),
      detail: "Fields across your registered farms",
      number: "02",
    },
    {
      label: "Total farm area",
      value: `${num(data.total_area, 1)} ${data.area_unit}`,
      detail: `Combined area in ${data.area_unit}s`,
      number: "03",
    },
    {
      label: "Prediction records",
      value: String(totalPredictions),
      detail: "Saved crop, disease and yield records",
      number: "04",
    },
  ];

  return (
    <div className="tv-dashboard">
      <header className="tv-dashboard-header">
        <div>
          <p className="tv-dashboard-eyebrow">
            FIELD INTELLIGENCE <span>/</span> OVERVIEW
          </p>
          <h1>
            Good day, <span>{firstName}.</span>
          </h1>
          <p className="tv-dashboard-description">
            A clear view of your agricultural operations and decision activity.
          </p>
        </div>

        {data.total_farms > 0 && (
          <button type="button" aria-busy={report.isPending} className="tv-dashboard-export"
            disabled={report.isPending}
            onClick={() => report.mutate()}
          >
            <span>
              {report.isPending ? "Preparing report..." : "Export farm report"}
            </span>
            <span aria-hidden="true">&#8599;</span>
          </button>
        )}
      </header>

      {report.error && (
        <div className="mb-5">
          <Banner kind="error">{report.error.message}</Banner>
        </div>
      )}

      <section
        className="tv-dashboard-metrics"
        aria-label="Farm statistics"
      >
        {stats.map((stat) => (
          <article className="tv-dashboard-metric" key={stat.number}>
            <div className="tv-dashboard-metric-top">
              <span>{stat.label}</span>
              <span>{stat.number}</span>
            </div>
            <div className="tv-dashboard-metric-value">{stat.value}</div>
            <p>{stat.detail}</p>
          </article>
        ))}
      </section>

      {data.total_farms === 0 && (
        <section className="tv-dashboard-onboarding">
          <div className="tv-dashboard-onboarding-mark">01</div>
          <div>
            <p className="tv-dashboard-eyebrow">YOUR FIRST STEP</p>
            <h2>Start with your land.</h2>
            <p>
              Register your first farm, add its fields and begin building your
              agricultural workspace.
            </p>
            <Link to="/app/farms" className="tv-dashboard-text-link">
              Register your first farm <span>&#8599;</span>
            </Link>
          </div>
          <div className="tv-dashboard-field-art" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
        </section>
      )}

      <div className="tv-dashboard-grid">
        <section className="tv-dashboard-panel">
          <div className="tv-dashboard-panel-heading">
            <div>
              <p className="tv-dashboard-eyebrow">ACTIVITY LOG</p>
              <h2>Recent predictions</h2>
            </div>
            <span className="tv-dashboard-panel-index">01 / 02</span>
          </div>

          {data.recent_predictions.length === 0 ? (
            <div className="tv-dashboard-empty">
              <span className="tv-dashboard-empty-mark">&#8212;</span>
              <h3>No prediction activity yet</h3>
              <p>
                Your recent crop, disease and yield predictions will appear here.
              </p>
              <Link to="/app/crops" className="tv-dashboard-text-link">
                Explore crop recommendations <span>&#8599;</span>
              </Link>
            </div>
          ) : (
            <ul className="tv-dashboard-activity">
              {data.recent_predictions.map((prediction, index) => (
                <li key={prediction.id}>
                  <span className="tv-dashboard-activity-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div className="tv-dashboard-activity-content">
                    <span className="tv-dashboard-activity-type">
                      {titleCase(prediction.type)}
                    </span>
                    <p>{prediction.summary}</p>
                  </div>
                  <time dateTime={prediction.created_at}>
                    {dateShort(prediction.created_at)}
                  </time>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="tv-dashboard-panel">
          <div className="tv-dashboard-panel-heading">
            <div>
              <p className="tv-dashboard-eyebrow">PREDICTION DISTRIBUTION</p>
              <h2>Prediction activity</h2>
            </div>
            <span className="tv-dashboard-panel-index">02 / 02</span>
          </div>

          <div className="tv-dashboard-chart">
            {totalPredictions === 0 ? (
              <div className="tv-dashboard-chart-empty">
                <strong>No prediction data yet</strong>
                <p>
                  Prediction types will appear here after your first saved
                  prediction.
                </p>
              </div>
            ) : (
              <div
                role="img"
                aria-label={`Predictions by type: ${counts
                  .map((item) => `${item.name} ${item.value}`)
                  .join(", ")}`}
                style={{ width: "100%", height: "100%" }}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={counts}
                    margin={{ top: 12, right: 8, left: -18, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 5"
                      stroke="#dfe5dc"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#737d70", fontSize: 12 }}
                      dy={10}
                    />
                    <YAxis
                      allowDecimals={false}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#737d70", fontSize: 11 }}
                    />
                    <Tooltip
                      cursor={{ fill: "#edf1e9" }}
                      contentStyle={{
                        border: "1px solid #dfe5dc",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Bar
                      dataKey="value"
                      fill="#315b43"
                      radius={[4, 4, 0, 0]}
                      maxBarSize={48}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="tv-dashboard-chart-footer">
            <span>Total prediction records</span>
            <strong>{totalPredictions}</strong>
          </div>
        </section>
      </div>

      <footer className="tv-dashboard-note">
        <span>FIELD INTELLIGENCE</span>
        <span>Decisions grounded in your farm data.</span>
      </footer>
    </div>
  );
}


