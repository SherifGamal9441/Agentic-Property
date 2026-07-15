import type { Property } from "../types";

function visualVariant(property: Property) {
  const seed = `${property.id}:${property.area}`.split("").reduce((value, character) => (value * 31 + character.charCodeAt(0)) >>> 0, 7);
  return { geometry: seed % 8, palette: (seed >>> 3) % 4 };
}

export default function PropertyVisual({ property, rank, large = false }: { property: Property; rank: number; large?: boolean }) {
  const variant = visualVariant(property);

  return <div className={`property-visual ${large ? "property-visual-large" : ""} visual-geometry-${variant.geometry} visual-palette-${variant.palette}`}>
    <div className="abstract-visual" aria-hidden="true"><span>{String(rank).padStart(2, "0")}</span><i /><i /><i /></div>
  </div>;
}
