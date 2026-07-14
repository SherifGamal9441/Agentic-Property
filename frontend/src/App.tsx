import { FormEvent, useEffect, useMemo, useState } from "react";

export type Property = {
  id: string;
  title: string;
  area: string;
  price: number | null;
  currency: string;
  beds: number | null;
  baths: number | null;
  property_type: string | null;
  size_sqft: number | null;
  furnishing: string | null;
  completion_status: string | null;
  parking_spaces: number | null;
  year_of_completion: number | null;
  latitude: number | null;
  longitude: number | null;
  location_status: "exact" | "unavailable";
  source_url?: string | null;
  source_name?: string | null;
  observed_at?: string | null;
  dataset_snapshot_at?: string | null;
  data_status: "active_dataset_listing" | "historical_insight" | "web_research";
  fit_score: number | null;
  score_factors: string[];
  matched_criteria: string[];
  unmatched_criteria: string[];
  price_assessment: string | null;
  data_intent: "recommend" | "insights_only";
  data_source: string;
};

type TraceStep = { node: string; label: string; status: "active" | "complete" };
type Criteria = { mustHave: string; niceToHave: string; dealBreaker: string };
type SavedSearch = { id: string; query: string; snapshot: string | null; resultIds: string[]; criteria?: Criteria; shortlistIds?: string[] };
type MarketContext = { area: string; record_count?: number; period_start?: string | null; period_end?: string | null; price_min?: number | null; price_max?: number | null; price_per_sqft_min?: number | null; price_per_sqft_max?: number | null; unavailable?: boolean };
type MapScope = "all" | "shortlist" | "comparison";
type SortBy = "fit" | "price-low" | "price-per-sqft";

const API_URL = import.meta.env.VITE_AGENT_API_URL || "http://localhost:8002";
const emptyValue = "Not reported";
const guidedBriefs = ["A ready 2BR in Dubai Marina under AED 2M", "Compare off-plan investment options", "A family home with room to grow"];

const price = (amount: number | null, currency = "AED") =>
  amount === null ? emptyValue : new Intl.NumberFormat("en-AE", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);

const value = (item: string | number | null | undefined) => item ?? emptyValue;
const pricePerSqft = (property: Property) => property.price !== null && property.size_sqft ? price(property.price / property.size_sqft, property.currency) : emptyValue;
const validCoordinates = (property: Property) => property.location_status === "exact" && Number.isFinite(property.latitude) && Number.isFinite(property.longitude);

function savedSearchesFromStorage() {
  try {
    const saved = JSON.parse(localStorage.getItem("aizen-saved-searches") || "[]");
    return Array.isArray(saved) ? saved as SavedSearch[] : [];
  } catch {
    return [];
  }
}

