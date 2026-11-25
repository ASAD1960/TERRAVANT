import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Banner, ConfidenceBar, Limitations, PageHeader } from "../../components/common/ui";
import { api } from "../../services/api";
import type { DiseaseResult } from "../../types";
import { titleCase } from "../../utils/format";

const MAX_MB = 8;
const OK = ["image/jpeg", "image/png", "image/webp"];

export default function DiseaseDetection() {
  const qc = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => { if (!file) { setPreview(null); return; } const u = URL.createObjectURL(file); setPreview(u); return () => URL.revokeObjectURL(u); }, [file]);

  const m = useMutation({
    mutationFn: (f: File) => { const fd = new FormData(); fd.append("file", f); return api<DiseaseResult>("/predictions/disease", { form: fd }); },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboard"] }),
  });
  const pick = (f: File | undefined) => {
    setLocalError(null);
    m.reset();
    setFile(null);
    if (!f) return;
    if (!OK.includes(f.type)) return setLocalError("Use a JPEG, PNG or WebP photo.");
    if (f.size > MAX_MB * 1024 * 1024) return setLocalError(`Photo is larger than ${MAX_MB} MB.`);
    setFile(f);
  };
  const r = m.data;
  return (
    <>
      <PageHeader title="Plant disease detection" subtitle="Upload a clear photo of one leaf. The model suggests a possible match; it cannot confirm a diagnosis." />
      <div className="grid gap-8 md:grid-cols-[18rem_1fr]">
        <div>
          <button type="button" onClick={() => input.current?.click()} className="flex aspect-square w-full items-center justify-center overflow-hidden rounded-md border-2 border-dashed border-forest/30 bg-soft text-sm text-muted hover:border-forest">
            {preview ? <img src={preview} alt="Selected leaf preview" className="h-full w-full object-cover" /> : "Choose or take a photo"}
          </button>
          <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" capture="environment" className="sr-only" aria-label="Leaf photo" onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ""; }} />
          <button type="button" aria-busy={m.isPending} className="btn mt-4 w-full" disabled={!file || m.isPending} onClick={() => file && m.mutate(file)}>{m.isPending ? "Analysing…" : "Analyse photo"}</button>
          <ul className="mt-4 list-disc space-y-1 pl-5 text-xs text-muted"><li>One leaf, in focus, in daylight</li><li>Fill the frame; avoid shadows</li><li>Max {MAX_MB} MB</li></ul>
        </div>
        <div aria-live="polite">
          {localError && <Banner kind="error">{localError}</Banner>}
          {m.error && <Banner kind={(m.error as { status?: number }).status === 503 ? "warn" : "error"}>{(m.error as Error).message}</Banner>}
          {r && (
            <section>
              {r.is_uncertain ? (<><p className="text-sm text-muted">Result</p><p className="text-3xl font-extrabold text-amber">Not sure</p></>) : (<><p className="text-sm text-muted">Possible match</p><p className="text-3xl font-extrabold text-forest">{titleCase(r.predicted_class)}</p></>)}
              <p className="mt-2 text-sm">{r.message}</p>
              <div className="mt-6 space-y-4"><h2 className="font-bold">Closest classes</h2>{r.alternatives.map((a) => <ConfidenceBar key={a.label} label={titleCase(a.label)} value={a.probability} />)}</div>
              <Limitations items={r.limitations} source={r.data_source} version={r.model_version} />
            </section>
          )}
        </div>
      </div>
    </>
  );
}
