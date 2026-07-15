import { lazy, Suspense, useEffect, useRef, useState } from "react";

import { compareAreas, interpretBrief, runBrief } from "./api";
import BrandMark from "./components/BrandMark";
import CaseStudy from "./components/CaseStudy";
import { calculateScenario } from "./finance";
import { readLocal, resetAizenStorage, writeLocal } from "./storage";
import type { AffordabilityInput, BuyerBrief, Criterion, MarketContext, Property, Relaxation, SourceItem, TraceStep } from "./types";

const LocationView = lazy(() => import("./components/LocationView"));
const PRESETS = [
  "Ready 2BR in Dubai Marina under AED 2M, no off-plan.",
  "Ready 3BR in Al Furjan under AED 3M.",
  "Furnished 1BR in Business Bay under AED 1.5M.",
];
const money = (value: number | null | undefined) => value == null ? "Not reported" : new Intl.NumberFormat("en-AE", { style: "currency", currency: "AED", maximumFractionDigits: 0 }).format(value);
const percent = (value: number | null | undefined) => value == null ? "Unknown" : `${Math.round(value * 100)}%`;

type View = "results" | "location" | "areas" | "affordability";
type Notes = Record<string, string>;
type BuyerStatus = Record<string, "saved" | "maybe" | "ruled_out">;
type ResearchSession = { threadId: string; title: string; lastActivityAt: string; brief: BuyerBrief };
type ScenarioForm = Record<"deposit" | "annualRate" | "years" | "transfer" | "finance" | "moving" | "annualService", string>;
const emptyScenario: ScenarioForm = { deposit: "", annualRate: "", years: "", transfer: "", finance: "", moving: "", annualService: "" };

function updateCriterion(brief: BuyerBrief, id: string, patch: Partial<Criterion>) {
  return { ...brief, criteria: brief.criteria.map((criterion) => criterion.id === id ? { ...criterion, ...patch } : criterion) };
}