function idsFromStorage(key: string) {
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "[]");
    return Array.isArray(saved) ? saved.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function LocationView({ properties, selectedId, shortlistIds, compareIds, onSelect }: {
  properties: Property[];
  selectedId?: string;
  shortlistIds: string[];
  compareIds: string[];
  onSelect: (property: Property) => void;
}) {
  const [scope, setScope] = useState<MapScope>("all");
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);
  const scopedProperties = scope === "all" ? properties : properties.filter((property) => (scope === "shortlist" ? shortlistIds : compareIds).includes(property.id));
  const mapped = scopedProperties.filter(validCoordinates);
  const bounds = useMemo(() => {
    if (!mapped.length) return null;
    const lats = mapped.map(({ latitude }) => latitude as number);
    const lngs = mapped.map(({ longitude }) => longitude as number);
    return { minLat: Math.min(...lats), maxLat: Math.max(...lats), minLng: Math.min(...lngs), maxLng: Math.max(...lngs) };
  }, [mapped]);
  const groups = useMemo(() => {
    // ponytail: group only exact supplied coordinates; add proximity grouping when coordinate precision exists.
    const grouped = new Map<string, Property[]>();
    mapped.forEach((property) => {
      const key = `${property.latitude},${property.longitude}`;
      grouped.set(key, [...(grouped.get(key) || []), property]);
    });
    return [...grouped.entries()].map(([key, homes]) => ({ key, homes }));
  }, [mapped]);
  const missing = scopedProperties.filter((property) => !validCoordinates(property));
  const selectedGroup = groups.find((group) => group.key === expandedGroup);
  const areas = [...new Set(mapped.map((property) => property.area))];
  const scopeLabel = scope === "all" ? "results" : scope;

  const changeScope = (nextScope: MapScope) => {
    setScope(nextScope);
    setExpandedGroup(null);
  };

  return <section className="map-rail">
    <div className="map-header"><div><p className="section-label">Location evidence</p><h3>Relative location view</h3></div><span>{mapped.length} pins</span></div>
    <div className="map-scopes" aria-label="Map location scope">
      <button type="button" aria-pressed={scope === "all"} aria-label="Show all result locations" onClick={() => changeScope("all")}>All</button>
      <button type="button" aria-pressed={scope === "shortlist"} aria-label="Show shortlist locations" onClick={() => changeScope("shortlist")}>Shortlist</button>
      <button type="button" aria-pressed={scope === "comparison"} aria-label="Show comparison locations" onClick={() => changeScope("comparison")}>Compare</button>
    </div>
    <div className="map" aria-label="Property location view">
      <div className="map-water" />
      {areas.map((area, index) => <span className="map-label" key={area} style={{ left: `${18 + index * 32}%`, top: `${18 + index * 18}%` }}>{area}</span>)}
      {groups.map((group, index) => {
        const property = group.homes[0];
        const latitude = property.latitude as number;
        const longitude = property.longitude as number;
        const latRange = Math.max((bounds?.maxLat ?? latitude) - (bounds?.minLat ?? latitude), 0.002);
        const lngRange = Math.max((bounds?.maxLng ?? longitude) - (bounds?.minLng ?? longitude), 0.002);
        const left = 14 + ((longitude - (bounds?.minLng ?? longitude)) / lngRange) * 72 + (index % 2) * 1.5;
        const top = 78 - ((latitude - (bounds?.minLat ?? latitude)) / latRange) * 58 + (index % 2) * 1.5;
        const isSelected = group.homes.some((home) => home.id === selectedId);
        const isShortlisted = group.homes.some((home) => shortlistIds.includes(home.id));
        const isComparing = group.homes.some((home) => compareIds.includes(home.id));
        const label = group.homes.length === 1 ? `Open ${property.title}` : `Open ${group.homes.length} homes in ${property.area}`;
        return <button type="button" className={`map-pin ${isSelected ? "selected" : ""} ${isShortlisted ? "shortlisted" : ""} ${isComparing ? "comparing" : ""}`} key={group.key} onClick={() => group.homes.length === 1 ? onSelect(property) : setExpandedGroup(group.key)} style={{ left: `${left}%`, top: `${top}%` }} aria-label={label}><span>{group.homes.length === 1 ? property.title : `${group.homes.length} homes`}</span></button>;
      })}
      <div className="map-attribution">Relative positions from supplied listing coordinates</div>
    </div>
    {selectedGroup && <section className="map-cluster" aria-label="Location group"><p>Choose a home at this location</p>{selectedGroup.homes.map((property) => <button type="button" key={property.id} onClick={() => { onSelect(property); setExpandedGroup(null); }}>Open {property.title}</button>)}</section>}
    {!mapped.length && <p className="map-note">No exact {scopeLabel} locations are available.</p>}
    {missing.map((property) => <p className="map-note" key={property.id}>{property.title} has area-only location evidence.</p>)}
  </section>;
}

