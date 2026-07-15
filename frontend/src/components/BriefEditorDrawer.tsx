import { useRef, useState } from "react";

import type { BuyerBrief, Criterion } from "../types";
import useDialogTrap from "./useDialogTrap";

const priorities = ["must_have", "nice_to_have", "deal_breaker"] as const;

export default function BriefEditorDrawer({ brief, highlightedId, onClose, onApply }: {
  brief: BuyerBrief;
  highlightedId?: string | null;
  onClose: () => void;
  onApply: (brief: BuyerBrief) => void;
}) {
  const drawer = useRef<HTMLElement>(null);
  const [draft, setDraft] = useState<BuyerBrief>(() => ({ ...brief, criteria: brief.criteria.map((item) => ({ ...item })) }));
  useDialogTrap(drawer, onClose);
  const update = (id: string, patch: Partial<Criterion>) => setDraft((current) => ({
    ...current,
    criteria: current.criteria.map((criterion) => criterion.id === id ? { ...criterion, ...patch } : criterion),
  }));

  return <div className="dialog-backdrop" onMouseDown={onClose}><aside ref={drawer} className="brief-drawer" role="dialog" aria-modal="true" aria-label="Edit buyer brief" onMouseDown={(event) => event.stopPropagation()}>
    <button type="button" className="icon-button" onClick={onClose} aria-label="Close brief editor">×</button>
    <p className="eyebrow">Buyer-controlled criteria</p><h2>Edit your brief</h2><p className="muted">Changes apply only when you run the research again.</p>
    {priorities.map((priority) => <section className="criterion-group" key={priority}><h3>{priority.replaceAll("_", " ")}</h3><div className="criterion-list">{draft.criteria.filter((criterion) => criterion.priority === priority).map((criterion) => <div className={`criterion-chip ${!criterion.verifiable ? "is-unverifiable" : ""} ${criterion.id === highlightedId ? "is-highlighted" : ""}`} key={criterion.id}>
      <input aria-label={`Label for ${criterion.label}`} value={criterion.label} onChange={(event) => update(criterion.id, { label: event.target.value })} />
      <input aria-label={`Value for ${criterion.label}`} value={criterion.value == null ? "Not verifiable" : String(criterion.value)} disabled={!criterion.verifiable} onChange={(event) => update(criterion.id, { value: typeof criterion.value === "number" ? Number(event.target.value) : event.target.value })} />
      <select aria-label={`Priority for ${criterion.label}`} value={criterion.priority} onChange={(event) => update(criterion.id, { priority: event.target.value as Criterion["priority"] })}><option value="must_have">Must-have</option><option value="nice_to_have">Nice-to-have</option><option value="deal_breaker">Deal-breaker</option></select>
      <button type="button" aria-label={`Remove ${criterion.label}`} onClick={() => setDraft((current) => ({ ...current, criteria: current.criteria.filter((item) => item.id !== criterion.id) }))}>×</button>
    </div>)}</div></section>)}
    <div className="drawer-actions"><button type="button" onClick={onClose}>Discard changes</button><button type="button" className="button-dark" onClick={() => onApply(draft)}>Apply & rerun</button></div>
  </aside></div>;
}