function useDialogTrap(container: React.RefObject<HTMLElement | null>, onClose: () => void) {
  const closeHandler = useRef(onClose);
  closeHandler.current = onClose;
  useEffect(() => {
    const focusable = () => Array.from(container.current?.querySelectorAll<HTMLElement>('button, a[href], input, textarea, select, [tabindex]:not([tabindex="-1"])') || []).filter((item) => !item.hasAttribute("disabled"));
    focusable()[0]?.focus();
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeHandler.current();
      if (event.key !== "Tab") return;
      const items = focusable();
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [container]);
}

function EvidenceDrawer({ property, shortlisted, compared, note, status, onClose, onShortlist, onCompare, onNote, onStatus }: {
  property: Property; shortlisted: boolean; compared: boolean; note: string; status?: BuyerStatus[string]; onClose: () => void; onShortlist: () => void; onCompare: () => void; onNote: (value: string) => void; onStatus: (value: BuyerStatus[string]) => void;
}) {
  const drawer = useRef<HTMLElement>(null);
  useDialogTrap(drawer, onClose);
  return <div className="dialog-backdrop" onMouseDown={onClose}><aside ref={drawer} className="evidence-drawer" role="dialog" aria-modal="true" aria-label="Property evidence" onMouseDown={(event) => event.stopPropagation()}>
    <button type="button" className="icon-button" onClick={onClose} aria-label="Close property evidence">×</button>
    <p className="eyebrow">Captured listing evidence</p><h2>{property.title}</h2><p className="muted">{property.area} · snapshot {property.dataset_snapshot_at}</p><strong className="display-price">{money(property.price)}</strong>
    <div className="action-row"><button type="button" onClick={onShortlist}>{shortlisted ? "Remove from shortlist" : "Add to shortlist"}</button><button type="button" className="button-dark" onClick={onCompare}>{compared ? "Remove from comparison" : "Add to comparison"}</button></div>
    <section><h3>Evidence profile</h3><div className="evidence-meters"><div><span>Fit</span><b>{percent(property.fit_score)}</b></div><div><span>Coverage</span><b>{percent(property.evidence_coverage)}</b></div><div><span>Suitability</span><b>{property.suitability}</b></div></div></section>
    <section className="evaluation-groups"><div><h3>Matched</h3><ul>{property.matched_criteria.map((item) => <li key={item}>✓ {item}</li>)}</ul></div><div><h3>Conflicts & unknowns</h3><ul>{property.conflicting_criteria.map((item) => <li className="conflict" key={item}>× {item}</li>)}{property.unknown_criteria.map((item) => <li className="unknown" key={item}>? {item}</li>)}{property.unsupported_criteria.map((item) => <li className="unknown" key={item}>— {item} is not verifiable</li>)}</ul></div></section>
    <section><h3>Reported facts</h3><dl className="fact-grid"><div><dt>Bedrooms</dt><dd>{property.beds ?? "Not reported"}</dd></div><div><dt>Bathrooms</dt><dd>{property.baths ?? "Not reported"}</dd></div><div><dt>Furnishing</dt><dd>{property.furnishing || "Not reported"}</dd></div><div><dt>Completion</dt><dd>{property.completion_status || "Not reported"}</dd></div><div><dt>Unit size</dt><dd>Not verified</dd></div><div><dt>Dedicated parking</dt><dd>Not verified</dd></div></dl></section>
    <section><h3>Your private decision</h3><div className="segmented">{(["saved", "maybe", "ruled_out"] as const).map((value) => <button type="button" aria-pressed={status === value} onClick={() => onStatus(value)} key={value}>{value.replace("_", " ")}</button>)}</div><label>Private note<textarea aria-label="Private note" value={note} onChange={(event) => onNote(event.target.value)} placeholder="Questions, viewing notes, or what to verify next" /></label></section>
    <section className="source-box"><p className="eyebrow">Source honesty</p><p>Captured {property.observed_at || "date unavailable"} · {property.snapshot_id}</p>{property.source_url ? <a href={property.source_url} target="_blank" rel="noreferrer">Open captured source reference ↗</a> : <span>Source URL unavailable</span>}</section>
  </aside></div>;
}

function AreaComparison() {
  const [areas, setAreas] = useState(["Dubai Marina", "Business Bay"]);
  const [contexts, setContexts] = useState<MarketContext[]>([]);
  const [error, setError] = useState("");
  const compare = async () => { setError(""); try { setContexts(await compareAreas(areas.filter(Boolean))); } catch (reason) { setError(reason instanceof Error ? reason.message : "Area evidence is unavailable."); } };
  return <section className="tool-panel"><div className="section-heading"><div><p className="eyebrow">Historical context</p><h2>Compare reported area evidence</h2></div><p>Transactions provide context—not current inventory or valuation.</p></div><div className="area-inputs">{areas.map((area, index) => <input aria-label={`Area ${index + 1}`} value={area} key={index} onChange={(event) => setAreas((current) => current.map((item, itemIndex) => itemIndex === index ? event.target.value : item))} />)}{areas.length < 3 && <button type="button" onClick={() => setAreas((current) => [...current, ""])}>+ Third area</button>}<button className="button-dark" type="button" onClick={() => void compare()}>Compare evidence</button></div>{error && <p role="alert">{error}</p>}<div className="area-grid">{contexts.map((context) => <article key={context.area}><p className="eyebrow">{context.evidence_quality} evidence</p><h3>{context.area}</h3><strong>{money(context.price_median)}</strong><p>Median reported price</p><dl><div><dt>Middle 50%</dt><dd>{money(context.price_q1)} – {money(context.price_q3)}</dd></div><div><dt>Usable records</dt><dd>{context.usable_record_count ?? 0}</dd></div><div><dt>Period</dt><dd>{context.period_start || "—"} to {context.period_end || "—"}</dd></div></dl></article>)}</div></section>;
}

function Affordability({ property, form, onChange }: { property?: Property; form: ScenarioForm; onChange: (form: ScenarioForm) => void }) {
  const labels: Record<keyof ScenarioForm, string> = { deposit: "Deposit", annualRate: "Annual interest rate (%)", years: "Mortgage term (years)", transfer: "Transfer cost", finance: "Finance cost", moving: "Moving cost", annualService: "Annual service charge" };
  let scenario: ReturnType<typeof calculateScenario> | null = null;
  let error = "";
  if (property?.price != null && Object.values(form).every((value) => value !== "")) {
    try { scenario = calculateScenario({ price: property.price, ...Object.fromEntries(Object.entries(form).map(([key, value]) => [key, Number(value)])) } as AffordabilityInput); } catch (reason) { error = reason instanceof Error ? reason.message : "Scenario is invalid."; }
  }
  return <section className="tool-panel"><div className="section-heading"><div><p className="eyebrow">Buyer-entered assumptions</p><h2>Affordability scenario</h2></div><p>Buyer scenario—not financial advice.</p></div>{!property ? <p>Shortlist or compare a home to start a scenario.</p> : <><div className="scenario-home"><span>{property.title}</span><strong>{money(property.price)}</strong></div><div className="scenario-form">{(Object.keys(labels) as (keyof ScenarioForm)[]).map((key) => <label key={key}>{labels[key]}<input inputMode="decimal" min="0" value={form[key]} onChange={(event) => onChange({ ...form, [key]: event.target.value })} placeholder="Unknown" /></label>)}</div>{error && <p role="alert">{error}</p>}{scenario ? <div className="scenario-results"><div><span>Estimated monthly payment</span><strong>{money(scenario.monthlyPayment)}</strong></div><div><span>Cash at purchase</span><strong>{money(scenario.cashAtPurchase)}</strong></div><div><span>Annual property cost</span><strong>{money(scenario.annualPropertyCost)}</strong></div></div> : <p className="muted">Blank values remain unknown. Complete every assumption to calculate.</p>}</>}</section>;
}

function Dossier({ brief, properties, notes, form, onClose }: { brief: BuyerBrief | null; properties: Property[]; notes: Notes; form: ScenarioForm; onClose: () => void }) {
  const dossier = useRef<HTMLElement>(null);
  useDialogTrap(dossier, onClose);
  return <div className="dialog-backdrop dossier-backdrop"><section ref={dossier} className="dossier" role="dialog" aria-modal="true" aria-label="Buyer dossier"><div className="dossier-actions no-print"><button type="button" onClick={onClose}>Close</button><button type="button" className="button-dark" onClick={() => window.print()}>Print / Save as PDF</button></div><BrandMark /><p className="eyebrow">Private decision document</p><h1>Buyer dossier</h1><p>Generated from captured listing evidence and buyer-entered assumptions. Snapshot {properties[0]?.dataset_snapshot_at || "not yet selected"}.</p><section><h2>Confirmed brief</h2><p>{brief?.original_query || "No confirmed brief."}</p><ul>{brief?.criteria.map((criterion) => <li key={criterion.id}><b>{criterion.priority.replace("_", " ")}</b> · {criterion.label}{!criterion.verifiable && " · not verifiable"}</li>)}</ul></section><section><h2>Selected homes</h2>{properties.length ? properties.map((property) => <article className="dossier-home" key={property.id}><h3>{property.title}</h3><p>{property.area} · {money(property.price)} · fit {percent(property.fit_score)} · coverage {percent(property.evidence_coverage)}</p><p><b>Unknowns:</b> {[...property.unknown_criteria, ...property.unsupported_criteria].join(", ") || "None in the confirmed brief"}</p>{notes[property.id] && <p><b>Private note:</b> {notes[property.id]}</p>}{property.source_url && <p>Source: <a href={property.source_url}>{property.source_url}</a> · observed {property.observed_at}</p>}</article>) : <p>No homes selected.</p>}</section><section><h2>Affordability assumptions</h2><dl className="fact-grid">{Object.entries(form).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value || "Unknown"}</dd></div>)}</dl><p>Buyer scenario—not financial advice.</p></section></section></div>;
}

