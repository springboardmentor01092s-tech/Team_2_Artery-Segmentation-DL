import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api";

const API_URL = "http://127.0.0.1:8000";

const STAGE_NAMES = {
  artery_segmentation: "Artery segmentation",
  syntax_segmentation: "Artery segmentation",
  stenosis_segmentation: "Stenosis segmentation",
  vessel_analysis: "Vessel analysis",
  candidate_extraction: "Candidate extraction",
  stenosis_classification: "Classification",
  stenosis_localization: "Localization",
  narrowing_estimation: "Narrowing estimate",
  severity_classification: "Severity",
  explainable_ai: "Grad-CAM",
  visualization: "Visualization",
};

// button labels for the two segmentation tasks (internal names: syntax, stenosis)
const TASK_LABELS = {
  syntax: "Artery",
  stenosis: "Stenosis",
};

const SEVERITY = {
  minimal: "bg-slate-100 text-slate-700",
  mild: "bg-amber-100 text-amber-800",
  moderate: "bg-orange-100 text-orange-800",
  severe: "bg-red-100 text-red-800",
};

const pct = (v) => (v == null ? "-" : `${(v * 100).toFixed(1)}%`);
const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : "-");

function Card({ title, hint, action, children }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm print:break-inside-avoid">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          {hint && <p className="text-sm text-slate-600">{hint}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function Tile({ value, label, valueClass = "text-slate-900" }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className={`text-2xl font-bold ${valueClass}`}>{value}</p>
      <p className="text-xs text-slate-600">{label}</p>
    </div>
  );
}

function Figure({ src, caption, className = "" }) {
  return (
    <figure>
      {src ? (
        <img
          src={src}
          alt={caption}
          className={`w-full rounded-lg border border-slate-200 bg-slate-900 ${className}`}
        />
      ) : (
        <div className="flex min-h-[160px] items-center justify-center rounded-lg bg-slate-100 text-sm text-slate-500">
          Not available
        </div>
      )}
      <figcaption className="mt-1 text-center text-xs text-slate-600">{caption}</figcaption>
    </figure>
  );
}

function Empty({ children }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-600">
      {children}
    </div>
  );
}

function explainText(c) {
  const parts = [
    `The classifier is ${(c.score * 100).toFixed(1)}% confident that this region is a stenosis.`,
  ];
  if (c.narrowing_pct != null && c.narrowing_pct >= 5) {
    parts.push(
      `The vessel narrows to ${c.narrowest_width_px}px where the normal width nearby is ${c.reference_width_px}px, an estimated ${c.narrowing_pct}% narrowing (${c.severity}).`
    );
  } else if (c.narrowing_pct != null) {
    parts.push(
      "No measurable narrowing was found in the vessel width here. The model flagged this region from its appearance, so it is worth a closer look."
    );
  }
  if (c.location)
    parts.push(
      `It is in the ${c.location} of the image${c.segment ? `, on vessel segment ${c.segment}` : ""}.`
    );
  return parts.join(" ");
}

