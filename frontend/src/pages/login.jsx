import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";

const FEATURES = [
  { title: "Artery segmentation", text: "Deep learning vessel masks from angiography images" },
  { title: "Stenosis detection", text: "Locate narrowed regions and estimate severity" },
  { title: "Explainable AI", text: "Heatmaps that show why the model decided" },
  { title: "Clinical reports", text: "Structured reports and full analysis history" },
];

async function requestLogin(email, password) {
  try {
    return await api.post("/auth/login", { email, password });
  } catch (err) {
    if (err.response && [400, 415, 422].includes(err.response.status)) {
      const body = new URLSearchParams();
      body.append("username", email);
      body.append("password", password);
      return await api.post("/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
    }
    throw err;
  }
}

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await requestLogin(email.trim(), password);
      localStorage.setItem("token", res.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      if (!err.response) setError("Cannot reach the server. Is the backend running?");
      else if (err.response.status === 401 || err.response.status === 400)
        setError("Incorrect email or password.");
      else setError("Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-white">
      <style>{`
        @keyframes drawLine { to { stroke-dashoffset: 0; } }
        .ecg { stroke-dasharray: 900; stroke-dashoffset: 900; animation: drawLine 3s ease-out infinite alternate; }
      `}</style>

      {/* Left brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-12 text-white lg:flex">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-rose-500/10 blur-3xl" />

        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/90 text-lg">
              ♥
            </div>
            <span className="text-2xl font-bold tracking-tight">Artery AI</span>
          </div>
          <h1 className="mt-14 text-4xl font-bold leading-tight">
            Intelligent coronary
            <br />
            artery analysis
          </h1>
          <p className="mt-4 max-w-md text-slate-300">
            Segmentation and stenosis detection powered by advanced deep learning,
            built for radiologists, researchers and ML engineers.
          </p>

          <svg viewBox="0 0 600 90" className="mt-8 w-full max-w-md" fill="none">
            <path
              className="ecg"
              d="M0 45 H120 L145 45 L165 10 L190 80 L215 45 H330 L350 45 L370 18 L395 72 L420 45 H600"
              stroke="#fb7185"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>

          <ul className="mt-8 space-y-4">
            {FEATURES.map((f) => (
              <li key={f.title} className="flex gap-3">
                <span className="mt-1 flex h-5 w-5 flex-none items-center justify-center rounded-full bg-indigo-500/30 text-xs text-indigo-200">
                  ✓
                </span>
                <div>
                  <p className="font-medium">{f.title}</p>
                  <p className="text-sm text-slate-400">{f.text}</p>
                </div>
              </li>
            ))}
          </ul>
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
            <h2 className="text-2xl font-bold text-slate-900">Welcome back</h2>
            <p className="mt-1 text-sm text-slate-500">Sign in to your clinical workspace</p>

            {error && (
              <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <form onSubmit={submit} className="mt-6 space-y-5">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
                <input
                  type="email"
                  required
                  autoFocus
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@hospital.org"
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Password</label>
                <div className="relative">
                  <input
                    type={show ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 pr-16 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    className="absolute inset-y-0 right-3 text-xs font-medium text-slate-500 hover:text-slate-800"
                  >
                    {show ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500">
              New to Artery AI?{" "}
              <Link to="/register" className="font-medium text-indigo-600 hover:underline">
                Create an account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}