export default function App({ initialProperties = [], initialBrief = null }: { initialProperties?: Property[]; initialBrief?: BuyerBrief | null }) {
  const storedBrief = initialBrief || readLocal<BuyerBrief | null>("aizen-last-brief", null);
  const [hash, setHash] = useState(location.hash);
  const [query, setQuery] = useState(storedBrief?.original_query || "");
  const [draftBrief, setDraftBrief] = useState<BuyerBrief | null>(storedBrief);
  const [confirmedBrief, setConfirmedBrief] = useState<BuyerBrief | null>(storedBrief);
  const [properties, setProperties] = useState<Property[]>(initialProperties);
  const [shown, setShown] = useState(6);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [relaxations, setRelaxations] = useState<Relaxation[]>([]);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [interpreting, setInterpreting] = useState(false);
  const [running, setRunning] = useState(false);
  const [view, setView] = useState<View>("results");
  const [selected, setSelected] = useState<Property | null>(null);
  const [shortlist, setShortlist] = useState<string[]>(() => readLocal("aizen-shortlist", []));
  const [comparison, setComparison] = useState<string[]>(() => readLocal("aizen-comparison", []));
  const [notes, setNotes] = useState<Notes>(() => readLocal("aizen-notes", {}));
  const [statuses, setStatuses] = useState<BuyerStatus>(() => readLocal("aizen-statuses", {}));
  const [scenario, setScenario] = useState<ScenarioForm>(() => readLocal("aizen-affordability", emptyScenario));
  const [dossierOpen, setDossierOpen] = useState(false);
  const [sessions, setSessions] = useState<ResearchSession[]>(() => readLocal("aizen-research-sessions", []));
  const [threadId, setThreadId] = useState(() => localStorage.getItem("aizen-thread-id") || crypto.randomUUID());

  useEffect(() => { localStorage.setItem("aizen-thread-id", threadId); }, [threadId]);
  useEffect(() => { const listener = () => setHash(location.hash); window.addEventListener("hashchange", listener); return () => window.removeEventListener("hashchange", listener); }, []);
  useEffect(() => writeLocal("aizen-shortlist", shortlist), [shortlist]);
  useEffect(() => writeLocal("aizen-comparison", comparison), [comparison]);
  useEffect(() => writeLocal("aizen-notes", notes), [notes]);
  useEffect(() => writeLocal("aizen-statuses", statuses), [statuses]);
  useEffect(() => writeLocal("aizen-affordability", scenario), [scenario]);
  useEffect(() => writeLocal("aizen-research-sessions", sessions), [sessions]);
  useEffect(() => { if (confirmedBrief) writeLocal("aizen-last-brief", confirmedBrief); }, [confirmedBrief]);
  if (hash === "#/case-study") return <CaseStudy />;

  const interpret = async () => { setInterpreting(true); setError(""); try { setDraftBrief(await interpretBrief(query, threadId)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Brief interpretation failed."); } finally { setInterpreting(false); } };
  const confirmAndRun = async () => {
    if (!draftBrief) return;
    setConfirmedBrief(draftBrief); setRunning(true); setError(""); setProperties([]); setTrace([]); setSources([]); setRelaxations([]); setAnswer(""); setShown(6);
    try {
      await runBrief(draftBrief, threadId, {
        onStarted: () => undefined,
        onStep: (step) => setTrace((current) => [...current.filter((item) => !(item.node === step.node && item.status === step.status)), step]),
        onProperties: setProperties,
        onSources: setSources,
        onToken: (token) => setAnswer((current) => current + token),
        onRelaxations: setRelaxations,
        onCompleted: () => { setRunning(false); setSessions((current) => [{ threadId, title: draftBrief.original_query.slice(0, 64), lastActivityAt: new Date().toISOString(), brief: draftBrief }, ...current.filter((item) => item.threadId !== threadId)].slice(0, 8)); },
      });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The live run failed."); setRunning(false); }
  };
  const toggle = (items: string[], setItems: (value: string[]) => void, id: string, max?: number) => { if (items.includes(id)) setItems(items.filter((item) => item !== id)); else if (!max || items.length < max) setItems([...items, id]); else setError(`Choose up to ${max} homes.`); };
  const chosen = properties.filter((property) => comparison.includes(property.id) || shortlist.includes(property.id)).slice(0, 4);
  const reset = () => { resetAizenStorage(); setQuery(""); setDraftBrief(null); setConfirmedBrief(null); setProperties([]); setShortlist([]); setComparison([]); setNotes({}); setStatuses({}); setSessions([]); setScenario(emptyScenario); setAnswer(""); setTrace([]); setSources([]); setRelaxations([]); setThreadId(crypto.randomUUID()); window.setTimeout(resetAizenStorage, 0); };

  return <div className="app-shell">
    <header className="topbar"><BrandMark /><nav aria-label="Primary navigation"><button aria-current={view === "results"} onClick={() => setView("results")}>Homes</button><button aria-current={view === "location"} onClick={() => setView("location")}>Map</button><button aria-current={view === "areas"} onClick={() => setView("areas")}>Areas</button><button aria-current={view === "affordability"} onClick={() => setView("affordability")}>Affordability</button><a href="#/case-study">Case study</a></nav><div className="header-actions"><span>{shortlist.length} shortlisted</span><button type="button" onClick={() => setDossierOpen(true)}>Open buyer dossier</button><button type="button" className="text-button" onClick={reset}>Reset showcase</button></div></header>
    <main>
      <section className="hero"><div className="hero-copy"><p className="eyebrow">Dubai home-buying intelligence · frozen snapshot</p><h1>Decide with evidence.<br /><em>Not listing noise.</em></h1><p>Aizen interprets your brief, lets you correct it, then audits every recommendation against captured facts.</p><div className="trust-row"><span><b>8</b> agent nodes</span><span><b>20</b> candidates scored</span><span><b>0</b> invented facts</span></div></div><div className="brief-card"><p className="eyebrow">01 · Shape the search</p><label htmlFor="buyer-query">Describe your ideal Dubai home</label><textarea id="buyer-query" value={query} onChange={(event) => { setQuery(event.target.value); setDraftBrief(null); }} placeholder="Example: Ready 2BR in Dubai Marina under AED 2M, no off-plan" /><button className="button-primary" type="button" disabled={!query.trim() || interpreting} onClick={() => void interpret()}>{interpreting ? "Interpreting…" : "Interpret my brief"}</button><div className="preset-list"><span>Live demo presets</span>{PRESETS.map((preset, index) => <button type="button" key={preset} onClick={() => { setQuery(preset); setDraftBrief(null); }}><b>0{index + 1}</b>{preset}</button>)}</div>{sessions.length > 0 && <div className="preset-list recent-briefs"><span>Recent local briefs</span>{sessions.map((session) => <button type="button" key={session.threadId} onClick={() => { setThreadId(session.threadId); localStorage.setItem("aizen-thread-id", session.threadId); setQuery(session.brief.original_query); setDraftBrief(session.brief); setConfirmedBrief(session.brief); }}><b>↺</b>{session.title}</button>)}</div>}</div></section>

      {draftBrief && <section className="brief-confirm"><div className="section-heading"><div><p className="eyebrow">02 · Buyer confirmation required</p><h2>Confirm what Aizen understood</h2></div><p>Edit values or priorities before any listing search begins.</p></div>{(["must_have", "nice_to_have", "deal_breaker"] as const).map((priority) => <div className="criterion-group" key={priority}><h3>{priority.replaceAll("_", " ")}</h3><div className="criterion-list">{draftBrief.criteria.filter((criterion) => criterion.priority === priority).map((criterion) => <div className={`criterion-chip ${!criterion.verifiable ? "is-unverifiable" : ""}`} key={criterion.id}><input aria-label={`Label for ${criterion.label}`} value={criterion.label} onChange={(event) => setDraftBrief(updateCriterion(draftBrief, criterion.id, { label: event.target.value }))} /><input aria-label={`Value for ${criterion.label}`} value={criterion.value == null ? "Not verifiable" : String(criterion.value)} disabled={!criterion.verifiable} onChange={(event) => setDraftBrief(updateCriterion(draftBrief, criterion.id, { value: typeof criterion.value === "number" ? Number(event.target.value) : event.target.value }))} /><select aria-label={`Priority for ${criterion.label}`} value={criterion.priority} onChange={(event) => setDraftBrief(updateCriterion(draftBrief, criterion.id, { priority: event.target.value as Criterion["priority"] }))}><option value="must_have">Must-have</option><option value="nice_to_have">Nice-to-have</option><option value="deal_breaker">Deal-breaker</option></select><button type="button" aria-label={`Remove ${criterion.label}`} onClick={() => setDraftBrief({ ...draftBrief, criteria: draftBrief.criteria.filter((item) => item.id !== criterion.id) })}>×</button></div>)}</div></div>)}<div className="confirm-bar"><p><b>{draftBrief.criteria.filter((item) => item.verifiable).length}</b> dataset-verifiable · <b>{draftBrief.criteria.filter((item) => !item.verifiable).length}</b> visible unknowns</p><button className="button-dark" type="button" disabled={running} onClick={() => void confirmAndRun()}>{running ? "Live run in progress…" : "Confirm & search"}</button></div></section>}

      {(running || trace.length > 0) && <section className="agent-progress dark-surface"><div><p className="eyebrow">Live agent run</p><h2>Calm on the surface.<br />Auditable underneath.</h2>{answer && <p className="agent-answer">{answer}</p>}</div><ol>{Object.entries(trace.reduce<Record<string, TraceStep>>((acc, step) => ({ ...acc, [step.node]: step }), {})).map(([node, step], index) => <li className={step.status === "completed" ? "is-complete" : "is-active"} key={node}><span>{String(index + 1).padStart(2, "0")}</span><div><b>{step.label}</b><small>{step.status}{step.duration_ms != null ? ` · ${step.duration_ms} ms` : ""}</small></div></li>)}</ol></section>}
      {error && <div className="error-banner" role="alert">{error}<button type="button" onClick={() => setError("")}>Dismiss</button></div>}

      <section className="workspace"><div className="workspace-tabs" role="navigation" aria-label="Decision workspace">{(["results", "location", "areas", "affordability"] as View[]).map((item) => <button type="button" key={item} aria-current={view === item} onClick={() => setView(item)}>{item === "results" ? "Ranked homes" : item}</button>)}</div>
        {view === "results" && <><div className="section-heading"><div><p className="eyebrow">03 · Audited shortlist</p><h2>{properties.length ? `${properties.length} evidence-ranked homes` : "Your ranked homes will appear here"}</h2></div><p>Fit is deterministic. Unknown facts stay visible. Snapshot {properties[0]?.dataset_snapshot_at || "awaiting a confirmed run"}.</p></div><div className="property-grid">{properties.slice(0, shown).map((property, index) => <article className="property-card" aria-label={property.title} key={property.id}><div className="architecture-visual" aria-hidden="true"><span>{String(index + 1).padStart(2, "0")}</span><i /><i /><i /></div><div className="card-body"><div className="card-meta"><span className={`suitability ${property.suitability}`}>{property.suitability}</span><span>{percent(property.fit_score)} fit</span><span>{percent(property.evidence_coverage)} evidence</span></div><h3>{property.title}</h3><p>{property.area} · {property.beds ?? "?"} bed · {property.completion_status || "completion unknown"}</p><strong>{money(property.price)}</strong><ul>{property.matched_criteria.slice(0, 2).map((item) => <li key={item}>✓ {item}</li>)}{property.unknown_criteria.slice(0, 1).map((item) => <li className="unknown" key={item}>? {item}</li>)}</ul><div className="card-actions"><button type="button" onClick={() => setSelected(property)}>Review evidence</button><button type="button" aria-label={`${shortlist.includes(property.id) ? "Remove" : "Add"} ${property.title} ${shortlist.includes(property.id) ? "from" : "to"} shortlist`} aria-pressed={shortlist.includes(property.id)} onClick={() => toggle(shortlist, setShortlist, property.id)}>◇</button></div></div></article>)}</div>{shown < properties.length && <button className="view-more" type="button" onClick={() => setShown(properties.length)}>View {properties.length - shown} more homes</button>}{!running && confirmedBrief && !properties.length && <div className="no-results"><h3>No snapshot match met every confirmed hard rule.</h3><p>Aizen did not silently relax your brief. Review the impact below, then edit and reconfirm.</p>{relaxations.map((item) => <div key={item.criterion_id}><span>Remove {confirmedBrief.criteria.find((criterion) => criterion.id === item.criterion_id)?.label}</span><b>{item.resulting_match_count} resulting matches</b></div>)}</div>}{sources.length > 0 && <details className="sources"><summary>Captured sources ({sources.length})</summary><ol>{sources.map((source, index) => <li key={`${source.url}-${index}`}><a href={source.url} target="_blank" rel="noreferrer">[{index + 1}] {source.title}</a><span>Observed {source.observed_at || "date unavailable"}</span></li>)}</ol></details>}</>}
        {view === "location" && <Suspense fallback={<div className="loading-panel">Loading the zero-cost map surface…</div>}><LocationView properties={properties} selectedId={selected?.id} onSelect={setSelected} /></Suspense>}
        {view === "areas" && <AreaComparison />}
        {view === "affordability" && <Affordability property={chosen[0] || properties[0]} form={scenario} onChange={setScenario} />}
      </section>
    </main>
    {comparison.length > 0 && <aside className="comparison-tray dark-surface"><div><p className="eyebrow">Decision tray</p><b>{comparison.length} of 4 homes selected</b></div>{properties.filter((property) => comparison.includes(property.id)).map((property) => <button type="button" key={property.id} onClick={() => setSelected(property)}>{property.title}<span>{money(property.price)}</span></button>)}<button type="button" onClick={() => setDossierOpen(true)}>Build dossier ↗</button></aside>}
    {selected && <EvidenceDrawer property={selected} shortlisted={shortlist.includes(selected.id)} compared={comparison.includes(selected.id)} note={notes[selected.id] || ""} status={statuses[selected.id]} onClose={() => setSelected(null)} onShortlist={() => toggle(shortlist, setShortlist, selected.id)} onCompare={() => toggle(comparison, setComparison, selected.id, 4)} onNote={(note) => setNotes((current) => ({ ...current, [selected.id]: note }))} onStatus={(status) => setStatuses((current) => ({ ...current, [selected.id]: status }))} />}
    {dossierOpen && <Dossier brief={confirmedBrief} properties={chosen} notes={notes} form={scenario} onClose={() => setDossierOpen(false)} />}
  </div>;
}
