import { calculateScenario } from "../finance";
import { money, percent } from "../format";
import type { AffordabilityInput, Property, ScenarioForm } from "../types";

function scenarioPayment(property: Property, form: ScenarioForm) {
  if (property.price == null || Object.values(form).some((value) => value === "")) return "Complete scenario";
  try {
    const result = calculateScenario({ price: property.price, ...Object.fromEntries(Object.entries(form).map(([key, value]) => [key, Number(value)])) } as AffordabilityInput);
    return money(result.monthlyPayment);
  } catch {
    return "Scenario invalid";
  }
}

export default function ComparisonView({ properties, selectedIds, statuses, scenario, onSelect, onRemove, onDossier }: {
  properties: Property[];
  selectedIds: string[];
  statuses: Record<string, string>;
  scenario: ScenarioForm;
  onSelect: (property: Property) => void;
  onRemove: (id: string) => void;
  onDossier: () => void;
}) {
  const selected = selectedIds.map((id) => properties.find((property) => property.id === id)).filter((property): property is Property => Boolean(property));
  if (!selected.length) return <section className="comparison-empty"><p className="eyebrow">Side-by-side decision space</p><h2>Select up to four homes to compare.</h2><p>Open any home profile, then bring your leading options together.</p></section>;
  const rows: Array<[string, (property: Property) => React.ReactNode]> = [
    ["Suitability", (property) => property.suitability], ["Reported price", (property) => money(property.price)], ["Deterministic fit", (property) => percent(property.fit_score)], ["Evidence coverage", (property) => percent(property.evidence_coverage)], ["Area", (property) => property.area || "Not reported"], ["Bedrooms", (property) => property.beds ?? "Not reported"], ["Bathrooms", (property) => property.baths ?? "Not reported"], ["Property type", (property) => property.property_type || "Not reported"], ["Furnishing", (property) => property.furnishing || "Not reported"], ["Completion", (property) => property.completion_status || "Not reported"], ["Completion year", (property) => property.year_of_completion ?? "Not reported"], ["Matched criteria", (property) => property.matched_criteria.join(", ") || "None recorded"], ["Conflicts", (property) => property.conflicting_criteria.join(", ") || "None known"], ["Unknowns", (property) => [...property.unknown_criteria, ...property.unsupported_criteria].join(", ") || "No known criterion gaps"], ["Captured source", (property) => property.source_name || "Source unavailable"], ["Observed", (property) => property.observed_at || "Date unavailable"], ["Buyer status", (property) => statuses[property.id]?.replace("_", " ") || "Not set"], ["Monthly scenario", (property) => scenarioPayment(property, scenario)],
  ];
  return <section className="comparison-view" aria-label="Property comparison"><div className="section-heading"><div><p className="eyebrow">Decision matrix</p><h2>See your leading homes side by side.</h2></div><button type="button" className="button-dark dossier-button" onClick={onDossier}>Build dossier</button></div><div className="comparison-scroll"><table><thead><tr><th scope="col">Property detail</th>{selected.map((property) => <th scope="col" key={property.id}><button type="button" onClick={() => onSelect(property)}>{property.title} ↗</button><button type="button" className="remove-compare" aria-label={`Remove ${property.title} from comparison`} onClick={() => onRemove(property.id)}>Remove</button></th>)}</tr></thead><tbody>{rows.map(([label, value]) => <tr key={label}><th scope="row">{label}</th>{selected.map((property) => <td key={property.id}>{value(property)}</td>)}</tr>)}</tbody></table></div></section>;
}
