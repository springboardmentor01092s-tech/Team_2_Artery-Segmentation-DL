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
];

const TITLES = {
  cases: ["Case Management", "Create, review and manage patient cases"],
  syntax: ["Segmentation", "Segment coronary arteries and measure vessels (syntax model)"],
  stenosis: ["Stenosis", "Find suspected stenosis regions (stenosis model)"],
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
  const [view, setView] = useState("cases"); // "cases" | "syntax" | "stenosis"

  // segmentation
  const [seg, setSeg] = useState(null); // result currently shown in the panel
  const [segAll, setSegAll] = useState({}); // saved results of the open case, by task
  const [segMap, setSegMap] = useState({}); // {caseId: ["syntax", ...]} for the lists
  const [segBusy, setSegBusy] = useState(false);
  const [segCaseId, setSegCaseId] = useState(null);

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
          <div className="px-3 py-2 text-slate-500">Reports (soon)</div>
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
                                {t}
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
                          <td className="px-4 py-3">{view === "syntax" ? "U-Net (syntax)" : "U-Net (stenosis)"}</td>
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
                Segmentation result ({seg.task})
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
                    {t}
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
    </div>
  );
}