import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  LayoutDashboard,
  FolderOpen,
  ShieldUser,
  Settings,
  BrainCircuit,
  ScanEye,
  FileBarChart2,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  LogOut,
  ChevronRight,
  User,
  ShieldCheck,
  Stethoscope,
  Microscope,
  ClipboardList,
  Eye,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { canCreateCases, canOpenSection, canViewModels } from "../../permissions";
import { demoAccountChoices, type SavedAccount } from "../../demoSessions";

export type SidebarView = "overview" | "cases" | "uploads" | "reviews" | "analysis" | "models" | "reports" | "account" | "admin" | "permissions" | "access" | "audit";

export interface SidebarUser {
  id?: string;
  email?: string;
  role?: string;
  permissions?: string[];
  display_name?: string;
  username?: string | null;
}

interface MacOSSidebarProps {
  activeView: SidebarView;
  onViewChange: (view: SidebarView) => void;
  user?: SidebarUser | null;
  role?: string;
  onNewCase: () => void;
  onLogout?: () => void;
  savedAccounts?: SavedAccount[];
  onSwitchAccount?: (account: SavedAccount) => void;
  children?: ReactNode;
}

const views = [
  { id: "overview", label: "Dashboard", icon: LayoutDashboard },
  { id: "cases", label: "Cases", icon: FolderOpen },
  { id: "uploads", label: "Data & Uploads", icon: Plus },
  { id: "reviews", label: "Severity Review", icon: ClipboardList },
  { id: "analysis", label: "AI Analysis", icon: ScanEye },
  { id: "models", label: "Model Evaluation", icon: BrainCircuit },
  { id: "reports", label: "Reports", icon: FileBarChart2 },
  { id: "admin", label: "User Management", icon: ShieldUser },
  { id: "permissions", label: "Roles & Permissions", icon: ShieldCheck },
  { id: "access", label: "Workspace & Case Access", icon: FolderOpen },
  { id: "audit", label: "Audit Logs", icon: ClipboardList },
  { id: "account", label: "Profile & Settings", icon: User },
] as const;

function viewLabel(view: (typeof views)[number], role?: string): string {
  if (view.id === "overview") return role === "admin" ? "Administration Overview" : role === "ml_engineer" ? "ML Overview" : role === "researcher" ? "Research Overview" : role === "doctor" || role === "clinician" ? "Clinical Overview" : "Dashboard";
  if (view.id === "cases") {
    if (role === "doctor" || role === "clinician") return "Research Cases";
    if (role === "technician") return "Case Intake";
    if (role === "viewer") return "Assigned Cases";
    if (role === "admin") return "Case Inventory";
    return "Research Cases";
  }
  if (view.id === "analysis" && role === "viewer") return "AI Results";
  if (view.id === "analysis" && role === "technician") return "Image Inspection";
  if (view.id === "models" && role === "admin") return "Model Registry";
  if (view.id === "models" && role === "ml_engineer") return "Registry & Evaluation Lab";
  if (view.id === "reports" && role === "researcher") return "Reports & Exports";
  if (view.id === "reports" && (role === "doctor" || role === "clinician")) return "Review Reports";
  if (view.id === "analysis" && (role === "doctor" || role === "clinician")) return "Image Review";
  if (view.id === "analysis" && role === "researcher") return "Analysis & Explainability";
  return view.label;
}

const AVATAR_COLORS = [
  "#c0392b", // brick red
  "#d35400", // pumpkin orange
  "#b45309", // amber
  "#047857", // emerald
  "#0e7490", // cyan
  "#1d4ed8", // blue
  "#4338ca", // indigo
  "#6d28d9", // violet
  "#be185d", // rose pink
];

function getAvatarColor(str?: string): string {
  if (!str) return AVATAR_COLORS[0];
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
}

function getInitials(nameOrEmail?: string): string {
  if (!nameOrEmail) return "U";
  const clean = nameOrEmail.trim();
  const parts = clean.split(/[\s._-]+/);
  if (parts.length >= 2 && parts[0] && parts[1]) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase();
}

function formatRole(role?: string): string {
  switch (role) {
    case "doctor":
    case "clinician":
      return "Doctor";
    case "researcher":
      return "Medical Researcher";
    case "ml_engineer":
      return "ML Engineer";
    case "technician":
      return "Technician / Data Operator";
    case "viewer":
      return "Standard User / Viewer";
    case "admin":
      return "System Administrator";
    default:
      return role || "Researcher";
  }
}

