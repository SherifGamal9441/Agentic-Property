import { lazy, Suspense, useEffect, useRef, useState } from "react";

import { compareAreas, interpretBrief, runBrief } from "./api";
import AgentRunSurface from "./components/AgentRunSurface";
import BrandMark from "./components/BrandMark";
import BriefEditorDrawer from "./components/BriefEditorDrawer";
import CaseStudy from "./components/CaseStudy";
import ComparisonView from "./components/ComparisonView";
import useDialogTrap from "./components/useDialogTrap";
import { calculateScenario } from "./finance";
import { money, percent } from "./format";
import { readLocal, resetAizenStorage, writeLocal } from "./storage";
import type { AffordabilityInput, BuyerBrief, MarketContext, Property, PropertyGuidance, Relaxation, RunStats, RunStatus, ScenarioForm, SourceItem, TraceStep } from "./types";

const LocationView = lazy(() => import("./components/LocationView"));
const PRESETS = [
  "Ready 2BR in Dubai Marina under AED 2M, no off-plan.",
  "Ready 3BR in Al Furjan under AED 3M.",
  "Furnished 1BR in Business Bay under AED 1.5M.",
];
const emptyStats: RunStats = { candidate_count: 0, audited_count: 0, total_matches: 0, shown_count: 0 };
const emptyScenario: ScenarioForm = { deposit: "", annualRate: "", years: "", transfer: "", finance: "", moving: "", annualService: "" };

type View = "results" | "comparison" | "location" | "areas" | "affordability";
type Notes = Record<string, string>;
type BuyerStatus = Record<string, "saved" | "maybe" | "ruled_out">;
type ResearchSession = { threadId: string; title: string; lastActivityAt: string; brief: BuyerBrief };

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

