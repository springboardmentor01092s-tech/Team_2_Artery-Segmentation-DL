// Adapted from https://registry.watermelon.sh/r/create-new-disclosure.json
// Controlled case actions replace the source's non-functional demo tiles.
import { useEffect, useId, useRef, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import { FolderPlus, Search, X, Plus } from "lucide-react";
import { Button } from "../prismui/button";
import "./create-new-disclosure.css";

export function CreateNewDisclosure({ mode, onModeChange, canCreate, createContent, findContent }: {
  mode: "create" | "find" | null;
  onModeChange: (mode: "create" | "find" | null) => void;
  canCreate: boolean;
  createContent: ReactNode;
  findContent: ReactNode;
}) {
  const id = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (mode) content.current?.querySelector<HTMLInputElement>("input")?.focus();
  }, [mode]);
  function close() { onModeChange(null); trigger.current?.focus(); }
  return <div className="cv-case-disclosure" onKeyDown={event => {
    if (event.key === "Escape" && mode) { event.preventDefault(); event.stopPropagation(); close(); }
  }}>
    <Button ref={trigger} type="button" variant="outline" className="cv-case-disclosure-trigger"
      aria-expanded={!!mode} aria-controls={id} onClick={() => mode ? close() : onModeChange(canCreate ? "create" : "find")}>
      <Plus size={18} aria-hidden="true"/><span>Case actions</span><span className="cv-disclosure-hint">{mode ? "Close" : "Open"}</span>
    </Button>
    {mode && <motion.section id={id} className="cv-case-disclosure-panel" aria-label="Case actions"
      initial={reduced ? false : {opacity:0, y:4}} animate={{opacity:1,y:0}} transition={{duration:reduced ? 0 : .16}}>
      <header><div><strong>Your case workspace</strong><p>Create a study or find an existing case.</p></div><Button type="button" size="icon" variant="ghost" onClick={close} aria-label="Close case actions"><X size={18} aria-hidden="true"/></Button></header>
      <div className="cv-case-disclosure-choices" role="group" aria-label="Choose a case action">
        {canCreate && <button type="button" aria-pressed={mode === "create"} onClick={() => onModeChange("create")}><FolderPlus size={21} aria-hidden="true"/><strong>Create case</strong><small>New study</small></button>}
        <button type="button" aria-pressed={mode === "find"} onClick={() => onModeChange("find")}><Search size={21} aria-hidden="true"/><strong>Find case</strong><small>Search & filter</small></button>
      </div>
      <div ref={content} className="cv-case-disclosure-content">{mode === "create" ? createContent : findContent}</div>
    </motion.section>}
  </div>;
}
