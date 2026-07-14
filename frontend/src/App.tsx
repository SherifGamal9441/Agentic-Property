import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type Mode = "demo" | "live";

export type Property = {
  id: string;
  title: string;
  area: string;
  price: number;
  currency: string;
  beds: number;
  baths: number;
  property_type: string;
  size_sqft: number;
  furnishing: string;
  completion_status: string;
  parking_spaces: number;
  year_of_completion: number;
  latitude: number;
  longitude: number;
  source_url?: string;
  fit_score: number;
  matched_criteria: string[];
  unmatched_criteria: string[];
  price_assessment: string;
  data_intent: "recommend" | "insights_only";
  data_source: string;
  visual_key: string;
};

type TraceStep = {
  node: string;
  label: string;
  status: "complete" | "active" | "waiting";
};

export const demoProperties: Property[] = [
  {
    id: "demo-marina-vista",
    title: "Marina Vista Residence",
    area: "Dubai Marina",
    price: 1_850_000,
    currency: "AED",
    beds: 2,
    baths: 2,
    property_type: "Apartment",
    size_sqft: 1108,
    furnishing: "Furnished",
    completion_status: "completed",
    parking_spaces: 1,
    year_of_completion: 2022,
    latitude: 25.0806,
    longitude: 55.1396,
    source_url: "https://dubailand.gov.ae/",
    fit_score: 0.94,
    matched_criteria: ["Dubai Marina", "2 bedrooms", "within target budget"],
    unmatched_criteria: [],
    price_assessment: "fair",
    data_intent: "recommend",
    data_source: "active",
    visual_key: "marina",
  },
  {
    id: "demo-cove",
    title: "Harbour Cove Apartment",
    area: "Dubai Marina",
    price: 2_040_000,
    currency: "AED",
    beds: 2,
    baths: 3,
    property_type: "Apartment",
    size_sqft: 1244,
    furnishing: "Unfurnished",
    completion_status: "under-construction",
    parking_spaces: 2,
    year_of_completion: 2027,
    latitude: 25.0779,
    longitude: 55.1375,
    source_url: "https://dubailand.gov.ae/",
    fit_score: 0.79,
    matched_criteria: ["Dubai Marina", "2 bedrooms", "extra parking"],
    unmatched_criteria: ["ready to move"],
    price_assessment: "fair",
    data_intent: "recommend",
    data_source: "active",
    visual_key: "city",
  },
];

const initialTrace: TraceStep[] = [
  { node: "memory", label: "Reviewing your brief", status: "complete" },
  { node: "query_understanding", label: "Understanding your criteria", status: "complete" },
  { node: "query_routing", label: "Searching active listings", status: "complete" },
  { node: "comparison_engine", label: "Ranking best matches", status: "complete" },
  { node: "reflection", label: "Reviewing recommendation quality", status: "complete" },
];

const quickStarts = [
  "A ready 2BR in Dubai Marina under AED 2M",
  "Compare off-plan investment options in Dubai",
  "What is happening in Dubai Marina right now?",
];

const formatPrice = (price: number, currency = "AED") =>
  new Intl.NumberFormat("en-AE", { style: "currency", currency, maximumFractionDigits: 0 }).format(price);

const score = (fit: number) => `${Math.round(fit * 100)}% match`;