function RoleIcon({ role }: { role?: string }) {
  const Icon = role === "admin" ? ShieldCheck
    : role === "doctor" || role === "clinician" ? Stethoscope
    : role === "researcher" ? Microscope
    : role === "ml_engineer" ? BrainCircuit
    : role === "technician" ? ClipboardList
    : role === "viewer" ? Eye : User;
  return <Icon size={19} strokeWidth={2.2} aria-hidden="true" />;
}

/** Watermelon macOS sidebar with bottom-left profile card and popup menu. */
export function MacOSSidebar({
  activeView,
  onViewChange,
  user,
  role,
  onNewCase,
  onLogout,
  savedAccounts = [],
  onSwitchAccount,
  children,
}: MacOSSidebarProps) {
  const [open, setOpen] = useState(true);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const footerRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();

  const userRole = role || user?.role;
  const visibleViews = views.filter(({ id }) => canOpenSection(id, userRole, user?.permissions));

  const displayName = (userRole === "doctor" || userRole === "clinician") && /^Demo /i.test(user?.display_name || "") ? "Demo Doctor" : user?.display_name || user?.username || user?.email || "User";
  const roleLabel = formatRole(userRole);
  const initials = getInitials(user?.display_name || user?.username || user?.email);
  const avatarColor = getAvatarColor(user?.email || user?.display_name || "user");

  useEffect(() => {
    if (activeView === "cases" || activeView === "uploads") setOpen(true);
  }, [activeView]);

  // Click outside to close popover
  useEffect(() => {
    if (!popoverOpen) return;

    function handleClickOutside(event: MouseEvent | TouchEvent) {
      if (footerRef.current && !footerRef.current.contains(event.target as Node)) {
        setPopoverOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setPopoverOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [popoverOpen]);

  return (
    <motion.aside
      className={`macos-sidebar ${open ? "is-open" : "is-collapsed"}`}
      animate={{ width: open ? 280 : 76 }}
      transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 320, damping: 35, bounce: 0 }}
      aria-label="Workspace sidebar"
    >
      <div className={`macos-sidebar-panel ${open ? "is-open" : "is-collapsed"}`}>
        <div className="macos-sidebar-top-section">
          <div className="macos-sidebar-toolbar">
            <span
              className="macos-toolbar-title"
              style={{
                opacity: open ? 1 : 0,
                maxWidth: open ? 120 : 0,
                overflow: "hidden",
                whiteSpace: "nowrap",
                display: "inline-block",
                transition: "opacity 0.18s ease, max-width 0.22s ease",
              }}
            >
              WORKSPACE
            </span>
            <div className="macos-toolbar-actions">
              {open && canCreateCases(userRole, user?.permissions) && (
                <button type="button" title="New case" aria-label="New case" onClick={onNewCase}>
                  <Plus size={19} aria-hidden="true" />
                </button>
              )}
              <button
                type="button"
                title={open ? "Collapse sidebar" : "Expand sidebar"}
                aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
                aria-expanded={open}
                onClick={() => setOpen((value) => !value)}
              >
                {open ? <PanelLeftClose size={20} aria-hidden="true" /> : <PanelLeftOpen size={20} aria-hidden="true" />}
              </button>
            </div>
          </div>
          <nav className="macos-sidebar-nav" aria-label="Main navigation">
            {visibleViews.map((view) => {
              const { id } = view;
              const Icon = id === "overview" ? (userRole === "researcher" ? Microscope : userRole === "doctor" || userRole === "clinician" ? Stethoscope : userRole === "admin" ? ShieldCheck : userRole === "ml_engineer" ? BrainCircuit : LayoutDashboard) : id === "admin" ? ShieldUser : view.icon;
              const label = viewLabel(view, userRole);
              return (
              <button
                key={id}
                type="button"
                className={`macos-nav-btn ${activeView === id ? "active" : ""}`}
                aria-label={label}
                aria-current={activeView === id ? "page" : undefined}
                title={!open ? label : undefined}
                onClick={() => onViewChange(id)}
              >
                {activeView === id && (
                  <motion.span
                    layoutId="macos-active-view"
                    className="macos-active-bg"
                    transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 350, damping: 32 }}
                  />
                )}
                <Icon size={19} aria-hidden="true" className="macos-nav-icon" />
                <span
                  className="macos-nav-label"
                  style={{
                    opacity: open ? 1 : 0,
                    maxWidth: open ? 180 : 0,
                    overflow: "hidden",
                    whiteSpace: "nowrap",
                    display: "inline-block",
                    pointerEvents: open ? "auto" : "none",
                    transition: "opacity 0.18s ease, max-width 0.22s ease",
                  }}
                >
                  {label}
                </span>
              </button>
              );
            })}
          </nav>
          <AnimatePresence initial={false}>
            {open && (activeView === "cases" || activeView === "uploads") && userRole !== "viewer" && children && (
              <motion.div
                className="macos-sidebar-cases"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.18, ease: "easeInOut" }}
              >
                {children}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom-left Profile & Settings Popover trigger */}
        <div className="macos-sidebar-footer" ref={footerRef}>
          {popoverOpen && (
            <div
              className={`macos-profile-popover ${open ? "popover-expanded" : "popover-collapsed"}`}
              role="menu"
              aria-label="Account menu"
            >
              <div className="macos-popover-header">
                <div className="macos-avatar" style={{ backgroundColor: avatarColor }} aria-hidden="true">
                  {initials}
                </div>
                <div className="macos-popover-user">
                  <strong className="macos-popover-name" title={displayName}>
                    {displayName}
                  </strong>
                  <span className="macos-popover-role">{roleLabel}</span>
                </div>
                <ChevronRight size={16} className="macos-popover-header-arrow" aria-hidden="true" />
              </div>

              <div className="macos-popover-divider" role="separator" />

              <button
                type="button"
                className={`macos-popover-item ${activeView === "account" ? "active" : ""}`}
                role="menuitem"
                onClick={() => {
                  onViewChange("account");
                  setPopoverOpen(false);
                }}
              >
                <ShieldUser size={18} aria-hidden="true" />
                <span>Settings</span>
              </button>

              {userRole === "admin" && (
                <button
                  type="button"
                  className={`macos-popover-item ${activeView === "admin" ? "active" : ""}`}
                  role="menuitem"
                  onClick={() => {
                    onViewChange("admin");
                    setPopoverOpen(false);
                  }}
                >
                  <Settings size={18} aria-hidden="true" />
                  <span>Administration</span>
                </button>
              )}

              {canViewModels(userRole) && (
                <button
                  type="button"
                  className={`macos-popover-item ${activeView === "models" ? "active" : ""}`}
                  role="menuitem"
                  onClick={() => {
                    onViewChange("models");
                    setPopoverOpen(false);
                  }}
                >
                  <BrainCircuit size={18} aria-hidden="true" />
                  <span>Model evaluation</span>
                </button>
              )}

              {savedAccounts.length > 0 && <>
                <div className="macos-popover-divider" role="separator" />
                <span className="macos-switch-label">SWITCH ACCOUNT</span>
                {demoAccountChoices(savedAccounts, userRole).map((account) => <button
                  key={account.id}
                  type="button"
                  className="macos-popover-item"
                  role="menuitem"
                  onClick={() => { setPopoverOpen(false); onSwitchAccount?.(account); }}
                >
                  <RoleIcon role={account.role} />
                  <span>{account.role === "doctor" || account.role === "clinician" ? "Demo Doctor" : account.name} <small>· {formatRole(account.role)}</small></span>
                </button>)}
              </>}

              <div className="macos-popover-divider" role="separator" />

              <button
                type="button"
                className="macos-popover-item macos-popover-logout"
                role="menuitem"
                onClick={() => {
                  setPopoverOpen(false);
                  onLogout?.();
                }}
              >
                <LogOut size={18} aria-hidden="true" />
                <span>Log out</span>
              </button>
            </div>
          )}

          <button
            type="button"
            className={`macos-profile-btn ${popoverOpen ? "popover-open" : ""} ${activeView === "account" ? "active-account" : ""}`}
            aria-haspopup="menu"
            aria-expanded={popoverOpen}
            onClick={() => setPopoverOpen((prev) => !prev)}
            title={!open ? `${displayName} (${roleLabel})` : undefined}
          >
            <div className="macos-avatar" style={{ backgroundColor: avatarColor }} aria-hidden="true">
              {initials}
            </div>
            {open && (
              <>
                <div className="macos-profile-meta">
                  <strong className="macos-profile-name" title={displayName}>
                    {displayName}
                  </strong>
                  <span className="macos-profile-role">{roleLabel}</span>
                </div>
                <ChevronRight size={15} className="macos-profile-chevron" aria-hidden="true" />
              </>
            )}
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