export default function CaseResults() {
  const { id } = useParams();
  const navigate = useNavigate();
  const startedFor = useRef(null);

  const [c, setCase] = useState(null);
  const [saved, setSaved] = useState({});
  const [pipe, setPipe] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [task, setTask] = useState("syntax");
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const url = (u) => (u ? `${API_URL}${u}?t=${pipe?.ts ?? 0}` : null);

  const runPipeline = async () => {
    setBusy(true);
    setError("");
    try {
      const res = await api.post(`/cases/${id}/stenosis-pipeline`);
      setPipe({ ...res.data, ts: Date.now() });
    } catch (e) {
      setError(e.response?.data?.detail || "The pipeline could not run for this case.");
    } finally {
      setBusy(false);
    }
  };

  // open the result saved by the backend (no model run); returns false if none exists yet
  const loadSavedPipeline = async () => {
    try {
      const res = await fetch(
        `${API_URL}/uploads/results/case_${id}_pipeline.json?t=${Date.now()}`
      );
      if (!res.ok) return false;
      const data = await res.json();
      setPipe({ ...data, ts: Date.now() });
      return true;
    } catch {
      return false;
    }
  };

  // download the report (pdf / csv / json) through axios so the login token is sent
  const downloadReport = async (fmt) => {
    setDownloading(fmt);
    setError("");
    try {
      const res = await api.get(`/cases/${id}/report`, {
        params: { format: fmt },
        responseType: "blob",
      });
      const href = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = href;
      a.download = `report_${c?.patient_id ?? id}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(href);
    } catch (e) {
      setError(
        e.response?.status === 404
          ? "The report endpoint is not available."
          : "Could not download the report. Run the pipeline for this case first."
      );
    } finally {
      setDownloading("");
    }
  };

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const list = await api.get("/cases");
        const found = list.data.find((x) => String(x.id) === String(id));
        if (!alive) return;
        if (!found) {
          setError("Case not found.");
          setLoading(false);
          return;
        }
        setCase(found);
        api.get(`/cases/${id}/results`).then((r) => alive && setSaved(r.data)).catch(() => {});
        api.get("/cases/model-metrics").then((r) => alive && setMetrics(r.data)).catch(() => {});
        api.get("/cases/model-comparison").then((r) => alive && setComparison(r.data)).catch(() => {});
        setLoading(false);
        if (found.image_path && startedFor.current !== id) {
          startedFor.current = id;
          const ok = await loadSavedPipeline();
          if (!ok && alive) runPipeline();
        }
      } catch (e) {
        if (e.response?.status === 401) navigate("/login");
        else setError("Could not load this case. Is the backend running?");
        setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading) return <p className="p-8 text-slate-600">Loading case...</p>;

  const cands = pipe?.candidates ?? [];
  const top = [...cands].sort((a, b) => b.score - a.score)[0];
  const seg = saved[task];
  const scanUrl = c?.image_path ? `${API_URL}/uploads/${c.image_path}` : null;

  const segImages = [
    ["Original", scanUrl],
    ["Overlay", seg ? `${API_URL}${seg.overlay_url}` : null],
    [
      "Mask",
      seg
        ? `${API_URL}${seg.mask_url}`
        : url(task === "syntax" ? pipe?.vessel_mask_url : pipe?.stenosis_mask_url),
    ],
    [
      "Centerline",
      seg?.vessel?.centerline_url
        ? `${API_URL}${seg.vessel.centerline_url}`
        : task === "syntax"
        ? url(pipe?.centerline_url)
        : null,
    ],
  ];
  const vs = seg?.vessel ?? pipe?.vessel_stats;

  // model comparison: best value per task and metric
  const compModels = comparison?.models ?? [];
  const bestOf = (taskName, key) =>
    Math.max(
      ...compModels.filter((m) => m.task === taskName).map((m) => (m[key] == null ? -1 : m[key]))
    );

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <div className="mx-auto max-w-6xl space-y-4 p-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <button
              onClick={() => navigate(-1)}
              className="mb-1 text-sm text-teal-700 hover:underline print:hidden"
            >
              Back to cases
            </button>
            <h1 className="text-2xl font-bold text-slate-900">
              Case {c?.patient_id}: stenosis analysis
            </h1>
            <p className="text-sm text-slate-600">
              {[c?.imaging_modality, c?.anatomical_region, c?.scan_date, pipe?.model_version]
                .filter(Boolean)
                .join(" · ")}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 print:hidden">
            <button
              onClick={runPipeline}
              disabled={busy || !c?.image_path}
              className="min-h-[44px] rounded-lg border border-teal-700 bg-white px-4 text-sm font-semibold text-teal-700 disabled:opacity-50"
            >
              {busy ? "Running..." : pipe ? "Re-run pipeline" : "Run pipeline"}
            </button>
            {["pdf", "csv", "json"].map((fmt) => (
              <button
                key={fmt}
                onClick={() => downloadReport(fmt)}
                disabled={!c?.image_path || downloading === fmt}
                className="min-h-[44px] rounded-lg border border-indigo-600 bg-white px-4 text-sm font-semibold text-indigo-700 disabled:opacity-50"
              >
                {downloading === fmt ? "..." : fmt.toUpperCase()}
              </button>
            ))}
            <button
              onClick={() => window.print()}
              disabled={!pipe}
              className="min-h-[44px] rounded-lg bg-teal-700 px-4 text-sm font-semibold text-white disabled:opacity-50"
            >
              Print
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {!c?.image_path && (
          <Empty>
            This case has no scan yet. Upload one from the Cases page, then open this page again.
          </Empty>
        )}
        {busy && !pipe && <Empty>Running the pipeline. This can take a few seconds on CPU...</Empty>}

        {/* Summary */}
        {pipe && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Tile
              value={top ? cap(top.severity) : "None"}
              label="Severity"
              valueClass={
                top?.severity === "severe"
                  ? "text-red-700"
                  : top?.severity === "moderate"
                  ? "text-orange-700"
                  : "text-slate-900"
              }
            />
            <Tile
              value={top?.narrowing_pct != null ? `${top.narrowing_pct}%` : "-"}
              label="Estimated narrowing"
            />
            <Tile value={top ? top.score : "-"} label="Classifier confidence" />
            <Tile
              value={cands.length}
              label={cands.length === 1 ? "Stenosis candidate" : "Stenosis candidates"}
            />
          </div>
        )}

        {/* 1. Pipeline stages */}
        {pipe && (
          <Card title="1. Pipeline stages" hint="Every step the image went through, in order.">
            <div className="flex flex-wrap gap-2">
              {pipe.stages_done.map((s, i) => (
                <span
                  key={s}
                  className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 text-xs font-medium text-teal-900"
                >
                  {i + 1}. {STAGE_NAMES[s] || cap(s.replace(/_/g, " "))}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* 2. Segmentation */}
        {c?.image_path && (
          <Card
            title="2. Segmentation"
            hint="Original angiogram and the artery masks."
            action={
              <div className="flex gap-2 print:hidden">
                {["syntax", "stenosis"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setTask(t)}
                    className={`min-h-[44px] rounded-lg border px-4 text-sm font-semibold ${
                      task === t
                        ? "border-teal-700 bg-teal-700 text-white"
                        : "border-teal-700 bg-white text-teal-700"
                    }`}
                  >
                    {TASK_LABELS[t]}
                  </button>
                ))}
              </div>
            }
          >
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {segImages.map(([name, src]) => (
                <Figure key={name} src={src} caption={name} />
              ))}
            </div>
            {vs && vs.vessel_segments != null && (
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
                <Tile value={vs.vessel_segments} label="Vessel segments" />
                <Tile value={`${vs.centerline_length_px}px`} label="Centerline length" />
                <Tile value={`${vs.mean_diameter_px}px`} label="Mean diameter" />
                <Tile value={`${vs.max_diameter_px}px`} label="Max diameter" />
                <Tile value={`${vs.min_diameter_px}px`} label="Min diameter" />
              </div>
            )}
          </Card>
        )}

        {/* 3 + 4. Detection and explanation */}
        {pipe && (
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="3. Stenosis detection" hint="Candidate regions found on the angiogram.">
              {cands.length === 0 ? (
                <Empty>No stenosis candidates detected for this case.</Empty>
              ) : (
                <>
                  <Figure src={url(pipe.visualization_url) || scanUrl} caption="Detected regions" />
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-xs text-slate-600">
                        <tr>
                          {["#", "Location", "Segment", "Score", "Narrowing", "Severity"].map((h) => (
                            <th key={h} className="border-b border-slate-200 px-2 py-2 font-medium">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {cands.map((x, i) => (
                          <tr key={i} className="border-b border-slate-100">
                            <td className="px-2 py-2">{i + 1}</td>
                            <td className="px-2 py-2">{cap(x.location)}</td>
                            <td className="px-2 py-2">{x.segment ?? "-"}</td>
                            <td className="px-2 py-2">{x.score}</td>
                            <td className="px-2 py-2">
                              {x.narrowing_pct != null ? `${x.narrowing_pct}%` : "-"}
                            </td>
                            <td className="px-2 py-2">
                              <span
                                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                  SEVERITY[x.severity] || SEVERITY.minimal
                                }`}
                              >
                                {cap(x.severity)}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </Card>

            <Card title="4. Why was this flagged?" hint="Heatmaps show where the classifier looked.">
              {cands.length === 0 ? (
                <Empty>Nothing was flagged, so there is nothing to explain.</Empty>
              ) : (
                <div className="space-y-4">
                  {cands.map((x, i) => (
                    <div key={i}>
                      <p className="mb-1 text-sm font-medium">Region {i + 1}</p>
                      <Figure
                        src={url(x.gradcam_url)}
                        caption="Crop, Grad-CAM, Grad-CAM++ (red = strongest focus)"
                      />
                      <p className="mt-2 rounded-lg bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
                        {explainText(x)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* 5. Final visualization */}
        {pipe?.visualization_url && (
          <Card
            title="5. Final visualization"
            hint="Original, artery segmentation, stenosis region and model explanation in one image."
            action={
              <a
                href={url(pipe.visualization_url)}
                target="_blank"
                rel="noreferrer"
                className="flex min-h-[44px] items-center rounded-lg border border-teal-700 px-4 text-sm font-semibold text-teal-700 print:hidden"
              >
                Open full size
              </a>
            }
          >
            <img
              src={url(pipe.visualization_url)}
              alt="Stenosis visualization"
              className="w-full rounded-lg border border-slate-200"
            />
          </Card>
        )}

        {/* 6. Model performance */}
        {metrics && (
          <Card
            title="6. Model performance"
            hint={`Stenosis classifier on the test set${
              metrics.n_test ? ` (${metrics.n_test} crops)` : ""
            }.`}
          >
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <Tile value={pct(metrics.accuracy)} label="Accuracy" />
              <Tile value={pct(metrics.precision)} label="Precision" />
              <Tile value={pct(metrics.recall)} label="Sensitivity" />
              <Tile value={pct(metrics.specificity)} label="Specificity" />
              <Tile value={metrics.f1 != null ? metrics.f1.toFixed(3) : "-"} label="F1 score" />
              <Tile value={metrics.auc != null ? metrics.auc.toFixed(3) : "-"} label="AUC-ROC" />
            </div>
            <p className="mt-3 text-xs text-slate-600">
              Confusion matrix: TP {metrics.tp}, FP {metrics.fp}, TN {metrics.tn}, FN {metrics.fn}
            </p>
          </Card>
        )}

        {/* 7. Model comparison */}
        {compModels.length > 0 && (
          <Card
            title="7. Model comparison"
            hint="U-Net vs Attention U-Net on the test set. Green marks the best value for each task."
          >
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-slate-600">
                  <tr>
                    {["Model", "Dice", "IoU", "Precision", "Recall"].map((h) => (
                      <th key={h} className="border-b border-slate-200 px-2 py-2 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {compModels.map((m) => (
                    <tr key={m.name} className="border-b border-slate-100">
                      <td className="px-2 py-2 font-medium">{m.name}</td>
                      {["dice", "iou", "precision", "recall"].map((k) => (
                        <td
                          key={k}
                          className={`px-2 py-2 ${
                            m[k] != null && m[k] === bestOf(m.task, k)
                              ? "font-semibold text-emerald-700"
                              : ""
                          }`}
                        >
                          {m[k] != null ? Number(m[k]).toFixed(4) : "-"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {comparison?.note && <p className="mt-3 text-xs text-slate-600">{comparison.note}</p>}
          </Card>
        )}
      </div>
    </div>
  );
}