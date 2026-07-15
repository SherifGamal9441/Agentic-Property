import BrandMark from "./BrandMark";

const nodes = ["Memory", "Scope", "Understanding", "Routing", "Web research", "Comparison", "Evidence audit", "Answer"];

export default function CaseStudy() {
  return <main className="case-study">
    <header className="case-header"><BrandMark /><a href="#/">Return to product</a></header>
    <section className="case-hero dark-surface">
      <p className="eyebrow">Recruiter case study · local flagship build</p>
      <h1>From prompt to auditable buyer decision</h1>
      <p>Aizen turns one Dubai home request into a validated live investigation, deterministic fit evidence, and a printable decision dossier.</p>
    </section>
    <section className="case-section"><p className="eyebrow">Product thesis</p><h2>Buyer confidence comes from visible evidence—not a persuasive score.</h2><p>One submission interprets and runs a validated brief; correction remains one drawer away. The model extracts references. Pydantic validates. Local code filters, scores, audits, and calculates. Historical transactions stay context; captured listings stay inventory.</p></section>
    <section className="case-section"><p className="eyebrow">Architecture</p><h2>Eight nodes, one evidence contract</h2><div className="node-flow">{nodes.map((node, index) => <div key={node}><span>{String(index + 1).padStart(2, "0")}</span>{node}</div>)}</div><p>LangGraph preserves the recognizable agent topology while MCP keeps property access behind a typed service boundary. PostgreSQL is primary; SQLite is an explicit degraded fallback.</p></section>
    <section className="case-grid"><article><p className="eyebrow">Truth</p><h3>Frozen snapshot</h3><p>Every shown home carries a captured source, observed date, and snapshot identity. Unverified unit size and dedicated parking are deliberately withheld.</p></article><article><p className="eyebrow">Decisioning</p><h3>Structured guidance</h3><p>Hard conflicts exclude, unknown must-haves become conditional, and the result reveal references only audited properties and criteria. Evidence coverage is never presented as AI confidence.</p></article><article><p className="eyebrow">Evaluation</p><h3>Release-gated proof</h3><p>Python, component, browser, Compose, accessibility, mobile, and print gates are documented from verified commands.</p></article></section>
    <section className="case-section"><p className="eyebrow">Deliberate limits</p><h2>Credibility includes saying no.</h2><p>No valuation model, financial advice, fabricated photography, paid map, cached AI answer, automatic relaxation, account system, or unsupported lifestyle claim.</p><div className="case-links"><a href="/docs/architecture.md">Architecture</a><a href="/docs/scoring-and-evidence.md">Scoring & evidence</a><a href="/docs/evaluation.md">Evaluation</a></div></section>
  </main>;
}
