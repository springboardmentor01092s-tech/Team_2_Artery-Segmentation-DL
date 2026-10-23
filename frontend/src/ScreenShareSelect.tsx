import { Children, isValidElement, useEffect, useLayoutEffect, useId, useRef, useState, type ReactNode } from "react";
import { Check, ChevronDown } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import "./components/watermelon/inline-disclosure-menu.css";

type Props = {
  id?: string;
  label?: string;
  value: string;
  children: ReactNode;
  onChange: (event: { target: { value: string } }) => void;
  multiple?: boolean;
  values?: string[];
  onValuesChange?: (values: string[]) => void;
};

/** In-page options are captured by browser-window screen sharing, unlike OS menus. */
export default function ScreenShareSelect({ id, label, value, children, onChange, multiple = false, values = [], onValuesChange }: Props) {
  const listId = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const root = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [side, setSide] = useState<"above" | "below">("below");
  useLayoutEffect(() => {
    if (!open || !trigger.current) return;
    const rect = trigger.current.getBoundingClientRect();
    const below = window.innerHeight - rect.bottom;
    setSide(below < 280 && rect.top > below ? "above" : "below");
  }, [open]);
  useEffect(() => {
    const outside = (event: PointerEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false); };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, []);
  useLayoutEffect(() => {
    if (!open) return;
    const list = document.getElementById(listId);
    const option = document.getElementById(`${listId}-${active}`);
    if (!list || !option) return;
    const top = option.offsetTop;
    if (top < list.scrollTop) list.scrollTop = top;
    else if (top + option.offsetHeight > list.scrollTop + list.clientHeight) list.scrollTop = top + option.offsetHeight - list.clientHeight;
  }, [active, open, listId]);
  const options = Children.toArray(children).filter(isValidElement).map(child => {
    const props = child.props as { value?: string; children: ReactNode };
    const label = Children.toArray(props.children).join("");
    return { value: props.value ?? label, label };
  });
  const choose = (index: number) => {
    if (!options[index]) return;
    if (multiple) {
      const selected = options[index].value;
      onValuesChange?.(values.includes(selected) ? values.filter(item => item !== selected) : [...values, selected]);
      trigger.current?.focus({preventScroll:true});
      return;
    }
    onChange({ target: { value: options[index].value } });
    setOpen(false);
    trigger.current?.focus({preventScroll:true});
  };
  return <div ref={root} className={`screen-share-select${open ? " is-open" : ""}`} onBlur={event => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }}>
    <button id={id} ref={trigger} type="button" role="combobox" aria-haspopup="listbox" aria-label={label}
      aria-expanded={open} aria-controls={listId}
      aria-activedescendant={open ? `${listId}-${active}` : undefined}
      onClick={() => { setActive(Math.max(0, options.findIndex(o => o.value === value))); setOpen(!open); }}
      onKeyDown={event => {
        if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
          event.preventDefault();
          const selected = Math.max(0, options.findIndex(o => o.value === value));
          setActive(event.key === "Home" ? 0 : event.key === "End" ? options.length - 1 :
            Math.max(0, Math.min(options.length - 1, (open ? active : selected) + (event.key === "ArrowDown" ? 1 : -1))));
          setOpen(true);
        } else if (open && ["Enter", " "].includes(event.key)) {
          event.preventDefault(); choose(active);
        } else if (event.key === "Escape" && open) { event.preventDefault(); event.stopPropagation(); setOpen(false); }
        else if (event.key.length === 1 && event.key !== " ") {
          const index = options.findIndex(o => o.label.toLowerCase().startsWith(event.key.toLowerCase()));
          if (index >= 0) { setActive(index); setOpen(true); }
        }
      }}><span>{multiple ? values.length ? options.filter(option => values.includes(option.value)).map(option => option.label).join(", ") : "Select one or more" : options.find(o => o.value === value)?.label ?? "Select an option"}</span><ChevronDown size={17} aria-hidden="true"/></button>
    {open && <motion.div id={listId} role="listbox" aria-multiselectable={multiple || undefined} data-side={side} aria-label={label || "Available options"} className="screen-share-options cv-selection-disclosure"
      initial={reduced ? false : {opacity:0,y:3}} animate={{opacity:1,y:0}} transition={{duration:reduced ? 0 : .15}}>
      <div className="cv-inline-menu-heading" aria-hidden="true">{label || "Choose an option"}</div>
      {options.map((option, index) => <div key={option.value} id={`${listId}-${index}`} role="option"
        aria-selected={multiple ? values.includes(option.value) : option.value === value} className={active === index ? "is-highlighted" : ""}
        onMouseDown={event => event.preventDefault()} onMouseMove={() => setActive(index)} onClick={event => { event.preventDefault(); event.stopPropagation(); choose(index); }}>
        <span>{option.label}</span>{(multiple ? values.includes(option.value) : option.value === value) && <Check size={16} aria-hidden="true"/>}
      </div>)}
    </motion.div>}
  </div>;
}
