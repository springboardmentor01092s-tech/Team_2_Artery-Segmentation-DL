import { FormEvent, useEffect, useRef, useState } from "react";
import { apiUrl, request } from "./api";
import AccountPanel, { type User } from "./AccountPanel";
import AdminPanel from "./AdminPanel";
import OverviewPanel from "./OverviewPanel";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";
import { Input } from "./components/prismui/input";
import { Label } from "./components/prismui/label";
import { GoogleLogo } from "./SocialLogos";
import { Building2 } from "lucide-react";
import Auth7 from "./components/ui/auth-07";
import CaseDetails from "./CaseDetails";
import CaseWorkflow from "./CaseWorkflow";
import AnalysisHistory from "./AnalysisHistory";
import DocumentUploader from "./components/ui/file-upload-5";
import { SwitchMode } from "./components/watermelon/switch-mode";
import { MacOSSidebar, type SidebarView } from "./components/watermelon/macos-sidebar";
import ModelWorkspace from "./ModelWorkspace";
import AnalysisWorkbench from "./AnalysisWorkbench";
import ReportsPage from "./ReportsPage";
import VolumeIntake from "./VolumeIntake";
import VolumeInference from './VolumeInference';
import TaskInference from './TaskInference';
import NotificationBell from "./NotificationBell";
import Alert1 from "./components/watermelon/alert-1";
import ViewerWorkspace from "./ViewerWorkspace";
import RoleWorkspace from "./RoleWorkspace";
import ReviewQueue from "./ReviewQueue";
import ReviewAssessment from "./ReviewAssessment";
import { runForImage } from './reviewEvidence';
import ScreenShareSelect from "./ScreenShareSelect";
import { CreateNewDisclosure } from "./components/watermelon/create-new-disclosure";
import { standardPipelines, type StandardPipeline } from "./preprocessingPipelines";
import { caseTasks, caseAnatomies, taskLabel } from "./caseConfiguration";
import { restoreUserDesign } from "./designPreview";
import type { AnalysisJob, AnalysisResult, CaseRecord } from "./caseTypes";
import { canCreateCases, canReadCases, canViewModels, canOpenSection } from "./permissions";
import { forgetAccount, localDemo, saveAccount, saveDemoAccounts, savedAccounts, type SavedAccount } from "./demoSessions";

const TOKEN_KEY = "artery-analysis-token";

