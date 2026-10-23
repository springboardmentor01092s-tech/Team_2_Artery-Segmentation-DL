// Adapted from Watermelon's inline-disclosure-menu registry.
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { MoreVertical, Trash2 } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import "./inline-disclosure-menu.css";

export interface MenuItemProps { icon: ReactNode; label: string; onClick?: () => void; className?: string; disabled?: boolean; }
export interface InlineDisclosureMenuProps {
  menuItems?: MenuItemProps[]; showDelete?: boolean; onDelete?: () => void;
  menuLabel?: string; triggerLabel?: string; className?: string;
}
export function InlineDisclosureMenu({ menuItems = [], showDelete = false, onDelete, menuLabel = "More options", triggerLabel = "Open more options", className = "" }: InlineDisclosureMenuProps) {
  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const id = useId();
  const reduced = useReducedMotion();
  function close(restore = false) { setOpen(false); setConfirm(false); if (restore) trigger.current?.focus(); }
  useEffect(() => {
    const outside = (event: PointerEvent) => { if (!ref.current?.contains(event.target as Node)) { setOpen(false); setConfirm(false); } };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, []);
  useEffect(() => { if (open) ref.current?.querySelector<HTMLButtonElement>('[role="menuitem"]:not(:disabled)')?.focus(); }, [open, confirm]);
  return <div ref={ref} className={`cv-inline-menu ${className}`} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) close(); }} onKeyDown={event => {
    if (event.key === "Escape" && open) { event.preventDefault(); event.stopPropagation(); close(true); }
    if (open && ["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const items = [...(ref.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]:not(:disabled)') || [])];
      const index = items.indexOf(document.activeElement as HTMLButtonElement);
      const next = event.key === "Home" ? 0 : event.key === "End" ? items.length - 1 : (index + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      items[next]?.focus();
    }
  }}>
    <button ref={trigger} type="button" className="cv-inline-menu-trigger" aria-label={triggerLabel} aria-haspopup="menu" aria-expanded={open} aria-controls={open ? id : undefined}
      onClick={() => open ? close(true) : setOpen(true)} onKeyDown={event => { if (["ArrowDown", "ArrowUp"].includes(event.key)) { event.preventDefault(); setOpen(true); } }}><MoreVertical size={20} aria-hidden="true"/></button>
    {open && <motion.div id={id} role="menu" aria-label={menuLabel} className="cv-inline-menu-panel"
      initial={reduced ? false : {opacity:0, scale:.98}} animate={{opacity:1, scale:1}} transition={{duration:reduced ? 0 : .15}}>
      <div className="cv-inline-menu-heading">{menuLabel}</div>
      <div className="cv-inline-menu-items">{menuItems.map(item => <button key={item.label} type="button" role="menuitem" disabled={item.disabled || !item.onClick} className={item.className}
        onClick={() => { close(true); item.onClick?.(); }}><span aria-hidden="true">{item.icon}</span><span>{item.label}</span></button>)}
      {!menuItems.length && !showDelete && <p>No actions available.</p>}</div>
      {showDelete && onDelete && <div className="cv-inline-menu-confirm">{confirm ? <><p>Confirm deletion?</p><button type="button" role="menuitem" onClick={() => { close(true); onDelete(); }}>Confirm delete</button><button type="button" role="menuitem" onClick={() => setConfirm(false)}>Cancel</button></> : <button type="button" role="menuitem" onClick={() => setConfirm(true)}><Trash2 size={18} aria-hidden="true"/>Delete</button>}</div>}
    </motion.div>}
  </div>;
}
