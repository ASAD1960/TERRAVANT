import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Banner, PageHeader, SelectField, Spinner } from "../../components/common/ui";
import { useFields } from "../../hooks/queries";
import { api } from "../../services/api";
import type { WeatherForecast } from "../../types";
import { num } from "../../utils/format";

export default function Weather() {
  const fields = useFields();
  const [fieldId, setFieldId] = useState("");
  const qs = fieldId ? `?field_id=${fieldId}` : "";
  const { data, isLoading, error } = useQuery({ queryKey: ["weather", fieldId], queryFn: () => api<WeatherForecast>(`/weather/forecast${qs}`), retry: false });
  return (
    <>
      <PageHeader title="Weather" subtitle={fieldId ? "Forecast for the selected field." : "Forecast for central Punjab (Lahore). Choose a field with coordinates for local weather."} />
      <div className="mb-8 max-w-xs"><SelectField label="Location" value={fieldId} onChange={(e) => setFieldId(e.target.value)} options={[{ value: "", label: "Central Punjab (default)" }, ...(fields.data ?? []).filter((f) => f.latitude != null && f.longitude != null).map((f) => ({ value: f.id, label: f.field_name }))]} /></div>
      {isLoading ? <Spinner /> : error ? <Banner kind="warn">{(error as Error).message} The rest of TERRAVANT keeps working.</Banner> : data && (
        <>
          {data.stale && <div className="mb-4"><Banner kind="warn">Showing saved data — the weather service could not be reached.</Banner></div>}
          <dl className="grid grid-cols-2 gap-6 border-y border-forest/15 py-6 sm:grid-cols-4">
            {[["Now", `${num(data.current.temperature_c)} °C`], ["Humidity", `${num(data.current.humidity_pct, 0)} %`], ["Wind", `${num(data.current.wind_kmh, 0)} km/h`], ["Rain now", `${num(data.current.precipitation_mm)} mm`]].map(([k, v]) => (
              <div key={k}><dt className="text-sm text-muted">{k}</dt><dd className="text-2xl font-extrabold tabular-nums text-forest">{v}</dd></div>))}
          </dl>
          {data.advisories.length > 0 && <div className="mt-6 space-y-2">{data.advisories.map((a) => <Banner key={a} kind="warn">{a}</Banner>)}</div>}
          <div className="mt-8 h-72" role="img" aria-label="Seven-day forecast of maximum and minimum temperature and rainfall">
            <ResponsiveContainer>
              <ComposedChart data={data.forecast}><CartesianGrid strokeDasharray="3 3" stroke="#163B2C22" vertical={false} />
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} tickLine={false} /><YAxis yAxisId="t" width={32} unit="°" tickLine={false} /><YAxis yAxisId="r" orientation="right" width={36} unit="mm" tickLine={false} />
                <Tooltip /><Legend />
                <Bar yAxisId="r" dataKey="rain_mm" name="Rain" fill="#6FAF76" radius={[3, 3, 0, 0]} />
                <Line yAxisId="t" dataKey="t_max" name="High" stroke="#C84C4C" strokeWidth={2} dot={false} />
                <Line yAxisId="t" dataKey="t_min" name="Low" stroke="#163B2C" strokeWidth={2} dot={false} /></ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-xs text-muted">Source: {data.source}</p>
        </>
      )}
    </>
  );
}
