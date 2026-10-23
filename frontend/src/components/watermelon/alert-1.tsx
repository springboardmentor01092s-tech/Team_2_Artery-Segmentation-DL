// Adapted from https://registry.watermelon.sh/r/alert-1.json.
import type { ReactNode } from "react";
import { CircleAlert, CircleCheck, Info, TriangleAlert, X } from "lucide-react";
import "./alert-1.css";

export type AlertTone = "info" | "success" | "warning" | "error";
export default function Alert1({ title, children, tone = "info", announce = true, onDismiss, unread = false }: {
  title: ReactNode; children?: ReactNode; tone?: AlertTone; announce?: boolean;
  onDismiss?: () => void; unread?: boolean;
}) {
  const Icon = {info:Info, success:CircleCheck, warning:TriangleAlert, error:CircleAlert}[tone];
  return <div className={`cv-alert cv-alert-${tone}${unread ? " is-unread" : ""}`}
    role={announce ? tone === "error" ? "alert" : "status" : undefined} aria-atomic={announce ? true : undefined}>
    <Icon className="cv-alert-icon" size={20} aria-hidden="true"/>
    <div className="cv-alert-content"><div className="cv-alert-title">{title}</div>{children && <div className="cv-alert-description">{children}</div>}</div>
    {onDismiss && <button type="button" className="cv-alert-dismiss" aria-label="Dismiss message" onClick={onDismiss}><X size={17} aria-hidden="true"/></button>}
  </div>;
}