function DecisionSheet({ properties, onClose }: { properties: Property[]; onClose: () => void }) {
  const [costs, setCosts] = useState({ transfer: "", finance: "", service: "", moving: "" });
  const enteredCosts = Object.values(costs).reduce((total, item) => total + (Number(item) || 0), 0);
  return <div className="drawer-backdrop" onClick={onClose}>
    <section className="intelligence-drawer decision-sheet" role="dialog" aria-label="Buyer decision sheet" onClick={(event) => event.stopPropagation()}>
      <button type="button" className="close" onClick={onClose} aria-label="Close buyer decision sheet">×</button>
      <p className="section-label">Buyer decision sheet</p><h2>{properties.length} selected home{properties.length === 1 ? "" : "s"}</h2>
      <div className="decision-grid">{properties.map((property) => <article key={property.id}><h3>{property.title}</h3><p>{price(property.price, property.currency)} · {value(property.size_sqft)} sq ft</p><p>{property.score_factors.join(" · ") || "No reported match factors"}</p><p>{property.unmatched_criteria.join(" · ") || "No reported gaps"}</p><p>{property.source_name || emptyValue} · {property.dataset_snapshot_at || "Snapshot date unavailable"}</p></article>)}</div>
      <section><h3>Historical comparable evidence</h3><p>Use historical transactions as market context only. They are not active listings.</p></section>
      <section><h3>Total ownership cost assumptions</h3><p>Property prices shown above. No fee is assumed: add only the costs you have confirmed.</p><div className="ownership-costs">{([['transfer', 'Transfer cost'], ['finance', 'Finance cost'], ['service', 'Annual service charge'], ['moving', 'Moving cost']] as const).map(([key, label]) => <label key={key}>{label}<input aria-label={label} type="number" min="0" inputMode="numeric" value={costs[key]} onChange={(event) => setCosts((current) => ({ ...current, [key]: event.target.value }))} /></label>)}</div><p className="entered-costs">Entered costs: {price(enteredCosts, "AED")}</p></section>
      <button type="button" className="dark-button" onClick={() => window.print()}>Print decision sheet</button>
    </section>
  </div>;
}