function Affordability({ properties, selectedId, form, onSelect, onChange }: { properties: Property[]; selectedId: string; form: ScenarioForm; onSelect: (id: string) => void; onChange: (form: ScenarioForm) => void }) {
  const property = properties.find((item) => item.id === selectedId) || properties[0];
  const labels: Record<keyof ScenarioForm, string> = { deposit: "Deposit", annualRate: "Annual interest rate (%)", years: "Mortgage term (years)", transfer: "Transfer cost", finance: "Finance cost", moving: "Moving cost", annualService: "Annual service charge" };
  let scenario: ReturnType<typeof calculateScenario> | null = null;
  let error = "";
  if (property?.price != null && Object.values(form).every((value) => value !== "")) {
    try { scenario = calculateScenario({ price: property.price, ...Object.fromEntries(Object.entries(form).map(([key, value]) => [key, Number(value)])) } as AffordabilityInput); } catch (reason) { error = reason instanceof Error ? reason.message : "Scenario is invalid."; }
  }
  return <section className="tool-panel"><div className="section-heading"><div><p className="eyebrow">Buyer-entered assumptions</p><h2>Affordability scenario</h2></div><p>Buyer scenario—not financial advice.</p></div>{!property ? <p>Shortlist or compare a home to start a scenario.</p> : <><label className="property-select">Scenario home<select aria-label="Affordability property" value={property.id} onChange={(event) => onSelect(event.target.value)}>{properties.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label><div className="scenario-home"><span>{property.title}</span><strong>{money(property.price)}</strong></div><div className="scenario-form">{(Object.keys(labels) as (keyof ScenarioForm)[]).map((key) => <label key={key}>{labels[key]}<input inputMode="decimal" min="0" value={form[key]} onChange={(event) => onChange({ ...form, [key]: event.target.value })} placeholder="Unknown" /></label>)}</div>{error && <p role="alert">{error}</p>}{scenario ? <div className="scenario-results"><div><span>Estimated monthly payment</span><strong>{money(scenario.monthlyPayment)}</strong></div><div><span>Cash at purchase</span><strong>{money(scenario.cashAtPurchase)}</strong></div><div><span>Annual property cost</span><strong>{money(scenario.annualPropertyCost)}</strong></div></div> : <p className="muted">Blank values remain unknown. Complete every assumption to calculate.</p>}</>}</section>;
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
  const [confirmedBrief, setConfirmedBrief] = useState<BuyerBrief | null>(storedBrief);
  const [briefEditorOpen, setBriefEditorOpen] = useState(false);
  const [highlightedCriterionId, setHighlightedCriterionId] = useState<string | null>(null);
  const [properties, setProperties] = useState<Property[]>(initialProperties);
  const [shown, setShown] = useState(6);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [relaxations, setRelaxations] = useState<Relaxation[]>([]);
  const [guidance, setGuidance] = useState<PropertyGuidance | null>(null);
  const [stats, setStats] = useState<RunStats>(() => initialProperties.length ? { candidate_count: initialProperties.length, audited_count: initialProperties.length, total_matches: initialProperties.length, shown_count: Math.min(6, initialProperties.length) } : emptyStats);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [runStatus, setRunStatus] = useState<RunStatus>(initialProperties.length ? "completed" : "idle");
  const [view, setView] = useState<View>("results");
  const [resultFilter, setResultFilter] = useState<"all" | "shortlisted">("all");
  const [selected, setSelected] = useState<Property | null>(null);
  const [shortlist, setShortlist] = useState<string[]>(() => readLocal("aizen-shortlist", []));
  const [comparison, setComparison] = useState<string[]>(() => readLocal("aizen-comparison", []));
  const [notes, setNotes] = useState<Notes>(() => readLocal("aizen-notes", {}));
  const [statuses, setStatuses] = useState<BuyerStatus>(() => readLocal("aizen-statuses", {}));
  const [scenario, setScenario] = useState<ScenarioForm>(() => readLocal("aizen-affordability", emptyScenario));
  const [affordabilityTarget, setAffordabilityTarget] = useState(() => readLocal("aizen-affordability-target", ""));
  const [dossierOpen, setDossierOpen] = useState(false);
  const [sessions, setSessions] = useState<ResearchSession[]>(() => readLocal("aizen-research-sessions", []));
  const [threadId, setThreadId] = useState(() => localStorage.getItem("aizen-thread-id") || crypto.randomUUID());
  const [recentRerun, setRecentRerun] = useState(false);
  const [copied, setCopied] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const briefTriggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => { localStorage.setItem("aizen-thread-id", threadId); }, [threadId]);
  useEffect(() => { const listener = () => setHash(location.hash); window.addEventListener("hashchange", listener); return () => window.removeEventListener("hashchange", listener); }, []);
  useEffect(() => writeLocal("aizen-shortlist", shortlist), [shortlist]);
  useEffect(() => writeLocal("aizen-comparison", comparison), [comparison]);
  useEffect(() => writeLocal("aizen-notes", notes), [notes]);
  useEffect(() => writeLocal("aizen-statuses", statuses), [statuses]);
  useEffect(() => writeLocal("aizen-affordability", scenario), [scenario]);
  useEffect(() => writeLocal("aizen-affordability-target", affordabilityTarget), [affordabilityTarget]);
  useEffect(() => writeLocal("aizen-research-sessions", sessions), [sessions]);
  useEffect(() => { if (confirmedBrief) writeLocal("aizen-last-brief", confirmedBrief); }, [confirmedBrief]);
  if (hash === "#/case-study") return <CaseStudy />;

  const beginRequest = () => { abortRef.current?.abort(); const controller = new AbortController(); abortRef.current = controller; return controller; };
  const clearRun = () => { setError(""); setProperties([]); setTrace([]); setSources([]); setRelaxations([]); setGuidance(null); setAnswer(""); setStats(emptyStats); setShown(6); setSelected(null); setCopied(false); };
  const handleFailure = (reason: unknown, controller: AbortController) => {
    if (abortRef.current !== controller) return;
    const isAbort = typeof reason === "object" && reason !== null && "name" in reason && reason.name === "AbortError";
    if (isAbort) { setRunStatus("cancelled"); setError(""); }
    else { setRunStatus("failed"); setError(reason instanceof Error ? reason.message : "The live run failed."); }
  };
  const executeBrief = async (brief: BuyerBrief, activeThreadId: string, controller: AbortController) => {
    clearRun(); setConfirmedBrief(brief); setRunStatus("running");
    await runBrief(brief, activeThreadId, {
      onStarted: () => undefined,
      onStep: (step) => setTrace((current) => [...current.filter((item) => !(item.node === step.node && item.status === step.status)), step]),
      onProperties: (payload) => { const count = payload.properties.length; setProperties(payload.properties); setStats({ candidate_count: payload.candidate_count ?? count, audited_count: payload.audited_count ?? count, total_matches: payload.total_matches ?? count, shown_count: payload.shown_count ?? Math.min(6, count) }); },
      onSources: setSources,
      onToken: (token) => setAnswer((current) => current + token),
      onRelaxations: setRelaxations,
      onGuidance: setGuidance,
      onCompleted: () => undefined,
    }, controller.signal);
    if (abortRef.current !== controller) return;
    setRunStatus("completed"); setRecentRerun(false);
    setSessions((current) => [{ threadId: activeThreadId, title: brief.original_query.slice(0, 64), lastActivityAt: new Date().toISOString(), brief }, ...current.filter((item) => item.threadId !== activeThreadId)].slice(0, 8));
  };
  const startSearch = async () => {
    if (!query.trim()) return;
    const controller = beginRequest(); clearRun(); setRunStatus("interpreting"); setRecentRerun(false);
    try { const brief = await interpretBrief(query, threadId, controller.signal); if (abortRef.current === controller) await executeBrief(brief, threadId, controller); }
    catch (reason) { handleFailure(reason, controller); }
    finally { if (abortRef.current === controller) abortRef.current = null; }
  };
  const rerunBrief = async (brief: BuyerBrief, activeThreadId = threadId, fromRecent = false) => {
    const controller = beginRequest(); setQuery(brief.original_query); setRecentRerun(fromRecent);
    try { await executeBrief(brief, activeThreadId, controller); }
    catch (reason) { handleFailure(reason, controller); }
    finally { if (abortRef.current === controller) abortRef.current = null; }
  };
  const cancelRun = () => { if (abortRef.current) { abortRef.current.abort(); setRunStatus("cancelled"); setError(""); } };
  const retry = () => { if (confirmedBrief) void rerunBrief(confirmedBrief); else void startSearch(); };
  const openBriefEditor = (criterionId: string | null = null) => { setHighlightedCriterionId(criterionId); setBriefEditorOpen(true); };
  const closeBriefEditor = () => { setBriefEditorOpen(false); setHighlightedCriterionId(null); window.setTimeout(() => briefTriggerRef.current?.focus(), 0); };
  const applyBrief = (brief: BuyerBrief) => { closeBriefEditor(); void rerunBrief(brief); };
  const toggle = (setItems: React.Dispatch<React.SetStateAction<string[]>>, id: string, max?: number) => setItems((current) => { if (current.includes(id)) return current.filter((item) => item !== id); if (max && current.length >= max) { setError(`Choose up to ${max} homes.`); return current; } return [...current, id]; });
  const compareTop = () => { const top = properties.filter((property) => property.suitability !== "excluded").slice(0, 2).map((property) => property.id); setComparison((current) => Array.from(new Set([...current, ...top])).slice(0, 4)); setView("comparison"); };
  const copySummary = async () => {
    const best = properties.find((property) => property.id === guidance?.best_match_id) || properties[0];
    const runner = properties.find((property) => property.id === guidance?.runner_up_id) || properties[1];
    const lines = ["Aizen buyer decision summary", confirmedBrief?.original_query || "No active brief", `Outcome: ${guidance?.outcome || "audited results"}`, best ? `Best match: ${best.title} · ${money(best.price)} · ${percent(best.fit_score)} fit · ${percent(best.evidence_coverage)} evidence` : "Best match: none", runner ? `Runner-up: ${runner.title} · ${money(runner.price)} · ${percent(runner.fit_score)} fit · ${percent(runner.evidence_coverage)} evidence` : "Runner-up: none", `Known gaps: ${best ? [...best.conflicting_criteria, ...best.unknown_criteria, ...best.unsupported_criteria].join(", ") || "No known criterion gaps in captured fields" : "No eligible home"}`, `Snapshot: ${best?.dataset_snapshot_at || "unavailable"}`, ...sources.map((source) => `Source: ${source.url}`)];
    try { await navigator.clipboard.writeText(lines.join("\n")); setCopied(true); window.setTimeout(() => setCopied(false), 2000); } catch { setError("The decision summary could not be copied."); }
  };
  const recentSearch = (session: ResearchSession) => { setThreadId(session.threadId); localStorage.setItem("aizen-thread-id", session.threadId); void rerunBrief(session.brief, session.threadId, true); };
  const reset = () => { abortRef.current?.abort(); resetAizenStorage(); setQuery(""); setConfirmedBrief(null); setProperties([]); setShortlist([]); setComparison([]); setNotes({}); setStatuses({}); setSessions([]); setScenario(emptyScenario); setAffordabilityTarget(""); setAnswer(""); setTrace([]); setSources([]); setRelaxations([]); setGuidance(null); setStats(emptyStats); setRunStatus("idle"); setThreadId(crypto.randomUUID()); window.setTimeout(resetAizenStorage, 0); };

  const dossierIds = comparison.length ? comparison : shortlist;
  const dossierProperties = dossierIds.map((id) => properties.find((property) => property.id === id)).filter((property): property is Property => Boolean(property)).slice(0, 4);
  const affordabilityProperties = [...comparison, ...shortlist, ...properties.map((property) => property.id)].map((id, index, ids) => ids.indexOf(id) === index ? properties.find((property) => property.id === id) : undefined).filter((property): property is Property => Boolean(property));
  const visibleProperties = (resultFilter === "shortlisted" ? properties.filter((property) => shortlist.includes(property.id)) : properties).slice(0, shown);
  const workspaceViews: View[] = comparison.length ? ["results", "comparison", "location", "areas", "affordability"] : ["results", "location", "areas", "affordability"];

  return <div className="app-shell">
    <header className="topbar"><BrandMark /><nav aria-label="Primary navigation"><button aria-current={view === "results"} onClick={() => setView("results")}>Homes</button><button aria-current={view === "location"} onClick={() => setView("location")}>Map</button><button aria-current={view === "areas"} onClick={() => setView("areas")}>Areas</button><button aria-current={view === "affordability"} onClick={() => setView("affordability")}>Affordability</button><a href="#/case-study">Case study</a></nav><div className="header-actions"><span>{shortlist.length} shortlisted</span><button type="button" onClick={() => setDossierOpen(true)}>Open buyer dossier</button><button type="button" className="text-button" onClick={reset}>Reset showcase</button></div></header>
    <main>
      <section className="hero"><div className="hero-copy"><p className="eyebrow">Dubai home-buying intelligence · frozen snapshot</p><h1>Decide with evidence.<br /><em>Not listing noise.</em></h1><p>Aizen structures your brief, runs the live agent, then audits every recommendation against captured facts.</p><div className="trust-row"><span><b>8-node</b> agent</span><span><b>Frozen</b> snapshot</span><span><b>Deterministic</b> fit</span></div></div><div className="brief-card"><p className="eyebrow">01 · Shape the search</p><label htmlFor="buyer-query">Describe your ideal Dubai home</label><textarea id="buyer-query" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); void startSearch(); } }} placeholder="Example: Ready 2BR in Dubai Marina under AED 2M, no off-plan" /><button className="button-primary" type="button" disabled={!query.trim() || runStatus === "interpreting" || runStatus === "running"} onClick={() => void startSearch()}>{runStatus === "interpreting" ? "Interpreting…" : runStatus === "running" ? "Live run in progress…" : "Find matching homes"}</button><div className="preset-list"><span>Live demo presets</span>{PRESETS.map((preset, index) => <button type="button" key={preset} onClick={() => setQuery(preset)}><b>0{index + 1}</b>{preset}</button>)}</div>{sessions.length > 0 && <div className="preset-list recent-briefs"><span>Recent searches</span>{sessions.map((session) => <button type="button" key={session.threadId} onClick={() => recentSearch(session)}><b>↺</b><span>{session.title}<small>{new Intl.DateTimeFormat("en-AE", { dateStyle: "medium", timeStyle: "short" }).format(new Date(session.lastActivityAt))}</small></span></button>)}</div>}{recentRerun && <p className="recent-status">Running live again—no saved answer is being replayed.</p>}</div></section>

      {confirmedBrief && <section className="active-brief"><div><p className="eyebrow">Active buyer brief</p><div className="brief-chips">{confirmedBrief.criteria.map((criterion) => <span className={`${criterion.priority} ${!criterion.verifiable ? "unverifiable" : ""}`} key={criterion.id}>{criterion.label}</span>)}</div></div><button ref={briefTriggerRef} type="button" onClick={() => openBriefEditor()}>Edit brief</button></section>}

      <AgentRunSurface status={runStatus} trace={trace} properties={properties} guidance={guidance} stats={stats} brief={confirmedBrief} webAnswer={answer} error={error} copied={copied} onCancel={cancelRun} onRetry={retry} onEdit={() => openBriefEditor()} onSelect={setSelected} onCompare={compareTop} onCopy={() => void copySummary()} />
      {error && runStatus !== "failed" && <div className="error-banner" role="alert">{error}<button type="button" onClick={() => setError("")}>Dismiss</button></div>}

      <section className="workspace"><div className="workspace-tabs" role="navigation" aria-label="Decision workspace">{workspaceViews.map((item) => <button type="button" key={item} aria-current={view === item} onClick={() => setView(item)}>{item === "results" ? "Ranked homes" : item}</button>)}</div>
        {view === "results" && <><div className="section-heading"><div><p className="eyebrow">Audited homes</p><h2>{properties.length ? `${properties.length} evidence-ranked homes` : "Your ranked homes will appear here"}</h2></div><p>Fit is deterministic. Unknown facts stay visible. Snapshot {properties[0]?.dataset_snapshot_at || "awaiting a live run"}.</p></div>{properties.length > 0 && <div className="result-filter" role="group" aria-label="Filter homes"><button type="button" aria-pressed={resultFilter === "all"} onClick={() => setResultFilter("all")}>All matches</button><button type="button" aria-pressed={resultFilter === "shortlisted"} onClick={() => setResultFilter("shortlisted")}>Shortlisted ({shortlist.length})</button></div>}<div className="property-grid">{visibleProperties.map((property, index) => <article className="property-card" aria-label={property.title} key={property.id}><div className="architecture-visual" aria-hidden="true"><span>{String(index + 1).padStart(2, "0")}</span><i /><i /><i /></div><div className="card-body"><div className="card-meta"><span className={`suitability ${property.suitability}`}>{property.suitability}</span><span>{percent(property.fit_score)} fit</span><span>{percent(property.evidence_coverage)} evidence</span></div><h3>{property.title}</h3><p>{property.area} · {property.beds ?? "?"} bed · {property.completion_status || "completion unknown"}</p><strong>{money(property.price)}</strong><ul>{property.matched_criteria.slice(0, 2).map((item) => <li key={item}>✓ {item}</li>)}{property.unknown_criteria.slice(0, 1).map((item) => <li className="unknown" key={item}>? {item}</li>)}</ul><div className="card-actions"><button type="button" onClick={() => setSelected(property)}>Review evidence</button><button type="button" aria-label={`${shortlist.includes(property.id) ? "Remove" : "Add"} ${property.title} ${shortlist.includes(property.id) ? "from" : "to"} shortlist`} aria-pressed={shortlist.includes(property.id)} onClick={() => toggle(setShortlist, property.id)}>◇</button></div></div></article>)}</div>{resultFilter === "shortlisted" && !visibleProperties.length && <div className="empty-filter"><h3>No shortlisted homes yet.</h3><p>Review a property’s evidence and save it when it deserves another look.</p><button type="button" onClick={() => setResultFilter("all")}>Return to all matches</button></div>}{resultFilter === "all" && shown < properties.length && <button className="view-more" type="button" onClick={() => setShown(properties.length)}>View {properties.length - shown} more homes</button>}{runStatus === "completed" && confirmedBrief?.mode === "property_search" && !properties.length && <div className="no-results"><h3>No snapshot match met every structured hard rule.</h3><p>Aizen did not silently relax your brief. Review a possible change before running again.</p>{relaxations.map((item) => <div key={item.criterion_id}><span>Review removing {confirmedBrief.criteria.find((criterion) => criterion.id === item.criterion_id)?.label}</span><b>{item.resulting_match_count} resulting matches</b><button type="button" onClick={() => openBriefEditor(item.criterion_id)}>Review this change</button></div>)}</div>}{sources.length > 0 && <details className="sources"><summary>Captured sources ({sources.length})</summary><ol>{sources.map((source, index) => <li key={`${source.url}-${index}`}><a href={source.url} target="_blank" rel="noreferrer">[{index + 1}] {source.title}</a><span>Observed {source.observed_at || "date unavailable"}</span></li>)}</ol></details>}</>}
        {view === "comparison" && <ComparisonView properties={properties} selectedIds={comparison} statuses={statuses} scenario={scenario} onSelect={setSelected} onRemove={(id) => toggle(setComparison, id)} onDossier={() => setDossierOpen(true)} />}
        {view === "location" && <Suspense fallback={<div className="loading-panel">Loading the zero-cost map surface…</div>}><LocationView properties={properties} selectedId={selected?.id} onSelect={setSelected} /></Suspense>}
        {view === "areas" && <AreaComparison />}
        {view === "affordability" && <Affordability properties={affordabilityProperties} selectedId={affordabilityTarget} form={scenario} onSelect={setAffordabilityTarget} onChange={setScenario} />}
      </section>
    </main>
    {comparison.length > 0 && <aside className="comparison-tray dark-surface"><div><p className="eyebrow">Decision tray</p><b>{comparison.length} of 4 homes selected</b></div>{properties.filter((property) => comparison.includes(property.id)).map((property) => <span className="tray-property" key={property.id}><button type="button" onClick={() => setSelected(property)}>{property.title}<small>{money(property.price)}</small></button><button type="button" aria-label={`Remove ${property.title} from comparison`} onClick={() => toggle(setComparison, property.id)}>×</button></span>)}<button type="button" onClick={() => setView("comparison")}>Compare selected</button><button type="button" onClick={() => setDossierOpen(true)}>Build dossier ↗</button></aside>}
    {selected && <EvidenceDrawer property={selected} shortlisted={shortlist.includes(selected.id)} compared={comparison.includes(selected.id)} note={notes[selected.id] || ""} status={statuses[selected.id]} onClose={() => setSelected(null)} onShortlist={() => toggle(setShortlist, selected.id)} onCompare={() => toggle(setComparison, selected.id, 4)} onNote={(note) => setNotes((current) => ({ ...current, [selected.id]: note }))} onStatus={(status) => setStatuses((current) => ({ ...current, [selected.id]: status }))} />}
    {briefEditorOpen && confirmedBrief && <BriefEditorDrawer brief={confirmedBrief} highlightedId={highlightedCriterionId} onClose={closeBriefEditor} onApply={applyBrief} />}
    {dossierOpen && <Dossier brief={confirmedBrief} properties={dossierProperties} notes={notes} form={scenario} onClose={() => setDossierOpen(false)} />}
  </div>;
}
