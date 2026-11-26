import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

const API_URL = "http://127.0.0.1:8000";

const EMPTY = {
  patient_id: "",
  age: "",
  gender: "",
  medical_history: "",
  risk_factors: "",
  clinical_notes: "",
  imaging_modality: "Coronary angiography",
  scan_date: "",
  anatomical_region: "",
};

const ROLE_INFO = {
  clinician: {
    label: "Radiologist / Clinician",
    badge: "bg-indigo-100 text-indigo-700",
    can: ["Create and edit your own cases", "Upload X-ray scans", "Run preprocessing"],
  },
  researcher: {
    label: "Medical Researcher",
    badge: "bg-emerald-100 text-emerald-700",
    can: ["View all cases (read-only)"],
  },
  data_scientist: {
    label: "Data Scientist / ML Engineer",
    badge: "bg-amber-100 text-amber-700",
    can: ["View all cases", "Run preprocessing"],
  },
  admin: {
    label: "Administrator",
    badge: "bg-rose-100 text-rose-700",
    can: ["Full access to all cases", "Audit logging"],
  },
};

const NAV = [
  ["cases", "Cases"],
  ["syntax", "Segmentation"],
  ["stenosis", "Stenosis"],
  ["reports", "Reports"],
];

const TITLES = {
  cases: ["Case Management", "Create, review and manage patient cases"],
  syntax: ["Segmentation", "Segment coronary arteries and measure vessels (artery model)"],
  stenosis: ["Stenosis", "Find suspected stenosis regions (stenosis model)"],
  reports: ["Reports", "Open or download the analysis report of a case"],
};

// display names for the two segmentation tasks (internal names: syntax, stenosis)
const TASK_LABELS = {
  syntax: "Artery",
  stenosis: "Stenosis",
};

const inputCls =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200";

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-600">{label}</span>
      {children}
    </label>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-3xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}