function PropertyMap({ properties, selectedId, onSelect }: {
  properties: Property[];
  selectedId?: string;
  onSelect: (property: Property, trigger: HTMLButtonElement) => void;
}) {
  const bounds = useMemo(() => {
    const latitudes = properties.map((property) => property.latitude);
    const longitudes = properties.map((property) => property.longitude);
    return {
      minLat: Math.min(...latitudes) - 0.002,
      maxLat: Math.max(...latitudes) + 0.002,
      minLng: Math.min(...longitudes) - 0.002,
      maxLng: Math.max(...longitudes) + 0.002,
    };
  }, [properties]);

  return (
    <div className="map" aria-label="Dubai property map">
      <div className="map-water" />
      <span className="map-label marina-label">Dubai Marina</span>
      <span className="map-label palm-label">Palm Jumeirah</span>
      <span className="map-label downtown-label">Downtown</span>
      {properties.map((property) => {
        const left = ((property.longitude - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * 72 + 12;
        const top = 82 - ((property.latitude - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * 62;
        return (
          <button
            className={`map-pin ${property.id === selectedId ? "selected" : ""}`}
            key={property.id}
            onClick={(event) => onSelect(property, event.currentTarget)}
            style={{ left: `${left}%`, top: `${top}%` }}
            aria-label={`Open ${property.title}`}
          >
            <span>{formatPrice(property.price).replace("AED", "")}</span>
          </button>
        );
      })}
      <div className="map-attribution">Property locations from listing data</div>
    </div>
  );
}

type AppProps = {
  initialProperties?: Property[];
};

function App({ initialProperties = demoProperties }: AppProps) {
  const [mode, setMode] = useState<Mode>(() => (localStorage.getItem("aizen-mode") as Mode) || "demo");
  const [query, setQuery] = useState(quickStarts[0]);
  const [properties, setProperties] = useState<Property[]>(initialProperties);
  const [selected, setSelected] = useState<Property | null>(null);
  const [shortlist, setShortlist] = useState<string[]>(() => JSON.parse(localStorage.getItem("aizen-shortlist") || "[]"));
  const [compare, setCompare] = useState<string[]>(() => JSON.parse(localStorage.getItem("aizen-compare") || "[]"));
  const [trace, setTrace] = useState<TraceStep[]>(initialTrace);
  const [answer, setAnswer] = useState("Marina Vista Residence is your strongest match: ready to view, two bedrooms, and inside your AED 2M brief.");
  const [isRunning, setIsRunning] = useState(false);
  const [notice, setNotice] = useState("");
  const propertyTriggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => localStorage.setItem("aizen-mode", mode), [mode]);
  useEffect(() => localStorage.setItem("aizen-shortlist", JSON.stringify(shortlist)), [shortlist]);
  useEffect(() => localStorage.setItem("aizen-compare", JSON.stringify(compare)), [compare]);

  const chooseProperty = (property: Property, trigger?: HTMLElement) => {
    propertyTriggerRef.current = trigger || propertyTriggerRef.current;
    setSelected(property);
  };
  const closeDrawer = () => {
    setSelected(null);
    window.setTimeout(() => propertyTriggerRef.current?.focus(), 0);
  };

  useEffect(() => {
    if (!selected) return;
    const dismissOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeDrawer();
    };
    window.addEventListener("keydown", dismissOnEscape);
    return () => window.removeEventListener("keydown", dismissOnEscape);
  }, [selected]);
  const toggleShortlist = (id: string) => setShortlist((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  const toggleCompare = (id: string) => {
    setNotice("");
    setCompare((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id);
      if (current.length === 3) {
        setNotice("Compare up to three homes at a time.");
        return current;
      }
      return [...current, id];
    });
  };

  async function runAgent(nextQuery = query) {
    if (!nextQuery.trim() || isRunning) return;
    setQuery(nextQuery);
    setIsRunning(true);
    setNotice("");
    setAnswer("");
    setTrace([{ node: "memory", label: "Reviewing your brief", status: "active" }]);

    try {
      const response = await fetch(`${import.meta.env.VITE_AGENT_API_URL || "http://localhost:8002"}/api/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: nextQuery,
          mode,
          thread_id: localStorage.getItem("aizen-thread-id") || crypto.randomUUID(),
        }),
      });
      if (!response.ok || !response.body) throw new Error("Aizen is temporarily unavailable.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        events.forEach((raw) => {
          const type = raw.match(/^event: (.+)$/m)?.[1];
          const dataLine = raw.match(/^data: (.+)$/m)?.[1];
          if (!type || !dataLine) return;
          const data = JSON.parse(dataLine);
          if (type === "agent_step") {
            setTrace((current) => {
              const next = current.filter((step) => step.node !== data.node);
              return [...next, { node: data.node, label: data.label, status: data.status }];
            });
          }
          if (type === "properties") setProperties(data.properties);
          if (type === "answer_token") setAnswer((current) => current + data.token);
          if (type === "run_failed") setNotice(`${data.message} Switch to Demo Mode to continue.`);
        });
      }
    } catch (error) {
      setNotice(error instanceof Error ? `${error.message} Switch to Demo Mode to continue.` : "Aizen is temporarily unavailable.");
    } finally {
      setIsRunning(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void runAgent();
  }

  const compareProperties = properties.filter((property) => compare.includes(property.id));

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Aizen home"><span>AI</span>ZEN</a>
        <nav><a href="#workspace">Workspace</a><a href="#how-it-works">How it works</a></nav>
        <div className="mode-switch" aria-label="Agent mode">
          <button className={mode === "demo" ? "active" : ""} onClick={() => setMode("demo")}>Demo mode</button>
          <button className={mode === "live" ? "active" : ""} onClick={() => setMode("live")}>Live mode</button>
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <div>
            <p className="eyebrow">Dubai property intelligence</p>
            <h1>Find a home.<br /><em>Know why it fits.</em></h1>
            <p className="hero-copy">Aizen turns a property brief into an inspectable decision: live research, ranked homes, clear trade-offs, and provenance you can see.</p>
            <a className="primary-link" href="#workspace">Start a property brief <span>↓</span></a>
          </div>
          <div className="hero-card">
            <p>Agent confidence</p>
            <strong>94<span>%</span></strong>
            <div className="confidence-bar"><span /></div>
            <small>Marina Vista Residence · strongest fit</small>
          </div>
        </section>

        <section className="proof-strip" id="how-it-works">
          <p><b>01</b> Understand your brief</p><p><b>02</b> Search active data</p><p><b>03</b> Compare and audit</p><p><b>04</b> Make decision with confidence</p>
        </section>

        <section className="workspace" id="workspace" aria-label="Aizen property workspace">
          <aside className="brief-rail">
            <p className="section-label">Guided starts</p>
            <h2>What are you looking for?</h2>
            {quickStarts.map((prompt) => <button key={prompt} onClick={() => void runAgent(prompt)}>{prompt}<span>↗</span></button>)}
            <div className="rail-note"><span className="pulse" /> {mode === "demo" ? "Reliable portfolio scenario" : "Connected to live agent"}</div>
          </aside>

          <section className="agent-canvas">
            <div className="canvas-header">
              <div><p className="section-label">Aizen workspace</p><h2>Your property brief</h2></div>
              <span className="source-badge">{mode === "demo" ? "Demo data" : "Live data"}</span>
            </div>
            <div className="trace" aria-label="Agent activity">
              {trace.map((step) => <div className={`trace-step ${step.status}`} key={step.node}><span>{step.status === "complete" ? "✓" : "·"}</span>{step.label}</div>)}
            </div>
            <form className="query-box" onSubmit={submit}>
              <textarea value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Property brief" rows={2} />
              <button type="submit" disabled={isRunning}>{isRunning ? "Aizen is working…" : "Ask Aizen →"}</button>
            </form>
            {notice && <p className="notice" role="status">{notice}</p>}
            <div className="answer"><span>A</span><p>{answer || "Aizen is collecting the strongest evidence for your brief…"}</p></div>

            <div className="results-heading"><div><p className="section-label">Selected matches</p><h3>{properties.length} homes worth inspecting</h3></div><span>Ranked by fit · {properties[0]?.data_source || "active"} data</span></div>
            <div className="property-grid">
              {properties.map((property) => (
                <article className="property-card" key={property.id}>
                  <button className={`property-visual ${property.visual_key}`} onClick={(event) => chooseProperty(property, event.currentTarget)} aria-label={`Open ${property.title}`}>
                    <span>Representative visual</span><b>{score(property.fit_score)}</b>
                  </button>
                  <div className="property-content">
                    <button className="property-title" onClick={(event) => chooseProperty(property, event.currentTarget)}>{property.title}</button>
                    <p>{property.area}</p><strong>{formatPrice(property.price, property.currency)}</strong>
                    <div className="property-specs"><span>{property.beds} bed</span><span>{property.baths} bath</span><span>{property.size_sqft.toLocaleString()} sq ft</span></div>
                    <div className="property-actions"><button onClick={() => toggleShortlist(property.id)}>{shortlist.includes(property.id) ? "Saved" : "Save"}</button><button onClick={() => toggleCompare(property.id)}>{compare.includes(property.id) ? "Comparing" : "Compare"}</button></div>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <aside className="map-rail"><div className="map-header"><div><p className="section-label">Location view</p><h3>Where the options sit</h3></div><span>{properties.length} pins</span></div><PropertyMap properties={properties} selectedId={selected?.id} onSelect={chooseProperty} /><p className="map-note">Select a pin to inspect its match details.</p></aside>
        </section>

        <section className="compare-tray" aria-label="Comparison shortlist">
          <div><p className="section-label">Decision tray</p><h2>Compare your shortlist</h2><p>Select up to three homes. Saved choices stay in this browser.</p></div>
          <div className="compare-slots">{[0, 1, 2].map((slot) => {
            const property = compareProperties[slot];
            return property ? <button key={property.id} onClick={(event) => chooseProperty(property, event.currentTarget)}><span>{score(property.fit_score)}</span>{property.title}<b>↗</b></button> : <div className="empty-slot" key={slot}>Add a home</div>;
          })}</div>
        </section>
      </main>

      {selected && <div className="drawer-backdrop" onClick={closeDrawer}>
        <aside className="intelligence-drawer" role="complementary" aria-label="Property intelligence" onClick={(event) => event.stopPropagation()}>
          <button className="close" onClick={closeDrawer} aria-label="Close property intelligence">×</button>
          <div className={`drawer-visual ${selected.visual_key}`}><span>Representative visual</span><b>{score(selected.fit_score)}</b></div>
          <p className="section-label">Property intelligence</p><h2>{selected.title}</h2><p className="drawer-area">{selected.area} · {selected.property_type}</p><strong className="drawer-price">{formatPrice(selected.price, selected.currency)}</strong>
          <div className="drawer-actions"><button className="dark-button" onClick={() => toggleShortlist(selected.id)}>{shortlist.includes(selected.id) ? "Saved to shortlist" : "Save to shortlist"}</button><button onClick={() => toggleCompare(selected.id)}>{compare.includes(selected.id) ? "Remove compare" : "Add compare"}</button></div>
          <section><h3>Why Aizen selected it</h3><ul>{selected.matched_criteria.map((item) => <li key={item}>✓ {item}</li>)}{selected.unmatched_criteria.map((item) => <li className="gap" key={item}>△ {item}</li>)}</ul></section>
          <section className="spec-grid"><h3>Key details</h3><div><span>Bedrooms</span><b>{selected.beds}</b></div><div><span>Bathrooms</span><b>{selected.baths}</b></div><div><span>Size</span><b>{selected.size_sqft.toLocaleString()} sq ft</b></div><div><span>Parking</span><b>{selected.parking_spaces}</b></div><div><span>Furnishing</span><b>{selected.furnishing}</b></div><div><span>Completion</span><b>{selected.completion_status}</b></div></section>
          <footer><span>{selected.data_intent === "insights_only" ? "Historical market signal" : "Active listing signal"}</span>{selected.source_url && <a href={selected.source_url} target="_blank" rel="noreferrer">View source ↗</a>}</footer>
        </aside>
      </div>}
    </div>
  );
}

export default App;
