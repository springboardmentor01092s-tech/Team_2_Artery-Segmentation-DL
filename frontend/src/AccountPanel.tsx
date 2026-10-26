import { FormEvent, useEffect, useState } from "react";
import { request } from "./api";
import { Button } from "./components/prismui/button";
import { Card } from "./components/prismui/card";
import { Input } from "./components/prismui/input";
import { Label } from "./components/prismui/label";
import { Building2 } from "lucide-react";
import AccessRequests from "./AccessRequests";
import { designOptions, saveUserDesign, useDesignVariant } from "./designPreview";

export type User = {
  id: string;
  email: string;
  role: string;
  permissions?: string[];
  status?: string;
  can_approve_reports?: boolean;
  display_name: string;
  username: string | null;
  created_at: string;
};
type Session = {
  id: string;
  created_at: string;
  expires_at: string;
  active: boolean;
  current: boolean;
};
type Audit = { id: string; action: string; case_id: string | null; created_at: string };

export default function AccountPanel({
  token, user, onUser, onLogout,
}: {
  token: string;
  user: User;
  onUser: (value: User) => void;
  onLogout: () => void;
}) {
  const isViewer = user.role === "viewer";
  const [name, setName] = useState(user.display_name);
  const currentDesign = useDesignVariant();
  const [appearanceNotice, setAppearanceNotice] = useState("");
  const [email, setEmail] = useState(user.email);
  const [emailPassword, setEmailPassword] = useState("");
  const [username, setUsername] = useState(user.username || "");
  const [identityPassword, setIdentityPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [showAllSessions, setShowAllSessions] = useState(false);
  const [showAllActivity, setShowAllActivity] = useState(false);
  const [linkedProviders, setLinkedProviders] = useState<string[]>([]);
  const [socialCapabilities, setSocialCapabilities] = useState({ google: false });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [nextSessions, nextAudit, social, capabilities] = await Promise.all([
      isViewer ? Promise.resolve([] as Session[]) : request<Session[]>("/api/auth/sessions", token),
      isViewer ? Promise.resolve([] as Audit[]) : request<Audit[]>("/api/auth/audit", token),
      request<{ providers: string[] }>("/api/auth/social-accounts", token),
      request<{ google: boolean }>("/api/auth/capabilities"),
    ]);
    setSessions(nextSessions);
    setAudit(nextAudit);
    setLinkedProviders(social.providers);
    setSocialCapabilities(capabilities);
  }

  useEffect(() => {
    const url = new URL(window.location.href);
    const linked = url.searchParams.get("oauth_linked");
    if (linked === "google") {
      setMessage("Google account connected.");
      url.searchParams.delete("oauth_linked");
      window.history.replaceState({}, "", url.pathname + url.search + url.hash);
    }
    refresh().catch((cause: Error) => setError(cause.message));
  }, [token, isViewer]);

  async function connectProvider(provider: "google") {
    setError("");
    setBusy(true);
    try {
      const result = await request<{ authorization_url: string }>(`/api/auth/oauth/${provider}/link/start`, token, {}, "POST");
      window.location.assign(result.authorization_url);
    } catch (cause) { setError((cause as Error).message); setBusy(false); }
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    try {
      const updated = await request<User>(
        "/api/auth/me", token,
        { display_name: name, email, current_password: emailPassword || undefined },
        "PATCH",
      );
      onUser(updated);
      setEmailPassword("");
      setMessage("Profile updated.");
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function changePassword(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await request(
        "/api/auth/change-password", token,
        { current_password: currentPassword, new_password: newPassword }, "POST",
      );
      onLogout();
    } catch (cause) {
      setError((cause as Error).message);
      setBusy(false);
    }
  }

  async function saveIdentifiers(event: FormEvent) {
    event.preventDefault();
    setError(""); setMessage(""); setBusy(true);
    try {
      const updated = await request<Pick<User, "username">>(
        "/api/auth/identifiers", token,
        { username, current_password: identityPassword }, "PATCH",
      );
      onUser({ ...user, ...updated });
      setIdentityPassword("");
      setMessage("Username updated.");
      await refresh();
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }

  async function signOutAll() {
    setBusy(true);
    try {
      await request("/api/auth/logout-all", token, undefined, "POST");
      onLogout();
    } catch (cause) {
      setError((cause as Error).message);
      setBusy(false);
    }
  }

  return (
    <div className="settings-page">
      <div className="page-heading"><div><p className="eyebrow">SETTINGS</p><h2>Appearance, profile and security</h2></div><span className="stage-badge">{user.role === "clinician" ? "Clinician" : user.role === "doctor" ? "Doctor" : user.role.replace("_", " ")}</span></div>
      {error && <p className="message error" role="alert">{error}</p>}
      {message && <p className="message success" role="status">{message}</p>}
      <div className="settings-grid">
        <Card className="panel">
          <h3>Profile</h3>
          <p className="muted">Update your display name and email address.</p>
          <form onSubmit={saveProfile}>
            <Label htmlFor="profile-name">Display name</Label>
            <Input id="profile-name" maxLength={100} value={name} onChange={(event) => setName(event.target.value)} />
            <Label htmlFor="profile-email">Email</Label>
            <Input id="profile-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            {email !== user.email && (
              <>
                <Label htmlFor="profile-password">Current password to change email</Label>
                <Input id="profile-password" type="password" autoComplete="current-password" value={emailPassword} onChange={(event) => setEmailPassword(event.target.value)} required />
              </>
            )}
            <Button className="primary" disabled={busy}>Save profile</Button>
          </form>
        </Card>
        <Card className="panel">
          <h3>Institutional and connected accounts</h3>
          <p className="muted">Use your hospital or university identity through institutional single sign-on (SSO), once configured by your organization.</p>
          <div className="connected-actions">
            <Button type="button" variant="outline" disabled aria-describedby="settings-sso-help"><Building2 size={18} aria-hidden="true" /> Hospital / University SSO</Button>
            {(["google"] as const).map((provider) => (
              <Button key={provider} type="button" variant="outline" disabled={busy || !socialCapabilities[provider] || linkedProviders.includes(provider)} onClick={() => connectProvider(provider)}>
                {linkedProviders.includes(provider) ? "Google connected" : "Connect Google"}
              </Button>
            ))}
          </div>
          <p className="muted" id="settings-sso-help">Not yet configured. Your IT administrator must provide an identity-provider connection before institutional SSO can be enabled. Signing in does not automatically grant clinical privileges.</p>
          {!socialCapabilities.google && <p className="muted">Google sign-in also requires administrator configuration.</p>}
        </Card>
        <Card className="panel">
          <h3>Username</h3>
          <p className="muted">Use a unique username or your email address to sign in.</p>
          <form onSubmit={saveIdentifiers}>
            <Label htmlFor="profile-username">Username</Label>
            <Input id="profile-username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="e.g. researcher01" />
            <Label htmlFor="identity-password">Current password</Label>
            <Input id="identity-password" type="password" autoComplete="current-password" value={identityPassword} onChange={(event) => setIdentityPassword(event.target.value)} required />
            <Button className="primary" disabled={busy}>Save username</Button>
          </form>
        </Card>
        <Card className="panel">
          <h3>{isViewer ? "Account security" : "Change password"}</h3>
          <p className="muted">Changing your password signs out every active session.</p>
          <form onSubmit={changePassword}>
            <Label htmlFor="current-password">Current password</Label>
            <Input id="current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required />
            <Label htmlFor="new-password">New password</Label>
            <Input id="new-password" type="password" autoComplete="new-password" minLength={12} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required />
            <Button className="primary" disabled={busy}>Change password</Button>
          </form>
          {isViewer && <div className="settings-actions">
            <Button type="button" variant="outline" onClick={signOutAll} disabled={busy}>Sign out all devices</Button>
          </div>}
        </Card>
        {!isViewer && <Card className="panel">
          <h3>Sessions</h3>
          <p className="muted">JWT access lasts up to eight hours and can be revoked.</p>
          <p className="muted">Showing {showAllSessions ? sessions.length : Math.min(10, sessions.length)} of {sessions.length} sessions.</p>
          <div className="simple-list" id="account-sessions">
            {sessions.length === 0 && <p className="muted">No sessions found.</p>}
            {(showAllSessions ? sessions : sessions.slice(0, 10)).map((item) => (
              <div key={item.id} className="list-row"><span>{new Date(item.created_at).toLocaleString()} {item.current ? "· current" : ""}</span><strong>{item.active ? "Active" : "Revoked"}</strong></div>
            ))}
          </div>
          <div className="settings-actions">
          {sessions.length > 10 && <Button type="button" variant="outline" aria-expanded={showAllSessions} aria-controls="account-sessions" onClick={() => setShowAllSessions(value => !value)}>{showAllSessions ? "Show less" : `Show all sessions (${sessions.length})`}</Button>}
          <Button variant="outline" className="secondary" onClick={signOutAll} disabled={busy}>Sign out all sessions</Button>
          </div>
        </Card>}
        {!isViewer && <Card className="panel">
          <h3>Recent activity</h3>
          <p className="muted">Showing {showAllActivity ? audit.length : Math.min(10, audit.length)} of {audit.length} loaded activity entries.</p>
          <div className="simple-list" id="account-activity">
            {audit.length === 0 && <p className="muted">No activity yet.</p>}
            {(showAllActivity ? audit : audit.slice(0, 10)).map((item) => (
              <div key={item.id} className="list-row"><span>{item.action.replaceAll("_", " ")}</span><time>{new Date(item.created_at).toLocaleString()}</time></div>
            ))}
          </div>
          {audit.length > 10 && <Button type="button" variant="outline" aria-expanded={showAllActivity} aria-controls="account-activity" onClick={() => setShowAllActivity(value => !value)}>{showAllActivity ? "Show less" : `Show all activity (${audit.length})`}</Button>}
        </Card>}
        <AccessRequests key={user.id} token={token} />
        <Card className="panel appearance-settings">
          <h3>Appearance</h3>
          <p className="muted" id="appearance-help">Choose a design. Changes apply immediately and are saved for your account on this browser, not synced to other devices. Light and dark mode remain available in the top bar.</p>
          <fieldset aria-describedby="appearance-help">
            <legend>Application design</legend>
            <div className="appearance-options">
              {designOptions.map(option => <label key={option.id}>
                <input type="radio" name="application-design" value={option.id} checked={currentDesign === option.id} onChange={() => {
                  try {
                    saveUserDesign(user.id, option.id);
                    setAppearanceNotice(`${option.label} saved on this browser.`);
                  } catch { setAppearanceNotice("Could not save your design. Allow browser storage and try again."); }
                }} />
                <span>{option.label}</span>
              </label>)}
            </div>
          </fieldset>
          <p role="status" aria-live="polite">{appearanceNotice}</p>
        </Card>
      </div>
    </div>
  );
}
