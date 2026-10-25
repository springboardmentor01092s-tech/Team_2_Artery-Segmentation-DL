import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";

const ROLES = [
  { value: "clinician", label: "Radiologist / Clinician" },
  { value: "researcher", label: "Medical Researcher" },
  { value: "data_scientist", label: "Data Scientist / ML Engineer" },
  { value: "admin", label: "Administrator" },
];

const inputCls =
  "w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200";

function strength(pw) {
  let s = 0;
  if (pw.length >= 8) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return s;
}

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "clinician",
  });
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const score = strength(form.password);
  const barColor = ["bg-slate-200", "bg-red-400", "bg-amber-400", "bg-lime-500", "bg-emerald-500"][score];
  const label = ["", "Weak", "Fair", "Good", "Strong"][score];

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (form.password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/register", form);
      navigate("/login");
    } catch (err) {
      if (!err.response) setError("Cannot reach the server. Is the backend running?");
      else {
        const d = err.response.data?.detail;
        setError(typeof d === "string" ? d : "Please check the details you entered.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-12 text-white lg:flex">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-rose-500/10 blur-3xl" />

        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/90 text-lg">♥</div>
            <span className="text-2xl font-bold tracking-tight">Artery AI</span>
          </div>
          <h1 className="mt-14 text-4xl font-bold leading-tight">
            Join the coronary
            <br />
            analysis platform
          </h1>
          <p className="mt-4 max-w-md text-slate-300">
            Choose the role that fits your work. Access is tailored to what each
            role needs.
          </p>

          <div className="mt-10 space-y-4">
            {[
              ["Radiologist / Clinician", "Manage cases, upload scans and review results"],
              ["Medical Researcher", "Study analyses and compare outcomes"],
              ["Data Scientist / ML Engineer", "Work with models, versions and performance"],
              ["Administrator", "Oversee users, access and audit logs"],
            ].map(([t, d]) => (
              <div key={t} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="font-medium">{t}</p>
                <p className="text-sm text-slate-400">{d}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-slate-500">
          For research and educational use. Public, de-identified datasets only.
        </p>
      </div>

      {/* Right form panel */}
      <div className="flex w-full items-center justify-center bg-slate-50 px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-500 text-white">♥</div>
            <span className="text-xl font-bold text-slate-900">Artery AI</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-900">Create your account</h2>
            <p className="mt-1 text-sm text-slate-500">Set up access to your workspace</p>

            {error && (
              <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Full name</label>
                <input
                  className={inputCls}
                  name="name"
                  placeholder="Dr. Jane Smith"
                  value={form.name}
                  onChange={change}
                  required
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
                <input
                  className={inputCls}
                  name="email"
                  type="email"
                  placeholder="you@hospital.org"
                  value={form.email}
                  onChange={change}
                  required
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Role</label>
                <select className={inputCls} name="role" value={form.role} onChange={change}>
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Password</label>
                <div className="relative">
                  <input
                    className={`${inputCls} pr-16`}
                    name="password"
                    type={show ? "text" : "password"}
                    placeholder="At least 8 characters"
                    value={form.password}
                    onChange={change}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    className="absolute inset-y-0 right-3 text-xs font-medium text-slate-500 hover:text-slate-800"
                  >
                    {show ? "Hide" : "Show"}
                  </button>
                </div>
                {form.password && (
                  <div className="mt-2 flex items-center gap-2">
                    <div className="flex flex-1 gap-1">
                      {[1, 2, 3, 4].map((i) => (
                        <div
                          key={i}
                          className={`h-1.5 flex-1 rounded-full ${i <= score ? barColor : "bg-slate-200"}`}
                        />
                      ))}
                    </div>
                    <span className="w-12 text-xs text-slate-500">{label}</span>
                  </div>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Confirm password</label>
                <input
                  className={inputCls}
                  type={show ? "text" : "password"}
                  placeholder="Re-enter your password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
              >
                {loading ? "Creating account..." : "Create account"}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500">
              Already have an account?{" "}
              <Link to="/login" className="font-medium text-indigo-600 hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}