function Badge({ status }) {
  const done = String(status).toLowerCase().includes("complete");
  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
        done ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
      }`}
    >
      {status}
    </span>
  );
}

function MiniStat({ value, label }) {
  return (
    <div className="rounded-lg bg-slate-50 py-2 text-center">
      <p className="text-lg font-semibold text-slate-800">{value}</p>
      <p className="text-[11px] text-slate-500">{label}</p>
    </div>
  );
}

const fmtPct = (v) => (v == null ? "-" : `${(v * 100).toFixed(1)}%`);

// plain-language explanation built from the measured values of one candidate
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
  if (c.location) {
    parts.push(
      `It is located in the ${c.location} of the image${c.segment ? `, on vessel segment ${c.segment}` : ""}.`
    );
  }
  parts.push("The heatmap shows the area the model focused on most (red is strongest).");
  return parts.join(" ");
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [cases, setCases] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [stages, setStages] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [view, setView] = useState("cases"); // "cases" | "syntax" | "stenosis" | "reports"

  // segmentation
  const [seg, setSeg] = useState(null); // result currently shown in the panel
  const [segAll, setSegAll] = useState({}); // saved results of the open case, by task
  const [segMap, setSegMap] = useState({}); // {caseId: ["syntax", ...]} for the lists
  const [segBusy, setSegBusy] = useState(false);
  const [segCaseId, setSegCaseId] = useState(null);

  // stenosis pipeline
  const [pipe, setPipe] = useState(null);
  const [pipeCase, setPipeCase] = useState(null);
  const [pipeBusy, setPipeBusy] = useState(false);
  const [pipeDims, setPipeDims] = useState({ w: 1, h: 1 });

  // classifier performance (shown once the backend endpoint exists)
  const [metrics, setMetrics] = useState(null);

  // U-Net vs Attention U-Net results
  const [comparison, setComparison] = useState(null);

  // report download in progress, e.g. "2-pdf"
  const [downloading, setDownloading] = useState("");

  const canWrite = ["clinician", "admin"].includes(user?.role);
  const canPreprocess = ["clinician", "admin", "data_scientist"].includes(user?.role);
  const roleInfo = ROLE_INFO[user?.role] || {
    label: user?.role || "",
    badge: "bg-slate-100 text-slate-700",
    can: [],
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const loadSummary = async () => {
    try {
      const s = await api.get("/cases/results/summary");
      setSegMap(s.data);
    } catch {
      /* ignore: the lists still work without badges */
    }
  };

  const loadCases = async () => {
    try {
      const res = await api.get("/cases");
      setCases(res.data);
      setError("");
      await loadSummary();
    } catch (e) {
      if (e.response?.status === 401) logout();
      else setError("Could not load cases. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => logout());
    loadCases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (view !== "stenosis" || metrics) return;
    api
      .get("/cases/model-metrics")
      .then((r) => setMetrics(r.data))
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  useEffect(() => {
    if ((view !== "syntax" && view !== "stenosis") || comparison) return;
    api
      .get("/cases/model-comparison")
      .then((r) => setComparison(r.data))
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return cases;
    return cases.filter((c) =>
      [c.patient_id, c.gender, c.anatomical_region, c.imaging_modality]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    );
  }, [cases, search]);

  const stats = {
    total: cases.length,
    pending: cases.filter((c) => !String(c.analysis_status).toLowerCase().includes("complete")).length,
    withImage: cases.filter((c) => c.image_path).length,
    preprocessed: cases.filter((c) => String(c.analysis_status).toLowerCase().includes("preprocess")).length,
  };

  // model comparison rows for the open tab (syntax = artery, stenosis = stenosis)
  const compRows = (comparison?.models || []).filter((m) => m.task === view);
  const bestOf = (key) => Math.max(...compRows.map((m) => (m[key] == null ? -1 : m[key])));

  const openNew = () => {
    setEditingId(null);
    setForm(EMPTY);
    setModalOpen(true);
  };

  const openEdit = (c) => {
    setEditingId(c.id);
    setForm({
      patient_id: c.patient_id ?? "",
      age: c.age ?? "",
      gender: c.gender ?? "",
      medical_history: c.medical_history ?? "",
      risk_factors: c.risk_factors ?? "",
      clinical_notes: c.clinical_notes ?? "",
      imaging_modality: c.imaging_modality ?? "",
      scan_date: c.scan_date ?? "",
      anatomical_region: c.anatomical_region ?? "",
    });
    setModalOpen(true);
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = async (e) => {
    e.preventDefault();
    if (!form.patient_id.trim()) {
      setError("Patient ID is required.");
      return;
    }
    setSaving(true);
    const payload = {};
    Object.keys(form).forEach((k) => {
      payload[k] = form[k] === "" ? null : form[k];
    });
    payload.patient_id = form.patient_id.trim();
    payload.age = form.age === "" ? null : Number(form.age);
    try {
      if (editingId) await api.put(`/cases/${editingId}`, payload);
      else await api.post("/cases", payload);
      setModalOpen(false);
      setError("");
      await loadCases();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save the case. Please check the fields.");
    } finally {
      setSaving(false);
    }
  };

  const uploadImage = async (id, file) => {
    if (!file) return;
    const data = new FormData();
    data.append("file", file);
    try {
      await api.post(`/cases/${id}/upload`, data);
      await loadCases();
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed.");
    }
  };

  const preprocess = async (id) => {
    try {
      const res = await api.post(`/cases/${id}/preprocess`);
      setStages(res.data.stages);
      await loadCases();
    } catch (e) {
      setError(e.response?.data?.detail || "Preprocessing failed.");
    }
  };

  // run the model (and save the result on the server)
  const runSegment = async (id, task = "syntax") => {
    setSegBusy(true);
    if (id !== segCaseId) setSegAll({});
    setSegCaseId(id);
    setError("");
    try {
      const res = await api.post(`/cases/${id}/segment`, null, { params: { task } });
      setSeg({ ...res.data, ts: Date.now() });
      setSegAll((prev) => ({ ...prev, [task]: res.data }));
      await loadSummary();
    } catch (e) {
      setError(e.response?.data?.detail || "Segmentation failed.");
    } finally {
      setSegBusy(false);
    }
  };

  // reopen saved results (no model run)
  const viewResults = async (id, preferred) => {
    try {
      const res = await api.get(`/cases/${id}/results`);
      const data = res.data;
      const first =
        preferred && data[preferred]
          ? preferred
          : data.syntax
          ? "syntax"
          : Object.keys(data)[0];
      if (!first) {
        setError("No saved results for this case yet.");
        return;
      }
      setSegCaseId(id);
      setSegAll(data);
      setSeg({ ...data[first], ts: Date.now() });
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load saved results.");
    }
  };

  // switch task in the panel: show saved result if there is one, else run the model
  const showTask = (t) => {
    if (segAll[t]) setSeg({ ...segAll[t], ts: Date.now() });
    else runSegment(segCaseId, t);
  };

  // run the full stenosis detection pipeline
  const runPipeline = async (c) => {
    setPipeBusy(true);
    setPipeCase(c);
    setError("");
    try {
      const res = await api.post(`/cases/${c.id}/stenosis-pipeline`);
      setPipe({ ...res.data, ts: Date.now() });
    } catch (e) {
      setError(e.response?.data?.detail || "Stenosis pipeline failed.");
    } finally {
      setPipeBusy(false);
    }
  };

  // download a report (pdf / csv / json). Goes through axios so the login token is sent.
  const downloadReport = async (c, fmt) => {
    const key = `${c.id}-${fmt}`;
    setDownloading(key);
    setError("");
    try {
      const res = await api.get(`/cases/${c.id}/report`, {
        params: { format: fmt },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `report_${c.patient_id}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(
        e.response?.status === 404
          ? "The report endpoint is not available yet."
          : "Could not download the report. Run the stenosis pipeline for this case first."
      );
    } finally {
      setDownloading("");
    }
  };

  const confirmDelete = async () => {
    try {
      await api.delete(`/cases/${deleteTarget.id}`);
      setDeleteTarget(null);
      await loadCases();
    } catch (e) {
      setError(e.response?.data?.detail || "Could not delete the case.");
      setDeleteTarget(null);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800">
      {/* Sidebar */}
      <aside className="hidden w-60 flex-col bg-slate-900 p-5 text-slate-200 md:flex">
        <div className="mb-8">
          <h1 className="text-xl font-bold text-white">Artery AI</h1>
          <p className="text-xs text-slate-400">Coronary analysis platform</p>
        </div>
        <nav className="space-y-1 text-sm">
          {NAV.map(([key, label]) => (
            <button
              key={key}
              onClick={() => {
                setView(key);
                setSearch("");
              }}
              className={`block w-full rounded-lg px-3 py-2 text-left ${
                view === key
                  ? "bg-indigo-600 font-medium text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
        <button
          onClick={logout}
          className="mt-auto rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
        >
          Logout
        </button>
      </aside>

      {/* Main */}
      <div className="flex-1">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">{TITLES[view][0]}</h2>
            <p className="text-xs text-slate-500">{TITLES[view][1]}</p>
          </div>

          {/* Profile menu */}
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-3 rounded-lg px-2 py-1 hover:bg-slate-100"
            >
              <div className="text-right text-sm">
                <p className="font-medium">{user?.name ?? "..."}</p>
                <p className="text-xs text-slate-500">{roleInfo.label}</p>
              </div>
              <div className="relative flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 font-semibold text-white">
                {user?.name?.[0]?.toUpperCase() ?? "U"}
                <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
              </div>
            </button>

            {menuOpen && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 z-40 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
                  {/* Banner */}
                  <div className="h-20 bg-gradient-to-r from-slate-900 via-indigo-900 to-rose-700" />
                  <div className="px-5 pb-5">
                    <div className="-mt-9 flex h-[72px] w-[72px] items-center justify-center rounded-full border-4 border-white bg-gradient-to-br from-indigo-500 to-violet-500 text-3xl font-bold text-white shadow">
                      {user?.name?.[0]?.toUpperCase() ?? "U"}
                    </div>
                    <p className="mt-3 text-lg font-semibold leading-tight">{user?.name}</p>
                    <p className="text-sm text-slate-500">{user?.email}</p>
                    <span className={`mt-3 inline-block rounded-full px-3 py-1 text-xs font-medium ${roleInfo.badge}`}>
                      {roleInfo.label}
                    </span>

                    <div className="mt-4 grid grid-cols-3 gap-2">
                      <MiniStat value={stats.total} label="Cases" />
                      <MiniStat value={stats.withImage} label="Scans" />
                      <MiniStat value={stats.preprocessed} label="Processed" />
                    </div>

                    {roleInfo.can.length > 0 && (
                      <div className="mt-4">
                        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
                          Your access
                        </p>
                        <ul className="space-y-1.5 text-sm text-slate-600">
                          {roleInfo.can.map((c) => (
                            <li key={c} className="flex items-start gap-2">
                              <span className="mt-0.5 text-emerald-500">✓</span>
                              {c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <button
                      onClick={logout}
                      className="mt-5 w-full rounded-lg bg-slate-900 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </header>

        <main className="space-y-6 p-6">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {view === "cases" && (
            <div className="grid gap-4 sm:grid-cols-3">
              <StatCard label="Total cases" value={stats.total} color="text-indigo-600" />
              <StatCard label="Awaiting analysis" value={stats.pending} color="text-amber-600" />
              <StatCard label="With scan uploaded" value={stats.withImage} color="text-emerald-600" />
            </div>
          )}

          {/* Model comparison: U-Net vs Attention U-Net (Segmentation and Stenosis tabs) */}
          {(view === "syntax" || view === "stenosis") && compRows.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700">
                {view === "syntax" ? "Artery segmentation" : "Stenosis segmentation"}: model comparison (test set)
              </h3>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-2">Model</th>
                      <th className="px-4 py-2">Dice</th>
                      <th className="px-4 py-2">IoU</th>
                      <th className="px-4 py-2">Precision</th>
                      <th className="px-4 py-2">Recall</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {compRows.map((m) => (
                      <tr key={m.name}>
                        <td className="px-4 py-2 font-medium">{m.name}</td>
                        {["dice", "iou", "precision", "recall"].map((k) => (
                          <td
                            key={k}
                            className={`px-4 py-2 ${
                              m[k] != null && m[k] === bestOf(k)
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
              <p className="mt-3 text-xs text-slate-500">
                Green marks the best value in each column.
                {comparison?.note ? ` ${comparison.note}` : ""}
              </p>
            </div>
          )}

          {/* Classifier performance (appears once the backend metrics endpoint exists) */}
          {view === "stenosis" && metrics && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700">
                Stenosis classifier performance (test set{metrics.n_test ? `, ${metrics.n_test} crops` : ""})
              </h3>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-6">
                <MiniStat value={fmtPct(metrics.accuracy)} label="Accuracy" />
                <MiniStat value={fmtPct(metrics.precision)} label="Precision" />
                <MiniStat value={fmtPct(metrics.recall)} label="Sensitivity (recall)" />
                <MiniStat value={fmtPct(metrics.specificity)} label="Specificity" />
                <MiniStat value={metrics.f1 != null ? metrics.f1.toFixed(3) : "-"} label="F1-score" />
                <MiniStat value={metrics.auc != null ? metrics.auc.toFixed(3) : "-"} label="AUC-ROC" />
              </div>
              <p className="mt-3 text-xs text-slate-500">
                Confusion matrix: TP {metrics.tp}, FP {metrics.fp}, TN {metrics.tn}, FN {metrics.fn}
              </p>
            </div>
          )}

          {view === "cases" ? (
            /* ---------- Cases ---------- */
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-4">
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by patient ID, gender, region..."
                  className={`${inputCls} max-w-sm`}
                />
                {canWrite && (
                  <button
                    onClick={openNew}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                  >
                    + New Case
                  </button>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Patient ID</th>
                      <th className="px-4 py-3">Age / Gender</th>
                      <th className="px-4 py-3">Modality</th>
                      <th className="px-4 py-3">Region</th>
                      <th className="px-4 py-3">Scan date</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {loading && (
                      <tr>
                        <td colSpan="7" className="px-4 py-10 text-center text-slate-400">
                          Loading cases...
                        </td>
                      </tr>
                    )}
                    {!loading && filtered.length === 0 && (
                      <tr>
                        <td colSpan="7" className="px-4 py-10 text-center text-slate-400">
                          {canWrite ? 'No cases yet. Click "New Case" to add one.' : "No cases to show."}
                        </td>
                      </tr>
                    )}
                    {filtered.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium">
                          <div className="flex items-center gap-3">
                            {c.image_path && (
                              <img
                                src={`${API_URL}/uploads/${c.image_path}`}
                                alt="scan"
                                className="h-10 w-10 rounded object-cover"
                              />
                            )}
                            {c.patient_id}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {c.age ?? "-"} / {c.gender ?? "-"}
                        </td>
                        <td className="px-4 py-3">{c.imaging_modality ?? "-"}</td>
                        <td className="px-4 py-3">{c.anatomical_region ?? "-"}</td>
                        <td className="px-4 py-3">{c.scan_date ?? "-"}</td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap items-center gap-1">
                            <Badge status={c.analysis_status} />
                            {(segMap[c.id] || []).map((t) => (
                              <span
                                key={t}
                                className="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium text-violet-700"
                              >
                                {TASK_LABELS[t] || t}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right">
                          {canWrite && (
                            <label className="mr-3 cursor-pointer text-emerald-600 hover:underline">
                              {c.image_path ? "Replace scan" : "Upload scan"}
                              <input
                                type="file"
                                accept="image/png,image/jpeg"
                                className="hidden"
                                onChange={(e) => uploadImage(c.id, e.target.files[0])}
                              />
                            </label>
                          )}
                          {canPreprocess && c.image_path && (
                            <button
                              onClick={() => preprocess(c.id)}
                              className="mr-3 text-slate-700 hover:underline"
                            >
                              Preprocess
                            </button>
                          )}
                          {canPreprocess && c.image_path && (
                            <button
                              onClick={() => runSegment(c.id, "syntax")}
                              disabled={segBusy && segCaseId === c.id}
                              className="mr-3 text-violet-600 hover:underline disabled:opacity-50"
                            >
                              {segBusy && segCaseId === c.id ? "Segmenting..." : "Segment"}
                            </button>
                          )}
                          {(segMap[c.id] || []).length > 0 && (
                            <button
                              onClick={() => viewResults(c.id)}
                              className="mr-3 text-fuchsia-600 hover:underline"
                            >
                              Results
                            </button>
                          )}
                          {canWrite && (
                            <button
                              onClick={() => openEdit(c)}
                              className="mr-3 text-indigo-600 hover:underline"
                            >
                              Edit
                            </button>
                          )}
                          {canWrite && (
                            <button
                              onClick={() => setDeleteTarget(c)}
                              className="text-red-600 hover:underline"
                            >
                              Delete
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : view === "reports" ? (
            /* ---------- Reports ---------- */
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 p-4">
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by patient ID, gender, region..."
                  className={`${inputCls} max-w-sm`}
                />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Patient ID</th>
                      <th className="px-4 py-3">Age / Gender</th>
                      <th className="px-4 py-3">Region</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Report</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {loading && (
                      <tr>
                        <td colSpan="5" className="px-4 py-10 text-center text-slate-400">
                          Loading cases...
                        </td>
                      </tr>
                    )}
                    {!loading && filtered.length === 0 && (
                      <tr>
                        <td colSpan="5" className="px-4 py-10 text-center text-slate-400">
                          No cases to show.
                        </td>
                      </tr>
                    )}
                    {filtered.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium">
                          <div className="flex items-center gap-3">
                            {c.image_path && (
                              <img
                                src={`${API_URL}/uploads/${c.image_path}`}
                                alt="scan"
                                className="h-10 w-10 rounded object-cover"
                              />
                            )}
                            {c.patient_id}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {c.age ?? "-"} / {c.gender ?? "-"}
                        </td>
                        <td className="px-4 py-3">{c.anatomical_region ?? "-"}</td>
                        <td className="px-4 py-3">
                          <Badge status={c.analysis_status} />
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right">
                          {!c.image_path ? (
                            <span className="text-xs text-slate-400">No scan uploaded</span>
                          ) : (
                            <>
                              <button
                                onClick={() => navigate(`/cases/${c.id}/analysis`)}
                                className="mr-3 text-teal-700 hover:underline"
                              >
                                Open
                              </button>
                              {["pdf", "csv", "json"].map((fmt) => (
                                <button
                                  key={fmt}
                                  onClick={() => downloadReport(c, fmt)}
                                  disabled={downloading === `${c.id}-${fmt}`}
                                  className="mr-2 rounded-lg border border-indigo-300 px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50 disabled:opacity-50"
                                >
                                  {downloading === `${c.id}-${fmt}` ? "..." : fmt.toUpperCase()}
                                </button>
                              ))}
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            /* ---------- Segmentation / Stenosis ---------- */
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 p-4">
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by patient ID, gender, region..."
                  className={`${inputCls} max-w-sm`}
                />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Patient ID</th>
                      <th className="px-4 py-3">Age / Gender</th>
                      <th className="px-4 py-3">Region</th>
                      <th className="px-4 py-3">Model</th>
                      <th className="px-4 py-3">Result</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {loading && (
                      <tr>
                        <td colSpan="6" className="px-4 py-10 text-center text-slate-400">
                          Loading cases...
                        </td>
                      </tr>
                    )}
                    {!loading && filtered.length === 0 && (
                      <tr>
                        <td colSpan="6" className="px-4 py-10 text-center text-slate-400">
                          No cases to show.
                        </td>
                      </tr>
                    )}
                    {filtered.map((c) => {
                      const done = (segMap[c.id] || []).includes(view);
                      const busy = segBusy && segCaseId === c.id;
                      return (
                        <tr key={c.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-medium">
                            <div className="flex items-center gap-3">
                              {c.image_path && (
                                <img
                                  src={`${API_URL}/uploads/${c.image_path}`}
                                  alt="scan"
                                  className="h-10 w-10 rounded object-cover"
                                />
                              )}
                              {c.patient_id}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {c.age ?? "-"} / {c.gender ?? "-"}
                          </td>
                          <td className="px-4 py-3">{c.anatomical_region ?? "-"}</td>
                          <td className="px-4 py-3">{view === "syntax" ? "U-Net (artery)" : "U-Net (stenosis)"}</td>
                          <td className="px-4 py-3">
                            {!c.image_path ? (
                              <span className="text-xs text-slate-400">No scan uploaded</span>
                            ) : done ? (
                              <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">
                                Done
                              </span>
                            ) : (
                              <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700">
                                Not run
                              </span>
                            )}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-right">
                            {canPreprocess && c.image_path && (
                              <button
                                onClick={() => runSegment(c.id, view)}
                                disabled={busy}
                                className="mr-3 text-violet-600 hover:underline disabled:opacity-50"
                              >
                                {busy ? "Running..." : done ? "Re-run" : "Run"}
                              </button>
                            )}
                            {done && (
                              <button
                                onClick={() => viewResults(c.id, view)}
                                className="text-fuchsia-600 hover:underline"
                              >
                                View result
                              </button>
                            )}
                            {view === "stenosis" && canPreprocess && c.image_path && (
                              <button
                                onClick={() => runPipeline(c)}
                                disabled={pipeBusy}
                                className="ml-3 text-indigo-600 hover:underline disabled:opacity-50"
                              >
                                {pipeBusy && pipeCase?.id === c.id ? "Running pipeline..." : "Pipeline"}
                              </button>
                            )}
                            {view === "stenosis" && c.image_path && (
                              <button
                                onClick={() => navigate(`/cases/${c.id}/analysis`)}
                                className="ml-3 text-teal-700 hover:underline"
                              >
                                Full report
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* New / Edit modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <form
            onSubmit={save}
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
          >
            <h3 className="mb-4 text-lg font-semibold">
              {editingId ? "Edit Case" : "New Case"}
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Patient ID *">
                <input className={inputCls} value={form.patient_id} onChange={set("patient_id")} />
              </Field>
              <Field label="Age">
                <input type="number" min="0" className={inputCls} value={form.age} onChange={set("age")} />
              </Field>
              <Field label="Gender">
                <select className={inputCls} value={form.gender} onChange={set("gender")}>
                  <option value="">Select</option>
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </select>
              </Field>
              <Field label="Scan date">
                <input type="date" className={inputCls} value={form.scan_date} onChange={set("scan_date")} />
              </Field>
              <Field label="Imaging modality">
                <input className={inputCls} value={form.imaging_modality} onChange={set("imaging_modality")} />
              </Field>
              <Field label="Anatomical region">
                <input
                  className={inputCls}
                  placeholder="e.g. LAD, RCA"
                  value={form.anatomical_region}
                  onChange={set("anatomical_region")}
                />
              </Field>
            </div>
            <div className="mt-4 space-y-4">
              <Field label="Medical history">
                <textarea rows="2" className={inputCls} value={form.medical_history} onChange={set("medical_history")} />
              </Field>
              <Field label="Risk factors">
                <textarea rows="2" className={inputCls} value={form.risk_factors} onChange={set("risk_factors")} />
              </Field>
              <Field label="Clinical notes">
                <textarea rows="3" className={inputCls} value={form.clinical_notes} onChange={set("clinical_notes")} />
              </Field>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {saving ? "Saving..." : editingId ? "Save changes" : "Create case"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Delete confirmation */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold">Delete case?</h3>
            <p className="mt-2 text-sm text-slate-600">
              Patient {deleteTarget.patient_id} will be removed permanently.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preprocessing results */}
      {stages && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">Preprocessing pipeline</h3>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {stages.map((s) => (
                <div key={s.name}>
                  <img
                    src={`${API_URL}${s.url}`}
                    alt={s.name}
                    className="w-full rounded-lg border"
                  />
                  <p className="mt-1 text-center text-xs text-slate-600">
                    {s.name.replace(/^\d_/, "")}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-4 text-right">
              <button
                onClick={() => setStages(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Segmentation results */}
      {seg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-lg font-semibold">
                Segmentation result ({TASK_LABELS[seg.task] || seg.task})
              </h3>
              <div className="flex items-center gap-2">
                {segBusy && <span className="text-xs text-slate-500">Running...</span>}
                {["syntax", "stenosis"].map((t) => (
                  <button
                    key={t}
                    onClick={() => showTask(t)}
                    disabled={segBusy}
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                      seg.task === t
                        ? "bg-indigo-600 text-white"
                        : "border border-slate-300 text-slate-700"
                    } disabled:opacity-50`}
                  >
                    {TASK_LABELS[t]}
                    {segAll[t] ? " ✓" : ""}
                  </button>
                ))}
                <button
                  onClick={() => runSegment(segCaseId, seg.task)}
                  disabled={segBusy}
                  className="rounded-lg border border-violet-300 px-3 py-1.5 text-xs font-medium text-violet-700 disabled:opacity-50"
                >
                  Re-run
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {[
                ["Overlay", seg.overlay_url],
                ["Mask", seg.mask_url],
                ["Centerline", seg.vessel?.centerline_url],
              ]
                .filter(([, u]) => u)
                .map(([name, u]) => (
                  <div key={name}>
                    <img
                      src={`${API_URL}${u}?t=${seg.ts}`}
                      alt={name}
                      className="w-full rounded-lg border"
                    />
                    <p className="mt-1 text-center text-xs text-slate-600">{name}</p>
                  </div>
                ))}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              <MiniStat value={`${seg.foreground_percent}%`} label="Vessel area" />
              <MiniStat value={seg.max_probability} label="Max probability" />
              <MiniStat value={seg.threshold} label="Threshold" />
              <MiniStat value={seg.model_version} label="Model" />
            </div>

            {seg.vessel && (
              <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5">
                <MiniStat value={seg.vessel.vessel_segments} label="Segments" />
                <MiniStat value={`${seg.vessel.centerline_length_px}px`} label="Centerline" />
                <MiniStat value={`${seg.vessel.mean_diameter_px}px`} label="Mean diameter" />
                <MiniStat value={`${seg.vessel.max_diameter_px}px`} label="Max diameter" />
                <MiniStat value={`${seg.vessel.min_diameter_px}px`} label="Min diameter" />
              </div>
            )}

            <div className="mt-4 text-right">
              <button
                onClick={() => setSeg(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stenosis pipeline results */}
      {pipe && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[90vh] w-full max-w-6xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-lg font-semibold">
                Stenosis detection pipeline: {pipeCase?.patient_id}
              </h3>
              <div className="flex flex-wrap gap-1">
                {pipe.stages_done.map((s, i) => (
                  <span
                    key={s}
                    className="rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-medium text-emerald-700"
                  >
                    {i + 1}. {s.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
              {[
                ["1. Scan", pipeCase?.image_path ? `/uploads/${pipeCase.image_path}` : null],
                ["2. Vessel mask", pipe.vessel_mask_url],
                ["3. Centerline", pipe.centerline_url],
                ["4. Stenosis mask", pipe.stenosis_mask_url],
              ]
                .filter(([, u]) => u)
                .map(([name, u]) => (
                  <div key={name}>
                    <img
                      src={`${API_URL}${u}?t=${pipe.ts}`}
                      alt={name}
                      onLoad={
                        name.startsWith("4")
                          ? (e) =>
                              setPipeDims({
                                w: e.target.naturalWidth,
                                h: e.target.naturalHeight,
                              })
                          : undefined
                      }
                      className="w-full rounded-lg border"
                    />
                    <p className="mt-1 text-center text-xs text-slate-600">{name}</p>
                  </div>
                ))}

              {/* 5. candidates drawn on the scan */}
              <div>
                <div
                  className="relative overflow-hidden rounded-lg border"
                  style={{ aspectRatio: `${pipeDims.w} / ${pipeDims.h}` }}
                >
                  {pipeCase?.image_path && (
                    <img
                      src={`${API_URL}/uploads/${pipeCase.image_path}?t=${pipe.ts}`}
                      alt="candidates"
                      className="h-full w-full object-fill"
                    />
                  )}
                  {pipe.candidates.map((c, i) => (
                    <div
                      key={i}
                      className="absolute border-2 border-red-500"
                      style={{
                        left: `${(c.bbox[0] / pipeDims.w) * 100}%`,
                        top: `${(c.bbox[1] / pipeDims.h) * 100}%`,
                        width: `${(c.bbox[2] / pipeDims.w) * 100}%`,
                        height: `${(c.bbox[3] / pipeDims.h) * 100}%`,
                      }}
                    >
                      <span className="absolute -top-5 left-0 rounded bg-red-500 px-1 text-[10px] text-white">
                        {c.score}
                      </span>
                      {c.centerline_point && (
                        <span
                          className="absolute h-2 w-2 rounded-full bg-yellow-300 ring-1 ring-red-600"
                          style={{
                            left: `${((c.centerline_point[0] - c.bbox[0]) / c.bbox[2]) * 100}%`,
                            top: `${((c.centerline_point[1] - c.bbox[1]) / c.bbox[3]) * 100}%`,
                            transform: "translate(-50%, -50%)",
                          }}
                        />
                      )}
                    </div>
                  ))}
                </div>
                <p className="mt-1 text-center text-xs text-slate-600">5. Candidates</p>
              </div>
            </div>

            {pipe.vessel_stats && (
              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
                <MiniStat value={pipe.vessel_stats.vessel_segments} label="Segments" />
                <MiniStat value={`${pipe.vessel_stats.centerline_length_px}px`} label="Centerline" />
                <MiniStat value={`${pipe.vessel_stats.mean_diameter_px}px`} label="Mean diameter" />
                <MiniStat value={`${pipe.vessel_stats.max_diameter_px}px`} label="Max diameter" />
                <MiniStat value={`${pipe.vessel_stats.min_diameter_px}px`} label="Min diameter" />
              </div>
            )}

            <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-2">#</th>
                    <th className="px-4 py-2">Box (x, y, w, h)</th>
                    <th className="px-4 py-2">Score</th>
                    <th className="px-4 py-2">Location</th>
                    <th className="px-4 py-2">Segment</th>
                    <th className="px-4 py-2">Vessel width</th>
                    <th className="px-4 py-2">Severity</th>
                    <th className="px-4 py-2">Narrowing</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {pipe.candidates.length === 0 && (
                    <tr>
                      <td colSpan="8" className="px-4 py-4 text-center text-slate-400">
                        No candidate regions found.
                      </td>
                    </tr>
                  )}
                  {pipe.candidates.map((c, i) => (
                    <tr key={i}>
                      <td className="px-4 py-2">{i + 1}</td>
                      <td className="px-4 py-2">{c.bbox.join(", ")}</td>
                      <td className="px-4 py-2">{c.score}</td>
                      <td className="px-4 py-2">{c.location ?? "-"}</td>
                      <td className="px-4 py-2">{c.segment ?? "-"}</td>
                      <td className="px-4 py-2">
                        {c.local_diameter_px != null ? `${c.local_diameter_px}px` : "-"}
                      </td>
                      <td className="px-4 py-2">{c.severity ?? "-"}</td>
                      <td className="px-4 py-2">
                        {c.narrowing_pct != null ? `${c.narrowing_pct}%` : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Combined stenosis visualization (Task 8) */}
            {pipe.visualization_url && (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <h4 className="text-sm font-semibold text-slate-700">
                    Stenosis visualization (original + artery segmentation + stenosis regions + model explanation)
                  </h4>
                  <a
                    href={`${API_URL}${pipe.visualization_url}?t=${pipe.ts}`}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg border border-indigo-300 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50"
                  >
                    Open full size
                  </a>
                </div>
                <img
                  src={`${API_URL}${pipe.visualization_url}?t=${pipe.ts}`}
                  alt="Stenosis visualization"
                  className="w-full max-w-3xl rounded-lg border"
                />
              </div>
            )}

            {/* Explainable AI: heatmaps + plain-language reason for every region */}
            {pipe.candidates.length > 0 && (
              <div className="mt-4 space-y-3">
                <h4 className="text-sm font-semibold text-slate-700">
                  Why was this flagged? (explainable AI)
                </h4>
                {pipe.candidates.map((c, i) => (
                  <div
                    key={i}
                    className="flex flex-wrap items-center gap-4 rounded-lg border border-slate-200 bg-slate-50 p-3"
                  >
                    {c.gradcam_url && (
                      <img
                        src={`${API_URL}${c.gradcam_url}?t=${pipe.ts}`}
                        alt={`Grad-CAM region ${i + 1}`}
                        className="h-36 rounded-lg border"
                      />
                    )}
                    <div className="min-w-[240px] flex-1 text-sm text-slate-700">
                      <p className="mb-1 font-medium">Region {i + 1}</p>
                      <p>{explainText(c)}</p>
                      <p className="mt-1 text-xs text-slate-400">
                        Panels: crop, Grad-CAM, Grad-CAM++. Red marks where the model focused most.
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 text-right">
              <button
                onClick={() => setPipe(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}