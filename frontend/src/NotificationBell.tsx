import { useEffect, useRef, useState } from "react";
import { Bell, X, Check, MailCheck, Trash2, Undo2 } from "lucide-react";
import { request } from "./api";
import Alert1, { type AlertTone } from "./components/watermelon/alert-1";

type Notification = {
  id: string; case_id: string | null; message: string; created_at: string;
  read_at: string | null; alert_level?: string;
};

export default function NotificationBell({ token, onOpenCase }: {
  token: string; onOpenCase: (id: string) => void;
}) {
  const [items, setItems] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reading, setReading] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [selecting, setSelecting] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [inboxUnread, setInboxUnread] = useState(0);
  const selectAll = useRef<HTMLInputElement>(null);
  const revision = useRef(0);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const unread = inboxUnread;
  const busy = bulkBusy || reading !== null;
  useEffect(() => { if (selectAll.current) selectAll.current.indeterminate = selected.length > 0 && selected.length < items.length; }, [selected, items, open]);

  useEffect(() => {
    let active = true;
    async function refresh() {
      const version = ++revision.current;
      try {
        const inbox = await request<Notification[]>("/api/notifications", token);
        const next = deleted ? await request<Notification[]>("/api/notifications?deleted=true", token) : inbox;
        if (active && version === revision.current) { setItems(next); setInboxUnread(inbox.filter(item => !item.read_at).length); setSelected(previous => previous.filter(id => next.some(item => item.id === id))); setError(""); }
      } catch (cause) { if (active) setError((cause as Error).message); }
      finally { if (active) setLoading(false); }
    }
    void refresh();
    const interval = window.setInterval(() => { if (!document.hidden) void refresh(); }, 60_000);
    return () => { active = false; window.clearInterval(interval); };
  }, [token, open, deleted]);

  async function bulk(action: "read" | "delete" | "restore") {
    if (busy || !selected.length) return;
    const ids = [...selected];
    ++revision.current;
    setBulkBusy(true); setError(""); setFeedback("");
    try {
      await request("/api/notifications/bulk", token, {ids, action}, "POST");
      const inbox = await request<Notification[]>("/api/notifications", token);
      const next = deleted ? await request<Notification[]>("/api/notifications?deleted=true", token) : inbox;
      ++revision.current;
      setItems(next); setInboxUnread(inbox.filter(item => !item.read_at).length);
      setSelected([]); setConfirmDelete(false);
      setFeedback(`${ids.length} notification${ids.length === 1 ? "" : "s"} ${action === "read" ? "marked as read" : action === "delete" ? "moved to Deleted. You can restore them there" : "restored to Inbox"}.`);
    } catch (cause) { setError((cause as Error).message); }
    finally { setBulkBusy(false); }
  }

  useEffect(() => {
    if (!open) return;
    closeButton.current?.focus();
    function outside(event: PointerEvent) {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    }
    function escape(event: KeyboardEvent) {
      if (event.key === "Escape") { setOpen(false); trigger.current?.focus(); }
    }
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  async function select(item: Notification) {
    if (busy) return;
    setReading(item.id); setError("");
    try {
      if (!item.read_at) {
        const result = await request<{ read_at: string }>(`/api/notifications/${item.id}/read`, token, undefined, "POST");
        setItems(previous => previous.map(row => row.id === item.id ? { ...row, read_at: result.read_at } : row));
        if (!deleted) setInboxUnread(value => Math.max(0, value - 1));
      }
      if (item.case_id) { onOpenCase(item.case_id); setOpen(false); trigger.current?.focus(); }
    } catch (cause) { setError((cause as Error).message); }
    finally { setReading(null); }
  }

  return <div className="notification-center" ref={root}>
    <button ref={trigger} type="button" className="notification-trigger" aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`} aria-expanded={open} aria-controls="notification-panel" onClick={() => setOpen(value => !value)}>
      <Bell size={22} aria-hidden="true" />
      {unread > 0 && <span className="notification-count" aria-hidden="true">{unread > 99 ? "99+" : unread}</span>}
    </button>
    {open && <section id="notification-panel" className="notification-panel" aria-labelledby="notification-title">
      <div className="notification-heading"><div><h2 id="notification-title">{selecting ? `${selected.length} Selected` : "Notifications"}</h2><small>{unread} unread · latest 100</small></div><div className="notification-heading-actions">{items.length > 0 && <button type="button" disabled={busy} onClick={() => { setSelecting(!selecting); setSelected([]); setConfirmDelete(false); }}>{selecting ? "Cancel" : "Select"}</button>}<button ref={closeButton} type="button" aria-label="Close notifications" onClick={() => { setOpen(false); trigger.current?.focus(); }}><X size={20} aria-hidden="true" /></button></div></div>
      <div className="notification-tabs" role="group" aria-label="Notification view">{[false,true].map(value => <button key={String(value)} type="button" disabled={busy} aria-pressed={deleted === value} onClick={() => { setDeleted(value); setSelected([]); setConfirmDelete(false); setFeedback(""); setItems([]); setLoading(true); }}>{value ? "Deleted" : "Inbox"}</button>)}{!deleted && items.length > 0 && <button type="button" disabled={busy || loading} title="Move all shown inbox notifications to Deleted" onClick={() => { setSelecting(true); setSelected(items.map(item => item.id)); setConfirmDelete(true); }}>Delete all</button>}</div>
      {loading && <p role="status">Loading notifications…</p>}
      {error && <Alert1 tone="error" title="Notifications could not be updated">{error}</Alert1>}
      {feedback && <p className="notification-feedback" role="status">{feedback}</p>}
      {selecting && !loading && items.length > 0 && <div className="notification-select-all"><label><input ref={selectAll} type="checkbox" checked={selected.length === items.length} disabled={busy} onChange={event => { setSelected(event.target.checked ? items.map(item => item.id) : []); setConfirmDelete(false); }} /><span>Select All</span></label><small>Shown {items.length} notifications</small></div>}
      {!loading && !error && !items.length && <p className="muted">{deleted ? "No deleted notifications." : "You’re all caught up. No notifications yet."}</p>}
      <ul className={`notification-list${selecting ? " is-selecting" : ""}`}>{items.map(item => <li key={item.id} className={selected.includes(item.id) ? "is-selected" : ""} onClick={event => {
        if (selecting && !busy && !(event.target as HTMLElement).closest("button,input,label")) { setSelected(previous => previous.includes(item.id) ? previous.filter(id => id !== item.id) : [...previous,item.id]); setConfirmDelete(false); }
      }}>
        {selecting && <label className="notification-select"><input type="checkbox" aria-label={`Select notification: ${item.message}`} checked={selected.includes(item.id)} disabled={busy} onChange={event => { setSelected(previous => event.target.checked ? [...previous, item.id] : previous.filter(id => id !== item.id)); setConfirmDelete(false); }} /><span className="notification-check-circle" aria-hidden="true">{selected.includes(item.id) && <Check size={16}/>}</span></label>}
        <Alert1 announce={false} unread={!item.read_at} tone={({warning:"warning",critical:"error",error:"error",success:"success"} as Record<string,AlertTone>)[item.alert_level || ""] || "info"} title={item.message}>
          <small>{item.read_at ? "Read" : "Unread"} · {(item.alert_level || "informational").replaceAll("_", " ")}</small>
          <small><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></small>
          {!selecting && !deleted && (item.case_id || !item.read_at) && <button type="button" disabled={busy} onClick={() => void select(item)}>{reading === item.id ? "Updating…" : item.case_id ? "Open case" : "Mark as read"}</button>}
        </Alert1>
      </li>)}</ul>
      {selecting && <div className="notification-selection-footer">
        {confirmDelete && <div className="notification-delete-confirm"><p>Move {selected.length} selected notifications to Deleted? Cases and reports will not be removed.</p><button type="button" disabled={busy} onClick={() => void bulk("delete")}>Confirm delete</button><button type="button" disabled={busy} onClick={() => setConfirmDelete(false)}>Keep notifications</button></div>}
        <div className="notification-selection-toolbar" role="group" aria-label="Selected notification actions">{deleted ? <button type="button" disabled={busy || !selected.length} onClick={() => void bulk("restore")}><Undo2 size={20} aria-hidden="true"/>Restore selected</button> : <><button type="button" disabled={busy || !selected.length} onClick={() => void bulk("read")}><MailCheck size={20} aria-hidden="true"/>Mark as read</button><button type="button" disabled={busy || !selected.length} onClick={() => setConfirmDelete(true)}><Trash2 size={20} aria-hidden="true"/>Delete</button></>}</div>
        {bulkBusy && <p role="status">Updating notifications…</p>}
      </div>}
    </section>}
  </div>;
}