function App({ initialProperties = [] }: { initialProperties?: Property[] }) {
  const [query, setQuery] = useState("");
  const [properties, setProperties] = useState<Property[]>(initialProperties);
  const [answer, setAnswer] = useState("");
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [selected, setSelected] = useState<Property | null>(null);
  const [shortlistIds, setShortlistIds] = useState<string[]>(() => idsFromStorage("aizen-shortlist"));
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [notice, setNotice] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [mustHave, setMustHave] = useState("");
  const [niceToHave, setNiceToHave] = useState("");
  const [dealBreaker, setDealBreaker] = useState("");
  const [marketContext, setMarketContext] = useState<MarketContext | null>(null);
  const [showDecisionSheet, setShowDecisionSheet] = useState(false);
  const [sortBy, setSortBy] = useState<SortBy>("fit");
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(savedSearchesFromStorage);

  useEffect(() => localStorage.setItem("aizen-saved-searches", JSON.stringify(savedSearches)), [savedSearches]);
  useEffect(() => localStorage.setItem("aizen-shortlist", JSON.stringify(shortlistIds)), [shortlistIds]);
  useEffect(() => {
    if (!selected && !showDecisionSheet) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setSelected(null); setShowDecisionSheet(false); }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selected, showDecisionSheet]);

  const snapshot = properties[0]?.dataset_snapshot_at || null;
  const criteria: Criteria = { mustHave, niceToHave, dealBreaker };
  const profile = [["Must-have", mustHave], ["Nice-to-have", niceToHave], ["Deal-breaker", dealBreaker]].filter(([, item]) => item) as [string, string][];
  const comparison = properties.filter((property) => compareIds.includes(property.id));
  const shortlist = properties.filter((property) => shortlistIds.includes(property.id));
  const changedSavedSearch = snapshot === null ? undefined : savedSearches.find((item) => item.snapshot !== null && item.snapshot !== snapshot);
  const savedChanges = changedSavedSearch ? {
    added: properties.filter((property) => !changedSavedSearch.resultIds.includes(property.id)).length,
    removed: changedSavedSearch.resultIds.filter((id) => !properties.some((property) => property.id === id)).length,
    unchanged: properties.filter((property) => changedSavedSearch.resultIds.includes(property.id)).length,
  } : null;
  const visibleProperties = useMemo(() => [...properties].sort((left, right) => {
    const leftValue = sortBy === "fit" ? left.fit_score : sortBy === "price-low" ? left.price : left.price !== null && left.size_sqft ? left.price / left.size_sqft : null;
    const rightValue = sortBy === "fit" ? right.fit_score : sortBy === "price-low" ? right.price : right.price !== null && right.size_sqft ? right.price / right.size_sqft : null;
    if (leftValue === null) return 1;
    if (rightValue === null) return -1;
    return sortBy === "fit" ? rightValue - leftValue : leftValue - rightValue;
  }), [properties, sortBy]);

  const toggleShortlist = (id: string) => {
    const exists = shortlistIds.includes(id);
    setShortlistIds(exists ? shortlistIds.filter((item) => item !== id) : [...shortlistIds, id]);
    setNotice(exists ? "Removed from shortlist." : "Added to shortlist.");
  };

  const toggleCompare = (id: string) => {
    if (compareIds.includes(id)) {
      setCompareIds(compareIds.filter((item) => item !== id));
      setNotice("Removed from comparison.");
      return;
    }
    if (compareIds.length === 4) {
      setNotice("Compare up to four homes at a time.");
      return;
    }
    setCompareIds([...compareIds, id]);
    setNotice("Added to comparison.");
  };

  const saveSearch = () => {
    if (!query.trim()) {
      setNotice("Add a property brief before saving a search.");
      return;
    }
    const existing = savedSearches.find((item) => item.query === query);
    const saved: SavedSearch = { id: existing?.id || crypto.randomUUID(), query, snapshot, resultIds: properties.map(({ id }) => id), criteria, shortlistIds };
    setSavedSearches([saved, ...savedSearches.filter((item) => item.query !== query)]);
    setNotice("Search saved in this browser.");
  };

  const restoreSavedSearch = () => {
    const saved = savedSearches[0];
    if (!saved) return;
    setQuery(saved.query);
    setMustHave(saved.criteria?.mustHave || "");
    setNiceToHave(saved.criteria?.niceToHave || "");
    setDealBreaker(saved.criteria?.dealBreaker || "");
    setShortlistIds(saved.shortlistIds || []);
    setNotice("Saved brief restored.");
  };

  const clearBrief = () => {
    setQuery(""); setMustHave(""); setNiceToHave(""); setDealBreaker(""); setProperties([]); setAnswer(""); setTrace([]); setSelected(null); setCompareIds([]); setShortlistIds([]); setNotice("Research brief and selections cleared.");
  };

  const startNewConversation = () => {
    localStorage.removeItem("aizen-thread-id");
    clearBrief();
    setNotice("New conversation started.");
  };

  const recordFeedback = (property: Property, kind: "useful" | "issue") => {
    // ponytail: browser-local feedback; persist after identity and retention policy exist.
    const feedback = JSON.parse(localStorage.getItem("aizen-feedback") || "[]");
    localStorage.setItem("aizen-feedback", JSON.stringify([...feedback, { propertyId: property.id, kind, at: new Date().toISOString() }]));
    setNotice("Feedback saved in this browser.");
  };

  const loadMarketContext = async (area: string) => {
    setMarketContext(null);
    try {
      const response = await fetch(`${API_URL}/api/market-context?${new URLSearchParams({ area })}`);
      setMarketContext(await response.json());
    } catch {
      setMarketContext({ area, unavailable: true });
    }
  };

  async function runAgent(event: FormEvent) {
    event.preventDefault();
    if (!query.trim() || isRunning) return;
    const threadId = localStorage.getItem("aizen-thread-id") || crypto.randomUUID();
    localStorage.setItem("aizen-thread-id", threadId);
    setIsRunning(true); setNotice(""); setAnswer(""); setProperties([]); setCompareIds([]); setTrace([]); setSelected(null);
    try {
      const decisionBrief = [query, ...profile.map(([label, item]) => `${label}: ${item}`)].join("\n");
      const response = await fetch(`${API_URL}/api/runs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: decisionBrief, thread_id: threadId }) });
      if (!response.ok || !response.body) throw new Error("Property research is temporarily unavailable. Please try again.");
      const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
      while (true) {
        const { done, value: chunk } = await reader.read(); if (done) break;
        buffer += decoder.decode(chunk, { stream: true }); const events = buffer.split("\n\n"); buffer = events.pop() || "";
        events.forEach((raw) => {
          const type = raw.match(/^event: (.+)$/m)?.[1]; const line = raw.match(/^data: (.+)$/m)?.[1]; if (!type || !line) return;
          const data = JSON.parse(line);
          if (type === "agent_step") setTrace((current) => [...current.filter((item) => item.node !== data.node), { node: data.node, label: data.label, status: data.status }]);
          if (type === "properties") setProperties(data.properties || []);
          if (type === "answer_token") setAnswer((current) => current + data.token);
          if (type === "run_failed") setNotice(data.message || "Property research is temporarily unavailable. Please try again.");
        });
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Property research is temporarily unavailable. Please try again.");
    } finally { setIsRunning(false); }
  }

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#top" aria-label="Aizen home"><span>AI</span>ZEN</a><nav><a href="#workspace">Workspace</a><a href="#how-it-works">How it works</a><button type="button" onClick={startNewConversation}>New conversation</button></nav></header>
    <main id="top">
      <section className="hero"><div><p className="eyebrow">Dubai property intelligence</p><h1>Find a home.<br /><em>Know why it fits.</em></h1><p className="hero-copy">Aizen turns a property brief into an inspectable decision: active dataset research, ranked homes, and trade-offs you can see.</p><a className="primary-link" href="#workspace">Start a property brief <span>↓</span></a></div><div className="hero-card"><p>Data promise</p><strong>Active<span> dataset</span></strong><div className="confidence-bar"><span /></div></div></section>
      <section className="proof-strip" id="how-it-works" aria-label="How Aizen works"><p><b>01</b> Understand your brief</p><p><b>02</b> Search active data</p><p><b>03</b> Compare and audit</p><p><b>04</b> Make a decision with confidence</p></section>
      <section className={`workspace ${properties.length ? "has-results" : ""}`} id="workspace" aria-label="Aizen property workspace">
        <aside className="brief-rail"><p className="section-label">Guided starts</p><h2>What are you looking for?</h2>{guidedBriefs.map((brief) => <button type="button" key={brief} onClick={() => setQuery(brief)}>{brief}<span>↗</span></button>)}<p className="rail-note"><span className="pulse" />Research with source, snapshot, and decision evidence.</p></aside>
        <section className="agent-canvas">
          <div className="canvas-header"><div><p className="section-label">Your property brief</p><h2>Tell Aizen what matters</h2></div><span className="source-badge">{snapshot ? `Snapshot ${snapshot}` : "Active dataset research"}</span></div>
          <form className="query-box" onSubmit={runAgent}><textarea value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Property brief" rows={2} placeholder="A ready 2BR in Dubai Marina under AED 2M" /><button type="submit" disabled={isRunning}>{isRunning ? "Researching…" : "Research properties"}</button></form>
          <div className="decision-profile"><label>Must-have criteria<input aria-label="Must-have criteria" value={mustHave} onChange={(event) => setMustHave(event.target.value)} placeholder="Waterfront, ready to move" /></label><label>Nice-to-have criteria<input aria-label="Nice-to-have criteria" value={niceToHave} onChange={(event) => setNiceToHave(event.target.value)} placeholder="Sea view, high floor" /></label><label>Deal-breaker<input aria-label="Deal-breaker" value={dealBreaker} onChange={(event) => setDealBreaker(event.target.value)} placeholder="No off-plan" /></label>{profile.map(([label, item]) => <p key={label}>{label}: {item}</p>)}</div>
          <div className="research-actions"><button type="button" onClick={saveSearch}>Save this search</button>{savedSearches.length > 0 && <button type="button" onClick={restoreSavedSearch}>Restore saved brief</button>}<button type="button" onClick={clearBrief}>Clear research brief</button>{shortlistIds.length > 0 && <button type="button" onClick={() => { setShortlistIds([]); setNotice("Shortlist cleared."); }}>Clear shortlist</button>}{compareIds.length > 0 && <button type="button" onClick={() => { setCompareIds([]); setNotice("Comparison cleared."); }}>Clear comparison</button>}</div>
          {(notice || savedChanges) && <p className="notice" role="status">{notice || `Saved research changed: ${savedChanges?.added} added, ${savedChanges?.removed} no longer matching, ${savedChanges?.unchanged} unchanged.`}</p>}
          {trace.length > 0 && <div className="trace" aria-label="Agent activity">{trace.map((step) => <div className={`trace-step ${step.status}`} key={step.node}>{step.label}</div>)}</div>}
          {answer && <div className="answer"><span>A</span><p>{answer}</p></div>}
          {isRunning ? <section className="empty-state researching"><p className="section-label">Research in progress</p><h3>Building your decision view</h3><p>Matching active records to your brief and criteria.</p></section> : !properties.length ? <section className="empty-state"><p className="section-label">Buyer workspace</p><h3>Start with a property brief</h3><p>Describe the home you want. Aizen will return source, snapshot, criteria, and known trade-offs.</p></section> : <section className="property-results" aria-label="Property results"><div className="results-heading"><div><p className="section-label">Property evidence</p><h3>{properties.length} homes returned</h3></div><label>Sort<select aria-label="Sort properties" value={sortBy} onChange={(event) => setSortBy(event.target.value as SortBy)}><option value="fit">Best evidence match</option><option value="price-low">Price: low to high</option><option value="price-per-sqft">Price / sq ft: low to high</option></select></label></div><div className="property-grid">{visibleProperties.map((property) => {
            const isShortlisted = shortlistIds.includes(property.id); const isComparing = compareIds.includes(property.id);
            return <article className={`property-card ${isShortlisted ? "shortlisted" : ""} ${isComparing ? "comparing" : ""}`} key={property.id}><button type="button" className="property-visual" onClick={() => setSelected(property)} aria-label={`Open ${property.title}`}><b>{property.fit_score === null ? "Match evidence pending" : `${Math.round(property.fit_score * 100)}% evidence match`}</b></button><div className="property-content"><button type="button" className="property-title" onClick={() => setSelected(property)}>{property.title}</button><p>{property.area} · {property.data_status === "historical_insight" ? "Historical market signal" : "Active dataset record"}</p><strong>{price(property.price, property.currency)}</strong><div className="property-specs"><span>{value(property.beds)} bed</span><span>{value(property.baths)} bath</span><span>{value(property.size_sqft)} sq ft</span></div><p className="evidence">{property.score_factors.join(" · ") || "No reported match factors"}</p><p className="evidence">{property.unmatched_criteria.join(" · ") || "No reported gaps"}</p><p className="evidence">{property.source_name || emptyValue} · {property.dataset_snapshot_at || "Snapshot unavailable"}</p><div className="property-actions"><button type="button" aria-pressed={isShortlisted} onClick={() => toggleShortlist(property.id)}>{isShortlisted ? "Remove from shortlist" : "Add to shortlist"}</button><button type="button" aria-pressed={isComparing} onClick={() => toggleCompare(property.id)}>{isComparing ? "Remove from comparison" : "Add to comparison"}</button>{property.source_url && <a href={property.source_url} target="_blank" rel="noreferrer">Source ↗</a>}</div></div></article>;
          })}</div></section>}
        </section>
        <LocationView properties={properties} selectedId={selected?.id} shortlistIds={shortlistIds} compareIds={compareIds} onSelect={setSelected} />
      </section>
      <section className="compare-tray" role="region" aria-label="Comparison shortlist"><div><p className="section-label">Decision tray</p><h2>Compare your shortlist</h2><p>{shortlist.length} saved home{shortlist.length === 1 ? "" : "s"} · select one to four homes for side-by-side evidence.</p></div><div className="compare-slots">{comparison.map((property) => <button type="button" key={property.id} onClick={() => setSelected(property)}><span>{property.fit_score === null ? "Evidence pending" : `${Math.round(property.fit_score * 100)}% match`}</span>{property.title}<b>↗</b></button>)}{Array.from({ length: Math.max(0, 4 - comparison.length) }, (_, index) => <div className="empty-slot" key={index}>Add a home</div>)}</div>{comparison.length > 0 && <button type="button" className="dark-button" onClick={() => setShowDecisionSheet(true)}>View decision sheet</button>}</section>
    </main>
    {selected && <div className="drawer-backdrop" onClick={() => setSelected(null)}><aside className="intelligence-drawer" role="complementary" aria-label="Property intelligence" onClick={(event) => event.stopPropagation()}><button type="button" className="close" onClick={() => setSelected(null)} aria-label="Close property intelligence">×</button><p className="section-label">Property evidence</p><h2>{selected.title}</h2><p>{selected.area} · {selected.data_status === "historical_insight" ? "Historical market signal" : "Active dataset record"}</p><strong className="drawer-price">{price(selected.price, selected.currency)}</strong><div className="drawer-actions"><button type="button" aria-pressed={shortlistIds.includes(selected.id)} onClick={() => toggleShortlist(selected.id)}>{shortlistIds.includes(selected.id) ? "Remove from shortlist" : "Add to shortlist"}</button><button type="button" className="dark-button" aria-pressed={compareIds.includes(selected.id)} onClick={() => toggleCompare(selected.id)}>{compareIds.includes(selected.id) ? "Remove from comparison" : "Add to comparison"}</button></div><section><h3>Why it was selected</h3><ul>{selected.score_factors.map((factor) => <li key={factor}>✓ {factor}</li>)}{selected.unmatched_criteria.map((gap) => <li className="gap" key={gap}>△ {gap}</li>)}</ul></section><section className="spec-grid"><h3>Reported details</h3><div><span>Bedrooms</span><b>{value(selected.beds)}</b></div><div><span>Bathrooms</span><b>{value(selected.baths)}</b></div><div><span>Size</span><b>{value(selected.size_sqft)}</b></div><div><span>Price / sq ft</span><b>{pricePerSqft(selected)}</b></div><div><span>Location evidence</span><b>{validCoordinates(selected) ? "Exact supplied coordinate" : selected.area ? "Area-only" : "Unavailable"}</b></div><div><span>Snapshot</span><b>{selected.dataset_snapshot_at || emptyValue}</b></div></section><section><h3>Historical area context</h3><button type="button" onClick={() => void loadMarketContext(selected.area)}>Load historical context</button>{marketContext && (marketContext.unavailable || !marketContext.record_count ? <p>Insufficient historical evidence for this area.</p> : <p>{marketContext.record_count} reported records · {marketContext.period_start} to {marketContext.period_end} · {price(marketContext.price_min ?? null)}–{price(marketContext.price_max ?? null)}</p>)}</section><section><h3>Research feedback</h3><button type="button" onClick={() => recordFeedback(selected, "useful")}>Useful result</button><button type="button" onClick={() => recordFeedback(selected, "issue")}>Missing or incorrect detail</button></section></aside></div>}
    {showDecisionSheet && <DecisionSheet properties={comparison} onClose={() => setShowDecisionSheet(false)} />}
  </div>;
}

export default App;
