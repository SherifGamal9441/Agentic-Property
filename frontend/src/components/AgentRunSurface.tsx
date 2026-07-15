import { useEffect, useRef } from "react";

import { money, percent } from "../format";
import PropertyVisual from "./PropertyVisual";
import type { BuyerBrief, Property, PropertyGuidance, RunStats, RunStatus, TraceStep } from "../types";

function Trace({ steps }: { steps: TraceStep[] }) {
  const unique = Object.entries(steps.reduce<Record<string, TraceStep>>((all, step) => ({ ...all, [step.node]: step }), {}));
  return <ol className="agent-trace">{unique.map(([node, step], index) => <li className={step.status === "completed" ? "is-complete" : "is-active"} key={node}><span>{String(index + 1).padStart(2, "0")}</span><div><b>{step.label}</b><small>{step.status}{step.duration_ms != null ? ` · ${step.duration_ms} ms` : ""}</small></div></li>)}</ol>;
}

export default function AgentRunSurface({ status, trace, properties, guidance, stats, brief, webAnswer, error, copied, onCancel, onRetry, onEdit, onSelect, onCompare, onCopy }: {
  status: RunStatus;
  trace: TraceStep[];
  properties: Property[];
  guidance: PropertyGuidance | null;
  stats: RunStats;
  brief: BuyerBrief | null;
  webAnswer: string;
  error: string;
  copied: boolean;
  onCancel: () => void;
  onRetry: () => void;
  onEdit: () => void;
  onSelect: (property: Property) => void;
  onCompare: () => void;
  onCopy: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (status !== "completed" || document.querySelector('[role="dialog"]')) return;
    heading.current?.focus({ preventScroll: true });
    heading.current?.scrollIntoView?.({ behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  }, [status]);
  if (status === "idle") return null;

  if (status === "interpreting" || status === "running") return <section className="agent-progress dark-surface" aria-live="polite"><div><p className="eyebrow">Live agent run</p><h2>{status === "interpreting" ? <>Interpreting your brief.<br />Preparing the evidence run.</> : <>Calm on the surface.<br />Auditable underneath.</>}</h2><p className="agent-supporting">{status === "interpreting" ? "Aizen is converting your request into structured buyer criteria." : "Live model reasoning stays private. Verified steps remain visible."}</p>{status === "running" && <button className="button-outline-light" type="button" onClick={onCancel}>Cancel run</button>}</div>{status === "running" ? <Trace steps={trace} /> : <div className="interpret-pulse" aria-hidden="true"><span /><span /><span /></div>}</section>;

  if (status === "failed" || status === "cancelled") return <section className="agent-state dark-surface" aria-live="polite"><p className="eyebrow">{status === "cancelled" ? "Research cancelled" : "Live research interrupted"}</p><h2 ref={heading} tabIndex={-1}>{status === "cancelled" ? "Your brief is ready when you are." : "Aizen could not complete this live run."}</h2><p>{error || (status === "cancelled" ? "No result was saved or replayed." : "Check the selected provider and try again.")}</p><div className="result-actions"><button type="button" className="button-champagne" onClick={onRetry}>Run again</button>{brief && <button type="button" className="button-outline-light" onClick={onEdit}>Edit brief</button>}</div></section>;

  const eligible = properties.filter((property) => property.suitability !== "excluded");
  const suitable = eligible.filter((property) => property.suitability === "suitable");
  const best = properties.find((property) => property.id === guidance?.best_match_id) || eligible[0];
  const runner = properties.find((property) => property.id === guidance?.runner_up_id) || eligible[1];
  const outcome = guidance?.outcome || (suitable.length ? "matches" : eligible.length ? "conditional" : "no_match");
  const outcomeHeadline = brief?.mode === "web_research" ? "Research complete" : outcome === "matches" ? `${suitable.length} ${suitable.length === 1 ? "home meets" : "homes meet"} your brief` : outcome === "conditional" ? `${eligible.length} promising ${eligible.length === 1 ? "home" : "homes"}—with evidence gaps` : "No exact snapshot match";
  const caveats = Array.from(new Set([...(best?.conflicting_criteria || []), ...(best?.unknown_criteria || []), ...(best?.unsupported_criteria || []), ...(runner?.conflicting_criteria || []), ...(runner?.unknown_criteria || []), ...(runner?.unsupported_criteria || [])]));
  const tied = Boolean(best && runner && best.fit_score === runner.fit_score && best.evidence_coverage === runner.evidence_coverage);

  return <section className="result-takeover dark-surface" aria-live="polite"><div className="result-intro"><p className="eyebrow">Research complete</p><h2 ref={heading} tabIndex={-1}>{outcomeHeadline}</h2><p>{brief?.mode === "web_research" ? "Live cited research is ready below." : `Audited against the frozen listing snapshot${best?.dataset_snapshot_at ? ` dated ${best.dataset_snapshot_at}` : ""}.`}</p></div>
    {brief?.mode === "web_research" ? <div className="web-result"><p>{webAnswer}</p></div> : <>
      <div className="result-metrics"><div><strong>{outcome === "matches" ? suitable.length : eligible.length}</strong><span>{outcome === "matches" ? "Homes meeting brief" : "Promising homes"}</span></div><div><strong>{stats.audited_count}</strong><span>Candidates audited</span></div><div><strong>{best ? percent(best.evidence_coverage) : "—"}</strong><span>Top-match evidence</span></div></div>
      {best && <article className="hero-match"><div><PropertyVisual property={best} rank={1} large /><p className="eyebrow">Top-ranked home</p><h3>{best.title}</h3><p>{best.area} · {best.beds ?? "?"} bed · {best.completion_status || "completion unknown"}</p><strong>{money(best.price)}</strong></div><dl><div><dt>Deterministic fit</dt><dd>{percent(best.fit_score)}</dd></div><div><dt>Evidence coverage</dt><dd>{percent(best.evidence_coverage)}</dd></div><div><dt>Criteria matched</dt><dd>{best.matched_criteria.length}</dd></div><div><dt>Unknown criteria</dt><dd>{best.unknown_criteria.length + best.unsupported_criteria.length}</dd></div></dl></article>}
      <div className="guidance-grid"><section><p className="eyebrow">Best match</p>{best ? <><button className="guidance-property" type="button" onClick={() => onSelect(best)}>{best.title} ↗</button><p>{best.matched_criteria.length ? `Matches ${best.matched_criteria.join(", ")}.` : "No supported criterion match was recorded."}</p></> : <p>No property met every confirmed hard rule.</p>}</section><section><p className="eyebrow">Runner-up</p>{runner ? <><button className="guidance-property" type="button" onClick={() => onSelect(runner)}>{runner.title} ↗</button><p>{runner.matched_criteria.length ? `Matches ${runner.matched_criteria.join(", ")}.` : "Review its evidence profile before deciding."}</p></> : <p>No second eligible home was audited.</p>}</section><section><p className="eyebrow">What to verify</p><p>{caveats.length ? caveats.join(", ") : "No known criterion gaps in the captured fields."}</p><small>Captured listing evidence is not a property inspection.</small></section></div>
      {tied && <p className="tie-note">Top homes are tied on fit and evidence. Stable ordering uses reported price, then property ID.</p>}
      <div className="result-actions">{best && <button type="button" className="button-champagne" onClick={() => onSelect(best)}>Review best match</button>}{runner && <button type="button" className="button-outline-light" onClick={onCompare}>Compare top matches</button>}<button type="button" className="button-outline-light" onClick={onEdit}>Edit brief</button><button type="button" className="button-outline-light" onClick={onCopy}>{copied ? "Copied" : "Copy decision summary"}</button></div>
    </>}
    {trace.length > 0 && <details className="trace-details"><summary>View agent trace</summary><Trace steps={trace} /></details>}
  </section>;
}