function App() {
  const [token, setToken] = useState(() => {
    return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || "";
  });
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => { restoreUserDesign(user?.id); }, [user?.id]);
  const [activeView, setActiveView] = useState<SidebarView>("overview");
  const [reviewWorkspace, setReviewWorkspace] = useState(false);
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selectedImageId, setSelectedImageId] = useState("");
  const [preview, setPreview] = useState("");
  const [previewOwner, setPreviewOwner] = useState('');
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>([]);
  const [overlay, setOverlay] = useState("");
  const [modelsReady, setModelsReady] = useState(false);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [analysisJob, setAnalysisJob] = useState<AnalysisJob | null>(null);
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [registering, setRegistering] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetStep, setResetStep] = useState<"request" | "confirm">("request");
  const [resetContact, setResetContact] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [capabilities, setCapabilities] = useState({ google: false, institutional_sso: false, email_reset: false });
  const [rememberMe, setRememberMe] = useState(true);
  const [demoAccounts, setDemoAccounts] = useState<SavedAccount[]>(savedAccounts);
  const [authNotice, setAuthNotice] = useState("");
  const [caseCode, setCaseCode] = useState("");
  const [newCaseOpen, setNewCaseOpen] = useState(false);
  const [caseFinderOpen, setCaseFinderOpen] = useState(false);
  const [newModality, setNewModality] = useState("XCA");
  const [newAnatomy, setNewAnatomy] = useState("coronary");
  const [newTasks, setNewTasks] = useState<string[]>(["artery_and_stenosis"]);
  const [newSource, setNewSource] = useState("");
  const [caseSection, setCaseSection] = useState("overview");
  useEffect(() => { if (activeView === "uploads") setCaseSection("assets"); }, [activeView]);
  useEffect(() => { if (user && !canOpenSection(activeView, user.role, user.permissions)) setActiveView("overview"); }, [activeView, user?.role, user?.permissions]);
  const [files, setFiles] = useState<File[]>([]);
  const [roi, setRoi] = useState("");
  const [frameIndex, setFrameIndex] = useState("");
  const [pageIndex, setPageIndex] = useState("");
  const [uploadMode, setUploadMode] = useState<"inference" | "dataset">("inference");
  const [preprocessingProfile, setPreprocessingProfile] = useState<"standard" | "research">("standard");
  const [standardPipeline, setStandardPipeline] = useState<StandardPipeline>("baseline");
  const [denoise, setDenoise] = useState(false);
  const [enhance, setEnhance] = useState(false);
  useEffect(() => {
    setUploadMode("inference");
    setPreprocessingProfile("standard");
    setStandardPipeline("baseline");
    setDenoise(false);
    setEnhance(false);
  }, [user?.id]);
  const [busy, setBusy] = useState(false);
  const uploadInFlight = useRef(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [caseSearch, setCaseSearch] = useState("");
  const [caseStatus, setCaseStatus] = useState("all");
  const [caseModality, setCaseModality] = useState("all");
  const [caseTaskFilter, setCaseTaskFilter] = useState("all");
  const [caseSort, setCaseSort] = useState<"newest" | "oldest" | "code">("newest");
  const [casePage, setCasePage] = useState(1);
  const [uploadProgress, setUploadProgress] = useState<{ done: number; total: number; name: string } | null>(null);
  const caseFetchSeq = useRef(0);
  const [caseListToken, setCaseListToken] = useState("");
  const requestedCaseNavigation = useRef<{ caseId: string; imageId: string | null } | null>((() => {
    const params = new URL(window.location.href).searchParams;
    const caseId = params.get("case_id");
    return caseId ? { caseId, imageId: params.get("image_id") } : null;
  })());
  const activeTokenRef = useRef(token);
  activeTokenRef.current = token;
  const selected = cases.find((item) => item.id === selectedId);
  const selectedImage = selected?.images.find((item) => item.id === selectedImageId) || selected?.images.at(-1);
  const selectedAnalysis = runForImage(selectedImage?.id, analysis);
  const selectedImageRef = useRef(selectedImage?.id);
  selectedImageRef.current = selectedImage?.id;
  const overlayRequest = useRef(0);
  const matchingCases = cases.filter((item) =>
    (caseStatus === "all" || item.status === caseStatus) &&
    (caseModality === "all" || item.modality === caseModality) &&
    (caseTaskFilter === "all" || (item.intended_tasks || [item.intended_task]).includes(caseTaskFilter)) &&
    `${item.case_code} ${item.patient_code || ""} ${item.source_dataset || ""} ${item.anatomy}`.toLowerCase().includes(caseSearch.trim().toLowerCase())
  ).sort((left, right) => caseSort === "code" ? left.case_code.localeCompare(right.case_code)
    : caseSort === "oldest" ? left.created_at.localeCompare(right.created_at) : right.created_at.localeCompare(left.created_at));
  const pageCount = Math.max(1, Math.ceil(matchingCases.length / 8));
  const visibleCases = matchingCases.slice((Math.min(casePage, pageCount) - 1) * 8, Math.min(casePage, pageCount) * 8);

  useEffect(() => () => { if (overlay.startsWith("blob:")) URL.revokeObjectURL(overlay); }, [overlay]);

  useEffect(() => {
    request<typeof capabilities>("/api/auth/capabilities").then(setCapabilities).catch(() => {});
    if (localDemo) {
      request<{ accounts: SavedAccount[] }>("/api/auth/demo-accounts")
        .then((res) => {
          if (res.accounts && res.accounts.length > 0) {
            const merged = saveDemoAccounts(res.accounts);
            setDemoAccounts([...merged]);
            // Explicit local-demo navigation uses the existing demo roster/session flow.
            // No passwords or session tokens are placed in URLs.
            if (["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname)) {
              const demoUrl = new URL(window.location.href);
              const requestedRole = demoUrl.searchParams.get("demo_role");
              const choice = res.accounts.find((account) => account.role === requestedRole && account.email.endsWith(".demo@example.com"));
              if (choice) {
                demoUrl.searchParams.delete("demo_role");
                window.history.replaceState({}, "", demoUrl.pathname + demoUrl.search + demoUrl.hash);
                switchAccount(choice);
              }
            }
          }
        })
        .catch(() => {});
    }
    const url = new URL(window.location.href);
    const ticket = url.searchParams.get("auth_ticket");
    const oauthError = url.searchParams.get("auth_error");
    if (!ticket && !oauthError) return;
    url.searchParams.delete("auth_ticket");
    url.searchParams.delete("auth_error");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
    if (oauthError) {
      setError(oauthError === "existing_account" ? "This email already has an account. Sign in with your password first." : "Social sign-in could not be completed.");
    }
    if (ticket) {
      request<{ access_token: string }>("/api/auth/oauth/exchange", undefined, { ticket }, "POST")
        .then((result) => { localStorage.setItem(TOKEN_KEY, result.access_token); sessionStorage.removeItem(TOKEN_KEY); setToken(result.access_token); })
        .catch((cause: Error) => setError(cause.message));
    }
  }, []);

  async function loadCases(activeToken: string) {
    const requestId = ++caseFetchSeq.current;
    const next = await request<CaseRecord[]>("/api/cases", activeToken);
    if (requestId !== caseFetchSeq.current || activeToken !== activeTokenRef.current) return;
    setCases((current) => JSON.stringify(current) === JSON.stringify(next) ? current : next);
    setCaseListToken(activeToken);
    setSelectedId((current) => next.some((item) => item.id === current) ? current : next[0]?.id || "");
  }

  useEffect(() => {
    if (!token || !canReadCases(user?.role)) return;
    let inFlight = false;
    const refresh = () => {
      if (document.visibilityState !== "visible" || inFlight) return;
      inFlight = true;
      loadCases(token).catch(() => {}).finally(() => { inFlight = false; });
    };
    const timer = window.setInterval(refresh, 2500);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [token, user?.role]);

  useEffect(() => {
    if (!token) return;
    let active = true;
    request<User>("/api/auth/me", token)
      .then((profile) => {
        if (!active || token !== activeTokenRef.current) return;
        setUser(profile);
        if (localStorage.getItem(TOKEN_KEY) === token) setDemoAccounts(saveAccount(profile, token));
        setActiveView("overview");
        if (canReadCases(profile.role)) return loadCases(token);
        setCases([]);
        setSelectedId("");
      })
      .catch(() => {
        if (!active || token !== activeTokenRef.current) return;
        setDemoAccounts(forgetAccount(token));
        sessionStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(TOKEN_KEY);
        setToken("");
      });
    return () => { active = false; };
  }, [token]);

  useEffect(() => {
    const target = requestedCaseNavigation.current;
    if (!target || !user || caseListToken !== token || new URL(window.location.href).searchParams.has("demo_role")) return;
    // Resolve only against the server-authorized case list for this exact session.
    const allowedCase = cases.find((item) => item.id === target.caseId);
    requestedCaseNavigation.current = null;
    const cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete("case_id");
    cleanUrl.searchParams.delete("image_id");
    window.history.replaceState({}, "", cleanUrl.pathname + cleanUrl.search + cleanUrl.hash);
    if (!allowedCase || !canOpenSection("analysis", user.role, user.permissions)) {
      setError("The requested analysis case is unavailable for this account.");
      return;
    }
    const image = allowedCase.images.find((item) => item.id === target.imageId) || allowedCase.images.at(-1);
    setSelectedId(allowedCase.id);
    setSelectedImageId(image?.id || "");
    setActiveView("analysis");
  }, [cases, user, caseListToken, token, demoAccounts]);

  useEffect(() => {
    const item = selectedImage;
    if (!item || !token) {
      setPreview("");
      return;
    }
    setPreview("");
    let active = true;
    let objectUrl = "";
    fetch(apiUrl(item.preview_url), { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => {
        if (!response.ok) throw new Error("Could not load preview");
        return response.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        if (active) { setPreviewOwner(item.id); setPreview(objectUrl); }
      })
      .catch((cause: Error) => setError(cause.message));
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [selectedImage?.id, token]);

  useEffect(() => {
    if (!token || !selectedImage) {
      setAnalysis(null);
      setOverlay("");
      setHistory([]);
      return;
    }
    setAnalysis(null);
    setOverlay("");
    setHistory([]);
    let active = true;
    let objectUrl = "";
    request<{ models_ready: boolean }>("/api/analysis/status", token)
      .then((status) => { if (active) setModelsReady(status.models_ready); })
      .catch(() => { if (active) setModelsReady(false); });
    request<AnalysisResult[]>(`/api/images/${selectedImage.id}/analyses`, token)
      .then((items) => { if (active) setHistory(items); })
      .catch(() => { if (active) setHistory([]); });
    request<AnalysisResult>(`/api/images/${selectedImage.id}/analysis`, token)
      .then(async (result) => {
        if (!active) return;
        setAnalysis(result);
        const response = await fetch(apiUrl(result.overlay_url), { headers: { Authorization: `Bearer ${token}` } });
        if (!response.ok) { if (active) setOverlay(''); return; }
        objectUrl = URL.createObjectURL(await response.blob());
        if (active) setOverlay(objectUrl);
      })
      .catch(() => { if (active) { setAnalysis(null); setOverlay(""); } });
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [selectedImage?.id, selectedImage?.latest_analysis_id, token]);

  async function showAnalysis(result: AnalysisResult) {
    if (selectedImageRef.current !== result.image_id) return;
    const sequence = ++overlayRequest.current;
    setAnalysis(result);
    setOverlay(previous => { if (previous) URL.revokeObjectURL(previous); return ''; });
    setError("");
    try {
      const response = await fetch(apiUrl(result.overlay_url), { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error("Analysis overlay unavailable");
      const objectUrl = URL.createObjectURL(await response.blob());
      if (selectedImageRef.current !== result.image_id || sequence !== overlayRequest.current) { URL.revokeObjectURL(objectUrl); return; }
      setOverlay((previous) => { if (previous) URL.revokeObjectURL(previous); return objectUrl; });
    } catch (cause) { setError((cause as Error).message); }
  }

  async function handleAnalysis() {
    if (!selectedImage || analysisBusy) return;
    const submittedImageId = selectedImage.id;
    setError("");
    setAnalysisBusy(true);
    setAnalysisJob(null);
    try {
      const storageKey = `corovision-job-${selectedImage.id}`;
      const key = sessionStorage.getItem(storageKey) || crypto.randomUUID();
      sessionStorage.setItem(storageKey, key);
      const job = await request<AnalysisJob>(`/api/images/${selectedImage.id}/analysis/jobs`, token, { idempotency_key: key }, "POST");
      sessionStorage.removeItem(storageKey);
      if (selectedImageRef.current === submittedImageId) setAnalysisJob(job);
    } catch (cause) {
      setError((cause as Error).message);
      setAnalysisBusy(false);
    }
  }

  useEffect(() => {
    let active = true;
    setAnalysisJob(null);
    setAnalysisBusy(false);
    if (selectedImage && token) request<AnalysisJob[]>(`/api/images/${selectedImage.id}/analysis/jobs`, token)
      .then((jobs) => { if (active) setAnalysisJob(jobs.find((job) => ["pending", "processing"].includes(job.status)) || jobs[0] || null); })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [selectedImage?.id, token]);

  useEffect(() => {
    if (!analysisJob || analysisJob.image_id !== selectedImage?.id || !token) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const jobId = analysisJob.id;
    setAnalysisBusy(true);
    async function poll() {
      try {
        const job = await request<AnalysisJob>(`/api/analysis/jobs/${jobId}`, token);
        if (!active) return;
        setAnalysisJob(job);
        if (job.status === "failed") {
          setError(job.error_detail || "Analysis job failed; review before requesting a new run.");
          setAnalysisBusy(false);
        } else if (job.status === "completed" && job.result_url) {
          const result = await request<AnalysisResult>(job.result_url, token);
          if (!active) return;
          await showAnalysis(result);
          const items = await request<AnalysisResult[]>(`/api/images/${job.image_id}/analyses`, token);
          if (!active) return;
          setHistory(items);
          await loadCases(token);
          if (!active) return;
          setNotice("Research analysis saved. Review masks, candidate evidence and limitations.");
          setAnalysisBusy(false);
        } else timer = setTimeout(poll, 1000);
      } catch (cause) {
        if (active) { setError((cause as Error).message); setAnalysisBusy(false); }
      }
    }
    void poll();
    return () => { active = false; clearTimeout(timer); };
  }, [analysisJob?.id, selectedImage?.id, token]);

  async function handleAuth(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (registering) {
        await request("/api/auth/register", undefined, { email, password, display_name: displayName, username: username || undefined }, "POST");
      }
      const result = await request<{ access_token: string }>(
        "/api/auth/login", undefined, { identifier: email, password, remember: rememberMe }, "POST",
      );
      if (rememberMe) {
        localStorage.setItem(TOKEN_KEY, result.access_token);
        sessionStorage.removeItem(TOKEN_KEY);
      } else {
        sessionStorage.setItem(TOKEN_KEY, result.access_token);
        localStorage.removeItem(TOKEN_KEY);
      }
      setToken(result.access_token);
      setPassword("");
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleReset(event: FormEvent) {
    event.preventDefault();
    setError("");
    setAuthNotice("");
    setBusy(true);
    try {
      if (resetStep === "request") {
        await request("/api/auth/password-reset/request", undefined, { contact: resetContact }, "POST");
        setResetStep("confirm");
        setAuthNotice("If this verified contact belongs to an account, a six-digit code has been sent.");
      } else {
        await request("/api/auth/password-reset/confirm", undefined,
          { contact: resetContact, code: resetCode, new_password: resetPassword }, "POST");
        setResetting(false);
        setResetStep("request");
        setResetCode("");
        setResetPassword("");
        setAuthNotice("Password reset. Sign in with your new password.");
      }
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleNewCase(event: FormEvent) {
    event.preventDefault();
    if (!newTasks.length) { setError("Select at least one intended task."); return; }
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const created = await request<CaseRecord>(
        "/api/cases", token, { case_code: caseCode.trim(), modality: newModality, anatomy: newAnatomy,
          intended_task: newTasks[0], intended_tasks: newTasks, source_dataset: newSource.trim() || null }, "POST",
      );
      await loadCases(token);
      setSelectedId(created.id);
      setCaseCode("");
      setNewCaseOpen(false);
      setCaseSection("assets");
      setNotice("Research case created. Select Assets & preparation to add supported inputs.");
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!selectedId || uploadInFlight.current) return;
    if (!files.length && !selectedImage?.source_url) return;
    uploadInFlight.current = true;
    setError("");
    setNotice("");
    setBusy(true);
    setUploadProgress({ done: 0, total: files.length, name: files[0]?.name || "" });
    try {
      let uploadFiles = files;
      const reprocessing = !uploadFiles.length;
      if (reprocessing && selectedImage?.source_url) {
        const original = await fetch(apiUrl(selectedImage.source_url), { headers: { Authorization: `Bearer ${token}` } });
        if (!original.ok) throw new Error("Could not load the preserved original for reprocessing.");
        uploadFiles = [new File([await original.blob()], selectedImage.original_name)];
      }
      let lastUploadedId = "";
      const failures: string[] = [];
      const duplicates: string[] = [];
      const remaining: File[] = [];
      for (const [index, file] of uploadFiles.entries()) {
        setUploadProgress({ done: index, total: uploadFiles.length, name: file.name });
        const body = new FormData();
        body.append("file", file);
        const selectedRoi = roi.trim() || (reprocessing ? selectedImage?.roi_box || "" : "");
        const selectedFrame = frameIndex || (reprocessing && selectedImage?.frame_index != null ? String(selectedImage.frame_index) : "");
        const selectedPage = pageIndex || (reprocessing && selectedImage?.page_index != null ? String(selectedImage.page_index) : "");
        if (selectedRoi) body.append("roi", selectedRoi);
        if (selectedFrame !== "" && /\.(dcm|dicom)$/i.test(file.name)) body.append("frame_index", selectedFrame);
        if (selectedPage !== "" && /\.pdf$/i.test(file.name)) body.append("page_index", selectedPage);
        body.append("profile", preprocessingProfile);
        body.append("standard_pipeline", preprocessingProfile === "standard" ? standardPipeline : "baseline");
        body.append("denoise", String(preprocessingProfile === "research" && denoise));
        body.append("enhance", String(preprocessingProfile === "research" && enhance));
        try {
          const response = await fetch(apiUrl(`/api/cases/${selectedId}/images`), {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body,
          });
          if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            if (response.status === 409 && String(result.detail || "").toLowerCase().includes("already attached")) {
              duplicates.push(file.name);
              continue;
            }
            throw new Error(result.detail || "Upload failed");
          }
          const uploaded = await response.json() as { id: string };
          lastUploadedId = uploaded.id;
        } catch (cause) {
          failures.push(`${file.name}: ${(cause as Error).message}`);
          remaining.push(file);
        }
        setUploadProgress({ done: index + 1, total: uploadFiles.length, name: file.name });
      }
      await loadCases(token);
      if (lastUploadedId) setSelectedImageId(lastUploadedId);
      setFiles(remaining);
      if (!remaining.length) { setRoi(""); setFrameIndex(""); setPageIndex(""); }
      setAnalysis(null);
      setOverlay("");
      if (lastUploadedId) setNotice(`${uploadFiles.length - failures.length - duplicates.length} study image(s) validated and prepared.${duplicates.length ? ` Skipped exact duplicate: ${duplicates.join(", ")}.` : ""}`);
      else if (duplicates.length) setNotice(`No new images added. Skipped exact duplicate: ${duplicates.join(", ")}.`);
      if (failures.length) setError(failures.join(" "));
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusy(false);
      setUploadProgress(null);
      uploadInFlight.current = false;
    }
  }

  function clearSession() {
    setDemoAccounts(forgetAccount(token));
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setUser(null);
    setCases([]);
    setSelectedId("");
    setSelectedImageId("");
    setPreview("");
    setHistory([]);
  }

  async function signOut() {
    try {
      await request("/api/auth/logout", token, undefined, "POST");
    } catch {
      // Clear the browser session even if the server already expired it.
    } finally {
      clearSession();
    }
  }

  function switchAccount(account: SavedAccount) {
    if (!localDemo || account.token === token) return;
    localStorage.setItem(TOKEN_KEY, account.token);
    sessionStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setCases([]);
    setSelectedId("");
    setSelectedImageId("");
    setPreview("");
    setHistory([]);
    setAnalysis(null);
    setOverlay("");
    setActiveView("overview");
    setToken(account.token);
  }

  function startNewCase() {
    if (!canCreateCases(user?.role, user?.permissions)) return;
    setActiveView("cases");
    setNewCaseOpen(true);
    setCaseFinderOpen(false);
    window.setTimeout(() => document.getElementById("case-code")?.focus(), 250);
  }

  function startFindCase() {
    setActiveView("cases");
    setNewCaseOpen(false);
    setCaseFinderOpen(true);
    window.setTimeout(() => document.getElementById("case-search")?.focus(), 250);
  }

  if (!token) {
    const social = !resetting && !registering ? (
      <div className="wm-auth-social">
        <Button type="button" variant="outline" className="wm-social-button" disabled={!capabilities.google} onClick={() => window.location.assign(apiUrl("/api/auth/oauth/google/start"))}>
          <GoogleLogo /> Continue with Google
        </Button>
        <Button type="button" variant="outline" className="wm-social-button" disabled title="Institutional SSO is not configured">
          <Building2 className="social-icon" aria-hidden="true" /> Hospital / University SSO
        </Button>
        {!capabilities.google && <p className="wm-auth-help">Google sign-in is unavailable until OAuth credentials are configured.</p>}
      </div>
    ) : undefined;

    return (
      <>
      <div className="theme-switch-float"><SwitchMode width={76} height={38} /></div>
      <Auth7
        title={resetting ? "Reset your password" : registering ? "Create your account" : "Welcome back"}
        description={resetting ? "Get a one-time code by email." : registering ? "Join the CoroVision AI research workspace." : "Sign in to access coronary vessel analysis."}
        social={social}
        footer={
          <p className="wm-auth-switch">
            {resetting ? "Remember your password?" : registering ? "Already have an account?" : "Don't have an account?"}{" "}
            <button type="button" onClick={() => { if (resetting) setResetting(false); else setRegistering(!registering); setError(""); setAuthNotice(""); }}>
              {resetting || registering ? "Sign in" : "Sign up"}
            </button>
          </p>
        }
      >
        {resetting ? (
          <form className="wm-auth-form" onSubmit={handleReset}>
            <Label htmlFor="reset-contact">Email</Label>
            <Input id="reset-contact" type="email" autoComplete="email" placeholder="you@example.com" value={resetContact} onChange={(event) => setResetContact(event.target.value)} required />
            {resetStep === "confirm" && (
              <>
                <Label htmlFor="reset-code">Six-digit code</Label>
                <Input id="reset-code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} placeholder="Enter your code" value={resetCode} onChange={(event) => setResetCode(event.target.value)} required />
                <Label htmlFor="reset-password">New password</Label>
                <Input id="reset-password" type="password" autoComplete="new-password" minLength={12} placeholder="At least 12 characters" value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} required />
              </>
            )}
            {error && <p className="wm-auth-message wm-auth-error" role="alert">{error}</p>}
            {authNotice && <p className="wm-auth-message" role="status">{authNotice}</p>}
            {!capabilities.email_reset && <p className="wm-auth-help">Email delivery must be configured by the project administrator.</p>}
            <Button className="wm-auth-submit" disabled={busy || !capabilities.email_reset}>{busy ? "Please wait…" : resetStep === "request" ? "Send code" : "Reset password"}</Button>
          </form>
        ) : (
          <form className="wm-auth-form" onSubmit={handleAuth}>
            {registering && (
              <>
                <Label htmlFor="display-name">Display name</Label>
                <Input id="display-name" autoComplete="name" maxLength={100} placeholder="Enter your name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
                <Label htmlFor="username">Username</Label>
                <Input id="username" autoComplete="username" placeholder="Choose a username" value={username} onChange={(event) => setUsername(event.target.value)} required />
              </>
            )}
            <Label htmlFor="email">{registering ? "Email" : "Username or email"}</Label>
            <Input id="email" type={registering ? "email" : "text"} autoComplete="username" placeholder={registering ? "Enter your email" : "Enter username or email"} value={email} onChange={(event) => setEmail(event.target.value)} required />
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" autoComplete={registering ? "new-password" : "current-password"} placeholder="Enter your password" minLength={registering ? 12 : undefined} value={password} onChange={(event) => setPassword(event.target.value)} required />
            {registering ? <p className="wm-auth-help">Use at least 12 characters.</p> : (
              <div className="wm-auth-options">
                <label className="wm-remember-option" htmlFor="remember-me">
                  <input id="remember-me" type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} />
                  <span>Keep me signed in on this device</span>
                </label>
                <button type="button" className="wm-auth-link" onClick={() => { setError(""); setAuthNotice(""); setResetContact(email.includes("@") ? email : ""); setResetting(true); }}>Forgot password?</button>
              </div>
            )}
            {error && <p className="wm-auth-message wm-auth-error" role="alert">{error}</p>}
            {authNotice && <p className="wm-auth-message" role="status">{authNotice}</p>}
            <Button className="wm-auth-submit" disabled={busy}>{busy ? "Please wait…" : registering ? "Create account" : "Sign in"}</Button>
          </form>
        )}
      </Auth7>
      </>
    );
  }

  if (!user) return <div className="auth-loading" role="status">Loading your workspace…</div>;

  const caseActionsPage = <section className="cv-case-page" aria-label={newCaseOpen ? "Create case workspace" : "Find case workspace"}>
    <header className="cv-case-page-heading"><div><p className="eyebrow">CASE WORKSPACE</p><h1>{newCaseOpen ? "Create a research case" : "Find a case"}</h1><p>{newCaseOpen ? "Register a de-identified study, then add images and prepare them for analysis." : "Search and filter the cases you are authorized to access."}</p></div><Button type="button" variant="outline" onClick={() => { setNewCaseOpen(false); setCaseFinderOpen(false); }}>Back to case workspace</Button></header>
    <CreateNewDisclosure mode={newCaseOpen && canCreateCases(user.role, user.permissions) ? "create" : caseFinderOpen ? "find" : null}
                canCreate={canCreateCases(user.role, user.permissions)}
                onModeChange={mode => { setNewCaseOpen(mode === "create"); setCaseFinderOpen(mode === "find"); }}
                findContent={<>
              <div className="case-list-controls">
                <label className="sr-only" htmlFor="case-search">Search cases</label>
                <Input id="case-search" value={caseSearch} onChange={(event) => { setCaseSearch(event.target.value); setCasePage(1); }} placeholder="Search case or patient ID" />
                <div><label className="sr-only" htmlFor="case-filter">Filter by status</label><ScreenShareSelect id="case-filter" value={caseStatus} onChange={(event) => { setCaseStatus(event.target.value); setCasePage(1); }}><option value="all">All statuses</option>{[...new Set(cases.map((item) => item.status))].map((status) => <option value={status} key={status}>{status}</option>)}</ScreenShareSelect>
                <label className="sr-only" htmlFor="case-sort">Sort cases</label><ScreenShareSelect id="case-sort" value={caseSort} onChange={(event) => setCaseSort(event.target.value as typeof caseSort)}><option value="newest">Newest</option><option value="oldest">Oldest</option><option value="code">Case ID</option></ScreenShareSelect></div>
              </div>
              <div className="case-list-controls"><label>Modality<ScreenShareSelect label="Modality" value={caseModality} onChange={e => { setCaseModality(e.target.value); setCasePage(1); }}><option value="all">All modalities</option>{[...new Set(cases.map(c => c.modality))].map(v => <option key={v}>{v}</option>)}</ScreenShareSelect></label><label>Research task<ScreenShareSelect label="Research task" value={caseTaskFilter} onChange={e => { setCaseTaskFilter(e.target.value); setCasePage(1); }}><option value="all">All tasks</option>{caseTasks.map(([id, title]) => <option key={id} value={id}>{title}</option>)}</ScreenShareSelect></label></div>
<section className="case-find-results" aria-label="Case search results"><h2>Search results <span>({matchingCases.length})</span></h2>
{visibleCases.length ? visibleCases.map(item => <button type="button" key={item.id} onClick={() => { setSelectedId(item.id); setNewCaseOpen(false); setCaseFinderOpen(false); setError(""); }}><strong>{item.case_code}</strong><span>{item.modality} · {item.anatomy} · {item.status}</span><small>{(item.intended_tasks || [item.intended_task]).map(taskLabel).join(", ")}</small><span>Open case →</span></button>) : <p className="muted">{cases.length ? "No cases match your filters." : "No accessible cases yet. Create a new study or ask the case owner to share access."}</p>}
{matchingCases.length > 8 && <div className="case-pagination"><Button type="button" variant="outline" disabled={casePage <= 1} onClick={() => setCasePage(page => page - 1)}>Previous</Button><span>{Math.min(casePage, pageCount)} / {pageCount}</span><Button type="button" variant="outline" disabled={casePage >= pageCount} onClick={() => setCasePage(page => page + 1)}>Next</Button></div>}
</section>
              </>}
                createContent={<form onSubmit={handleNewCase} className="new-case">
                <label className="case-code-field" htmlFor="case-code">New case code<Input id="case-code" placeholder="e.g. CASE-001" maxLength={80} value={caseCode} onChange={(e) => setCaseCode(e.target.value)} required /></label>
                <label>Modality<ScreenShareSelect label="Modality" value={newModality} onChange={e => { const v = e.target.value; setNewModality(v); setNewTasks(v === "XCA" ? ["artery_and_stenosis"] : ["volume_preparation"]); if (v === "XCA") setNewAnatomy("coronary"); }}><option value="XCA">X-ray angiography</option><option value="CTA">CT angiography</option><option value="CT">CT</option><option value="MRA">MR angiography</option></ScreenShareSelect></label>
                <label>Anatomy<ScreenShareSelect label="Anatomy" value={newAnatomy} onChange={e => setNewAnatomy(e.target.value)}>{caseAnatomies.filter(v => newModality !== "XCA" || v === "coronary").map(v => <option key={v}>{v}</option>)}</ScreenShareSelect></label>
                <label>Intended tasks<ScreenShareSelect label="Intended tasks" value={newTasks[0] || ""} multiple values={newTasks} onValuesChange={setNewTasks} onChange={e => setNewTasks([e.target.value])}>{caseTasks.filter(([id]) => newModality === "XCA" ? id !== "volume_preparation" : id === "volume_preparation").map(([id, title]) => <option key={id} value={id}>{title}</option>)}</ScreenShareSelect></label>
                <label>Source dataset or release<Input value={newSource} maxLength={120} onChange={e => setNewSource(e.target.value)} placeholder="e.g. ARCADE official release" /></label>
                <Button className="primary" disabled={busy}>{busy ? "Creating…" : "Create research case"}</Button>
                {error && <Alert1 tone="error" title="Case could not be created">{error}</Alert1>}
              </form>} />
  </section>;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark" aria-hidden="true"><img src="/corovision-heart-mark.png" alt="" /></span><span>CoroVision AI <small>VASCULAR IMAGING RESEARCH</small></span></div>
        <div className="account"><NotificationBell key={user.id} token={token} onOpenCase={(id) => { setSelectedId(id); setSelectedImageId(""); setActiveView("cases"); }} /><div className="theme-switch"><SwitchMode width={76} height={38} /></div></div>
      </header>
      <main className="workspace">
        <MacOSSidebar activeView={activeView} onViewChange={setActiveView} user={user} role={user?.role} onNewCase={startNewCase} onLogout={signOut} savedAccounts={demoAccounts.filter((account) => account.id !== user.id)} onSwitchAccount={switchAccount}>
            <>
              <h1>Cases</h1>
              <p className="muted">Authorized de-identified research studies</p>
              <div className="sidebar-case-actions">
                {canCreateCases(user.role, user.permissions) && <Button type="button" variant={newCaseOpen ? "default" : "outline"} onClick={startNewCase}>Create case</Button>}
                <Button type="button" variant={caseFinderOpen ? "default" : "outline"} onClick={startFindCase}>Find case</Button>
              </div>
              <div className="case-list" role="list" aria-label="Cases">
                {matchingCases.length === 0 && <p className="empty">{cases.length ? "No cases match your filters." : "No accessible cases yet."}</p>}
                {visibleCases.map((item) => (
                  <button key={item.id} className={`case-item ${selectedId === item.id ? "active" : ""}`} onClick={() => { setSelectedId(item.id); setNewCaseOpen(false); setCaseFinderOpen(false); setError(""); }}>
                    <strong>{item.case_code}</strong>
                    <span>{item.modality} · {item.anatomy} · {item.status}</span><small>{(item.intended_tasks || [item.intended_task]).map(taskLabel).join(", ")}</small>
                  </button>
                ))}
              </div>
              {matchingCases.length > 8 && <div className="case-pagination"><button type="button" disabled={casePage <= 1} onClick={() => setCasePage((page) => page - 1)}>Previous</button><span>{Math.min(casePage, pageCount)} / {pageCount}</span><button type="button" disabled={casePage >= pageCount} onClick={() => setCasePage((page) => page + 1)}>Next</button></div>}
            </>
        </MacOSSidebar>
        <section className="content">
          {user.role === "viewer" && activeView !== "account" ? <ViewerWorkspace cases={cases} selected={selected} onSelect={setSelectedId} page={activeView === "overview" ? "overview" : "cases"} onCases={() => setActiveView("cases")} onSettings={() => setActiveView("account")} /> : <>
          {activeView === "overview" && (user.role === "admin" || user.role === "ml_engineer") && <RoleWorkspace role={user.role} onOpen={setActiveView} />}
          {activeView === "overview" && user.role !== "admin" && user.role !== "ml_engineer" && (
            <OverviewPanel
              token={token}
              user={user}
              cases={cases}
              onNewCase={startNewCase}
              onViewCases={startFindCase}
              onOpenCase={(id) => { setSelectedId(id); setActiveView("cases"); }}
              onOpenTask={(id, view) => { setSelectedId(id); setActiveView(view === "analysis" ? "analysis" : "cases"); }}
              onViewAnalysis={() => setActiveView("analysis")}
              onViewReports={() => setActiveView("reports")}
              onViewModels={() => setActiveView("models")}
              onOpenWorkspace={setActiveView}
            />
          )}
          {activeView === "models" && canViewModels(user.role) && <ModelWorkspace token={token} />}
          {(activeView === "analysis" || activeView === 'reviews' && reviewWorkspace) && canReadCases(user.role) && <>
            {error && <Alert1 tone="error" title="Action could not be completed" onDismiss={() => setError("")}>{error}</Alert1>}
            {notice && <Alert1 tone="success" title="Update completed" onDismiss={() => setNotice("")}>{notice}</Alert1>}
            {activeView === 'reviews' && <Button variant="outline" onClick={() => setReviewWorkspace(false)}>Back to review queue</Button>}
            <AnalysisWorkbench onImageReview={() => setActiveView('analysis')} reviewMode={activeView === 'reviews'}
              assessment={activeView === 'reviews' && selected ? <ReviewAssessment key={`${selected.id}:${analysis?.id}`} token={token} role={user.role} caseRecord={selected} analysis={analysis?.image_id === selectedImage?.id ? analysis : null} onSaved={updated => setCases(items => items.map(c => c.id === updated.id ? updated : c))} /> : undefined}
              onReview={selected?.permissions?.can_review ? () => { setReviewWorkspace(true); setActiveView('reviews'); } : undefined}
              token={token} cases={cases} selectedCase={selected} selectedImage={selectedImage} processedPreview={previewOwner === selectedImage?.id ? preview : ''}
              overlay={selectedAnalysis ? overlay : ''} analysis={selectedAnalysis}
              history={history.filter(r => r.image_id === selectedImage?.id)} modelsReady={modelsReady} analysisBusy={analysisBusy}
              jobStatus={analysisJob?.status} canRunAnalysis={selected?.permissions?.can_run_analysis ?? canCreateCases(user.role)}
              onCaseChange={(id) => { setSelectedId(id); setSelectedImageId(""); }} onImageChange={setSelectedImageId}
              onRun={handleAnalysis} onSelectAnalysis={showAnalysis} onUpload={() => setActiveView("cases")} onReports={() => setActiveView("reports")} />
          </>}
          {activeView === "reports" && canReadCases(user.role) && <ReportsPage token={token} role={user.role} cases={cases} selectedCase={selected} selectedImage={selectedImage} analysis={analysis?.image_id === selectedImage?.id ? analysis : null} history={history.filter(r => r.image_id === selectedImage?.id)} onSelectAnalysis={showAnalysis} onCaseChange={(id) => { setSelectedId(id); setSelectedImageId(""); }} onImageChange={setSelectedImageId} onAnalysis={() => setActiveView("analysis")} />}
          {activeView === "account" && <AccountPanel token={token} user={user} onUser={setUser} onLogout={clearSession} />}
          {(["admin", "permissions", "access", "audit"] as string[]).includes(activeView) && user?.role === "admin" && <AdminPanel key={activeView} section={activeView === "admin" ? "users" : activeView as "permissions" | "access" | "audit"} token={token} currentUser={user} />}
          {activeView === "reviews" && !reviewWorkspace && (user.role === "doctor" || user.role === "clinician" || user.role === "admin") && <ReviewQueue cases={cases} onOpen={id => { setSelectedId(id); setSelectedImageId(''); setReviewWorkspace(true); }} />}
          {activeView === "cases" && (newCaseOpen || caseFinderOpen) && canReadCases(user.role) && caseActionsPage}
          {(activeView === "cases" || activeView === "uploads") && !(activeView === "cases" && (newCaseOpen || caseFinderOpen)) && canReadCases(user.role) && (
          <>
          <div className="page-heading">
            <div><p className="eyebrow">{user.role === "doctor" || user.role === "clinician" ? "CLINICAL REVIEW" : user.role === "technician" ? "CASE INTAKE" : user.role === "viewer" ? "OBSERVATION" : "IMAGE PREPARATION"}</p><h2>{selected ? selected.case_code : "Select a case"}</h2></div>
            <span className="stage-badge">{user.role === "doctor" || user.role === "clinician" ? "Clinical workspace" : user.role === "viewer" ? "Read-only view" : "Research workspace"}</span>
          </div>
          {error && <Alert1 tone="error" title="Action could not be completed" onDismiss={() => setError("")}>{error}</Alert1>}
          {notice && <Alert1 tone="success" title="Update completed" onDismiss={() => setNotice("")}>{notice}</Alert1>}
          {selected && <><p className="muted">{selected.modality} · {selected.anatomy} · {(selected.intended_tasks || [selected.intended_task]).map(taskLabel).join(", ")} · {selected.source_dataset || "Source not recorded"}</p><nav className="case-section-nav" aria-label="Case sections">{[["overview", "Overview & access"], ["assets", "Assets & preparation"], ["reviews", "Reviews & notes"], ["history", "Analysis history"]].map(([id, title]) => <Button key={id} type="button" variant={caseSection === id ? "default" : "outline"} aria-pressed={caseSection === id} onClick={() => setCaseSection(id)}>{title}</Button>)}<Button type="button" variant="outline" onClick={() => setActiveView("analysis")}>Open analysis</Button><Button type="button" variant="outline" onClick={() => setActiveView("reports")}>Reports</Button></nav></>}
          {!selected ? (
            <div className="placeholder">{user.role === "viewer" ? "Select an assigned case from the sidebar to view." : "Create a de-identified case to upload an angiography image."}</div>
          ) : (
            <div className={`analysis-grid ${caseSection === 'assets' ? 'case-assets-layout' : ''}`}>
              {caseSection === "overview" && <CaseWorkflow caseRecord={selected} token={token} role={user.role}
                onUpdated={(updated) => setCases((items) => items.map((item) => item.id === updated.id ? updated : item))}
                onDeleted={(id) => { setCases((items) => items.filter((item) => item.id !== id)); setSelectedId(""); setSelectedImageId(""); setAnalysis(null); setOverlay(""); setActiveView("overview"); }}
                onNext={() => setCaseSection("assets")}>
                <CaseDetails key={`${selected.id}:overview`} section="overview" caseRecord={selected} token={token} modelVersion={analysis?.model_version} userRole={user.role} currentUserId={user.id}
                  onSaved={(updated) => setCases((items) => items.map((item) => item.id === updated.id ? updated : item))} />
              </CaseWorkflow>}
              {caseSection === "reviews" && <CaseDetails key={`${selected.id}:${caseSection}`} section={caseSection} caseRecord={selected} token={token} modelVersion={analysis?.model_version} userRole={user.role} currentUserId={user.id}
                onSaved={(updated) => setCases((items) => items.map((item) => item.id === updated.id ? updated : item))} />}
              {caseSection === "assets" && <>
              {selected.permissions?.can_upload ?? user.role !== "viewer" ? (
                <Card className={`panel ${selected.modality !== 'XCA' ? 'volume-assets-panel' : ''}`}>
                  <h3>{selected.modality === 'XCA' ? 'Upload image' : '3D volume workspace'}</h3>
                  <p className="muted">CoroVision AI · {selected.modality === "XCA" ? "Image intake and preprocessing" : "Separate research volume workflow"}</p>
                  <fieldset className="upload-mode-picker">
                    <legend>What are you uploading?</legend>
                    <button type="button" className={uploadMode === "inference" ? "active" : ""} onClick={() => setUploadMode("inference")}><strong>{selected.modality === "XCA" ? "Case image preparation" : "Research volume workflow"}</strong><small>{selected.modality === "XCA" ? "De-identified coronary angiography frames" : selected.anatomy === 'aorta' && ['CT', 'CTA'].includes(selected.modality) ? 'Pinned AortaSeg 3D research segmentation' : selected.modality === 'CTA' && selected.anatomy === 'coronary' ? 'Pinned ImageCAS and ImageCAS-X 3D research segmentation' : 'Preparation only; no compatible inference model'}</small></button>
                    {(user.role === "researcher" || user.role === "admin") && <button type="button" className={uploadMode === "dataset" ? "active" : ""} onClick={() => setUploadMode("dataset")}><strong>Research dataset</strong><small>Images paired with annotations for training and evaluation</small></button>}
                  </fieldset>
                  {selected.modality !== 'XCA' ? <VolumeIntake key={selected.id} caseId={selected.id} token={token} readOnly={user.role !== 'researcher' && user.role !== 'admin'} anatomy={selected.anatomy} inferenceEligible={(selected.anatomy==='coronary'&&(selected.modalities||[selected.modality]).includes('CTA'))||(selected.anatomy==='aorta'&&(selected.modalities||[selected.modality]).some(m=>m==='CT'||m==='CTA'))} /> : uploadMode === "dataset" ? <div className="dataset-intake-note">
                    <h4>ARCADE research dataset</h4>
                    <p>Preserve the official <strong>syntax</strong> and <strong>stenosis</strong> tasks and their train, validation, and test splits. Keep each task’s image files paired with its own COCO annotation JSON and class schema.</p>
                    <p>Dataset annotation conversion, split checks, duplicate auditing, and preprocessing use the ARCADE dataset pipeline. The case uploader below is for inference images and must not be used to turn annotation files into case images.</p>
                    <code>python3 -m ml.preprocessing.run_preprocessing --data-root arcade --output-root data/processed/arcade</code>
                    <Button type="button" variant="outline" onClick={() => setActiveView("models")}>Open model evaluation</Button>
                  </div> : <>
                  {selected.anatomy === 'coronary' && selected.modalities?.includes('CTA') && <details><summary>Separate coronary CTA volume workflow</summary><VolumeIntake caseId={selected.id} token={token} inferenceEligible readOnly={user.role !== 'researcher' && user.role !== 'admin'} /></details>}
                  <ol className="processing-stepper" aria-label="Image intake steps">
                    <li className={files.length ? "complete" : "active"}><span>1</span><div><strong>Select</strong><small>Images and options</small></div></li>
                    <li className={uploadProgress ? "active" : selected.images.length ? "complete" : ""}><span>2</span><div><strong>Validate</strong><small>Check and prepare</small></div></li>
                    <li className={selectedImage ? "complete" : ""}><span>3</span><div><strong>Quality check</strong><small>Review preview</small></div></li>
                  </ol>
                  <form onSubmit={handleUpload} className="image-intake-form">
                    <DocumentUploader files={files} onFilesChange={(next) => { setFiles(next); if (!next.some((item) => /\.(dcm|dicom)$/i.test(item.name))) setFrameIndex(""); if (!next.some((item) => /\.pdf$/i.test(item.name))) setPageIndex(""); }} />
                    <section className="intake-pipeline" aria-labelledby="intake-pipeline-title">
                      <h4 id="intake-pipeline-title">Image preprocessing pipeline</h4>
                      <p aria-live="polite">{standardPipelines.find(pipeline => pipeline.id === (preprocessingProfile === "standard" ? standardPipeline : denoise ? enhance ? "balanced" : "denoise" : enhance ? "contrast" : "baseline"))?.path}</p>
                      <small>The original is retained. Each preset applies only its listed operations. Uploading does not start model training.</small>
                    </section>
                    <fieldset className="preprocessing-profile">
                      <legend>Preprocessing profile</legend>
                      <p className="caption">Choose any combination of enhancements. Standard preparation is always included.</p>
                      <label><input type="checkbox" checked={preprocessingProfile === "standard" && standardPipeline === "baseline"} onChange={() => { setPreprocessingProfile("standard"); setStandardPipeline("baseline"); setDenoise(false); setEnhance(false); }} /><span><strong>Standard only</strong><small>Validation, grayscale / intensity normalization, optional ROI, aspect-preserving resize and padding, then quality check. Selecting this clears optional enhancements.</small></span></label>
                      {standardPipelines.filter(pipeline => pipeline.id === "denoise" || pipeline.id === "contrast").map(pipeline => <label key={pipeline.id}><input type="checkbox" checked={pipeline.id === "denoise" ? (preprocessingProfile === "research" ? denoise : standardPipeline === "denoise" || standardPipeline === "balanced") : (preprocessingProfile === "research" ? enhance : standardPipeline === "contrast" || standardPipeline === "balanced")} onChange={event => {
                        const noise = pipeline.id === "denoise" ? event.target.checked : (preprocessingProfile === "research" ? denoise : standardPipeline === "denoise" || standardPipeline === "balanced");
                        const contrast = pipeline.id === "contrast" ? event.target.checked : (preprocessingProfile === "research" ? enhance : standardPipeline === "contrast" || standardPipeline === "balanced");
                        if (preprocessingProfile === "research") { setDenoise(noise); setEnhance(contrast); }
                        else setStandardPipeline(noise ? contrast ? "balanced" : "denoise" : contrast ? "contrast" : "baseline");
                      }} /><span><strong>{pipeline.title}</strong><small>{pipeline.description}</small></span></label>)}
                      {(user.role === "researcher" || user.role === "admin") && <label><input type="checkbox" checked={preprocessingProfile === "research"} onChange={event => {
                        if (event.target.checked) { setDenoise(standardPipeline === "denoise" || standardPipeline === "balanced"); setEnhance(standardPipeline === "contrast" || standardPipeline === "balanced"); setPreprocessingProfile("research"); }
                        else { setStandardPipeline(denoise ? enhance ? "balanced" : "denoise" : enhance ? "contrast" : "baseline"); setDenoise(false); setEnhance(false); setPreprocessingProfile("standard"); }
                      }} /><span><strong>Research mode</strong><small>Record the selected preparation as a controlled research comparison. This does not add another filtering pass.</small></span></label>}
                    </fieldset>
                    <p className="caption">Each profile preserves the original and records the operations applied. Enhanced profiles may change thin vessels and are not validated accuracy improvements. Compare with Standard.</p>
                    <details className="upload-options"><summary>Frame, page and ROI options</summary>
                      <label htmlFor="upload-roi">Region of interest (x,y,width,height in source pixels)</label>
                      <Input id="upload-roi" placeholder="Optional, e.g. 40,50,300,300" value={roi} onChange={(e) => setRoi(e.target.value)} />
                      {files.some((item) => /\.(dcm|dicom)$/i.test(item.name)) && <><label htmlFor="frame-index">DICOM frame index (applies to DICOM files)</label><Input id="frame-index" type="number" min="0" step="1" placeholder="Required for multi-frame studies" value={frameIndex} onChange={(e) => setFrameIndex(e.target.value)} /></>}
                      {files.some((item) => /\.pdf$/i.test(item.name)) && <><label htmlFor="page-index">PDF page index (zero-based; applies to PDF files)</label><Input id="page-index" type="number" min="0" max="999" step="1" placeholder="Defaults to first page" value={pageIndex} onChange={(e) => setPageIndex(e.target.value)} /></>}
                    </details>
                    <Button type="submit" className="primary" disabled={busy || (!files.length && !selectedImage?.source_url)}>{busy ? "Processing…" : files.length ? `Validate and upload ${files.length} file${files.length === 1 ? "" : "s"}` : "Validate & reprocess saved original"}</Button>
                    {uploadProgress && <div className="upload-progress" role="status"><progress value={uploadProgress.done} max={uploadProgress.total} /> <span>{uploadProgress.done} of {uploadProgress.total} · {uploadProgress.name}</span></div>}
                  </form>
                  <p className="upload-privacy-note">Use public or de-identified images. Supported raster formats, DICOM, and scanned PDF pages are processed. Office documents, masks, and unsupported formats are not valid inference images.</p>
                  </>}
                  <div className="metadata">
                    <div><span>Modality</span><strong>{selected.modality}</strong></div>
                    <div><span>Status</span><strong>{selected.status}</strong></div>
                    <div><span>Images</span><strong>{selected.images.length}</strong></div>
                  </div>
                </Card>
              ) : (
                <Card className="panel">
                  <div className="viewer-heading"><h3>Study Intake</h3><span>Read-only</span></div>
                  <p className="muted">This assignment does not allow image uploads. Upload requires case ownership or edit access and a role with upload permission.</p>
                  {((selected.anatomy==='coronary'&&(selected.modalities||[selected.modality]).includes('CTA'))||(selected.anatomy==='aorta'&&(selected.modalities||[selected.modality]).some(m=>m==='CT'||m==='CTA'))) && <VolumeInference caseId={selected.id} token={token} anatomy={selected.anatomy} readOnly />}
                  <div className="metadata">
                    <div><span>Modality</span><strong>{selected.modality}</strong></div>
                    <div><span>Status</span><strong>{selected.status}</strong></div>
                    <div><span>Images</span><strong>{selected.images.length}</strong></div>
                  </div>
                </Card>
              )}
              {selected.modality === 'XCA' && <Card className="panel viewer">
                <div className="viewer-heading"><h3>Step 3 of 3 · Quality check</h3><span>512 × 512</span></div>
                {selected.images.length > 1 && <label className="image-picker" htmlFor="case-image">Image<ScreenShareSelect id="case-image" value={selectedImage?.id || ""} onChange={(event) => setSelectedImageId(event.target.value)}>{selected.images.map((item) => <option key={item.id} value={item.id}>{item.original_name} · {item.id.slice(0, 8)}</option>)}</ScreenShareSelect></label>}
                {preview ? <img src={preview} alt={`Processed preview for case ${selected.case_code}`} /> : <div className="image-empty">No images uploaded for this case yet.</div>}
                {selectedImage && <><p className="caption">Source: {selectedImage.original_name} · Original dimensions: {selectedImage.width} × {selectedImage.height} · Source spacing: {selectedImage.spacing_mm || "unavailable"}{selectedImage.processed_spacing_mm ? ` · Processed content spacing: ${selectedImage.processed_spacing_mm} mm` : ""}</p>
                  <details className="preprocessing-steps"><summary>Preprocessing record · {selectedImage.processing_record?.pipeline_version || "legacy"}</summary><p>Profile: {selectedImage.processing_record?.profile || "standard"} · Pipeline: {selectedImage.processing_record?.standard_pipeline || "custom / legacy"} · Denoising: {selectedImage.processing_record?.options?.denoise ? "on" : "off"} · Contrast enhancement: {selectedImage.processing_record?.options?.contrast_enhancement ? "on" : "off"}</p><ol>{(selectedImage.preprocessing || []).map((step) => <li key={step}>{step.replaceAll("_", " ")}</li>)}</ol>{selectedImage.processing_record?.warnings?.map((warning) => <Alert1 tone="warning" announce={false} title="Preprocessing warning" key={warning}>{warning.replaceAll("_", " ")}</Alert1>)}<p>The trained model applies its documented 3×3 median and clipped autocontrast input transform at inference. Compare model overlays with the preserved original before interpreting results.</p>{selectedImage.roi_box && <p>ROI: {selectedImage.roi_box}</p>}{selectedImage.frame_index !== null && <p>DICOM frame index: {selectedImage.frame_index}</p>}{selectedImage.page_index != null && <p>PDF page: {selectedImage.page_index + 1}</p>}</details></>}
              </Card>}
              </>}
              {caseSection === 'history' && ((selected.anatomy==='coronary'&&(selected.modalities||[selected.modality]).includes('CTA'))||(selected.anatomy==='aorta'&&(selected.modalities||[selected.modality]).some(m=>m==='CT'||m==='CTA'))) && <VolumeInference caseId={selected.id} token={token} anatomy={selected.anatomy} readOnly />}
              {caseSection === 'assets' && selected.anatomy==='coronary' && (selected.modalities||[selected.modality]).includes('XCA') && <TaskInference key={selected.id+':tasks'} caseId={selected.id} token={token} images={selected.images} canRun={selected.permissions?.can_run_analysis??false}/>}
              {caseSection === "history" && !selectedImage && selected.modality === 'XCA' && <Card className="panel"><h3>No 2D analysis history yet</h3><p>Prepare a supported 2D image first. 3D results, when available, are listed separately.</p></Card>}
              {caseSection === "history" && selectedImage && <Card className="panel analysis-panel">
                <div className="viewer-heading"><h3>AI vessel analysis</h3><span>Research only</span></div>
                <p className="caption">Selected source: {selectedImage.original_name}. Choose a different image under Assets & preparation to inspect its history.</p>
                <p className="muted">Two trained neural models create artery and suspected stenosis masks. The colors show pixel predictions, not a diagnosis or severity grade.</p>
                {(selected.permissions?.can_run_analysis ?? user.role !== "viewer") && (
                  <Button className="primary" type="button" onClick={handleAnalysis} disabled={analysisBusy || !modelsReady || selected.modality !== "XCA"}>
                    {analysisBusy ? "Analyzing…" : analysis ? "Run again" : "Run analysis"}
                  </Button>
                )}
                {!modelsReady && <p className="caption">Models are unavailable. Train both ARCADE baselines to enable analysis.</p>}
                {selected.modality !== "XCA" && <p className="caption">The current trained models accept X-ray coronary angiography only.</p>}
                {overlay && <div className="analysis-overlay"><img src={overlay} alt="Research artery and stenosis mask overlay" /><p className="caption">Cyan: predicted artery · Coral: predicted stenosis</p></div>}
                {analysis && <div className="analysis-details">
                  <p><strong>Model:</strong> {analysis.model_version}</p>
                  <p><strong>Predicted mask pixels:</strong> artery {analysis.artery_pixels.toLocaleString()} · stenosis {analysis.stenosis_pixels.toLocaleString()}</p>
                  <p>{analysis.interpretation}</p>
                  <p className="caption">Validation Dice: artery {analysis.validation.syntax?.validation_dice ?? "unavailable"} · stenosis {analysis.validation.stenosis?.validation_dice ?? "unavailable"}. Baseline validation is limited and is not clinical accuracy.</p>
                </div>}
              </Card>}
              {caseSection === "history" && selectedImage && <AnalysisHistory imageId={selectedImage.id} token={token} history={history} onSelect={showAnalysis} />}
              {caseSection !== "overview" && <nav className="case-bottom-navigation case-step-navigation" aria-label="Case workflow navigation">
                <Button type="button" variant="outline" onClick={() => setCaseSection(caseSection === "assets" ? "overview" : caseSection === "reviews" ? "assets" : "reviews")}>← Previous</Button>
                {caseSection === "assets" && <Button type="button" className="primary" disabled={busy || !!uploadProgress} onClick={() => setCaseSection("reviews")}>Next: Reviews &amp; notes →</Button>}
                {caseSection === "reviews" && <Button type="button" className="primary" onClick={() => setCaseSection("history")}>Next: Analysis history →</Button>}
                {caseSection === "history" && canOpenSection("reports", user.role, user.permissions) && <Button type="button" className="primary" disabled={analysisBusy} onClick={() => setActiveView("reports")}>Next: Reports →</Button>}
              </nav>}
            </div>
          )}
          <p className="footer-note">Research prototype · AI masks require expert review and are not a clinical diagnosis.</p>
          </>
          )}
          </>}
        </section>
      </main>
    </div>
  );
}

export default App;
