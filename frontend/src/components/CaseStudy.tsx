import BrandMark from "./BrandMark";

const nodes = [
  ["01", "memory", "Restores the private session"],
  ["02", "query_relevancy", "Checks Dubai property scope"],
  ["03", "query_understanding", "Validates the buyer brief"],
  ["04", "query_routing", "Chooses the evidence path"],
  ["05", "web_search", "Gathers cited area research"],
  ["06", "comparison_engine", "Evaluates criteria deterministically"],
  ["07", "reflection", "Audits facts and arithmetic"],
  ["08", "answer_generation", "Shapes concise buyer guidance"],
] as const;

export default function CaseStudy() {
  return <main className="case-study">
    <header className="case-header"><BrandMark /><a href="#/">Return to product</a></header>
    <section className="case-hero dark-surface">
      <p className="eyebrow">Recruiter case study · local flagship build</p>
      <h1>Find what fits.<br /><em>See what matters.</em></h1>
      <p>Aizen turns one Dubai home request into a live, validated investigation, a considered shortlist, and a printable decision dossier.</p>
    </section>
    <section className="case-section"><p className="eyebrow">Product thesis</p><h2>Search less. Decide better.</h2><p>One submission becomes a structured buyer brief. Aizen keeps the model focused on language while local code handles filtering, fit, evidence, and affordability. Every result arrives with the context needed for a confident next step.</p></section>
    <section className="case-section"><p className="eyebrow">Architecture</p><h2>Eight nodes, one clear journey</h2><div className="case-graph" aria-label="Aizen LangGraph routing diagram"><div className="case-graph-row"><GraphNode node={nodes[0]} /><Arrow label="next" /><GraphNode node={nodes[1]} /></div><div className="case-graph-branch"><div className="case-branch-line"><span>Dubai property</span><Arrow label="→" /><GraphNode node={nodes[2]} /><Arrow label="→" /><GraphNode node={nodes[3]} /></div><div className="case-branch-line"><span>Out of scope</span><Arrow label="→" /><strong className="case-end">END</strong></div></div><div className="case-graph-branch case-graph-branch-wide"><div className="case-branch-line"><span>Web research</span><Arrow label="→" /><GraphNode node={nodes[4]} /><Arrow label="→" /><GraphNode node={nodes[7]} /></div><div className="case-branch-line"><span>Property search</span><Arrow label="→" /><GraphNode node={nodes[5]} /><Arrow label="→" /><GraphNode node={nodes[6]} /><Arrow label="→" /><GraphNode node={nodes[7]} /></div></div><div className="case-graph-footer"><span>Guidance</span><Arrow label="→" /><strong className="case-end">END</strong></div></div><p>LangGraph preserves eight named responsibilities. Query routing selects the web research path or the property path; the comparison and reflection stages remain deterministic and auditable.</p></section>
    <section className="case-grid"><article><p className="eyebrow">Experience</p><h3>Editorial buyer journey</h3><p>A warm reading surface, focused brief ledger, cinematic research reveal, and synchronized shortlist turn technical depth into a calm decision workspace.</p></article><article><p className="eyebrow">Decisioning</p><h3>Structured guidance</h3><p>Hard criteria, evidence coverage, stable ordering, comparison, affordability scenarios, and source references keep every recommendation easy to inspect.</p></article><article><p className="eyebrow">Engineering</p><h3>Release-gated proof</h3><p>Python, component, browser, Compose, accessibility, mobile, print, and security checks are documented as repeatable local commands.</p></article></section>
    <section className="case-section"><p className="eyebrow">Built for clarity</p><h2>Beautiful on the surface. Considered underneath.</h2><p>Aizen keeps its visual language focused: warm editorial surfaces for reading and decision work, selective dark cinematic moments for research and evidence, abstract architectural geometry for every home, and a compact technical vocabulary behind the scenes.</p><div className="case-links"><a href="/docs/architecture.md">Architecture</a><a href="/docs/scoring-and-evidence.md">Scoring &amp; evidence</a><a href="/docs/evaluation.md">Evaluation</a><a href="/docs/design-system.md">Design system</a></div></section>
  </main>;
}

function GraphNode({ node }: { node: readonly [string, string, string] }) {
  return <div className="case-graph-node"><span>{node[0]}</span><b>{node[1]}</b><small>{node[2]}</small></div>;
}

function Arrow({ label }: { label: string }) {
  return <span className="case-graph-arrow" aria-hidden="true">{label}</span>;
}
