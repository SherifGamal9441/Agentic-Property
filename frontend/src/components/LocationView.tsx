import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import type { Property } from "../types";

const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

export default function LocationView({ properties, selectedId, onSelect }: { properties: Property[]; selectedId?: string; onSelect: (property: Property) => void }) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef<maplibregl.Marker[]>([]);
  const [failed, setFailed] = useState(false);
  const located = properties.filter((item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude));

  useEffect(() => {
    if (!container.current || map.current || !located.length) return;
    try {
      const instance = new maplibregl.Map({ container: container.current, style: STYLE_URL, center: [located[0].longitude as number, located[0].latitude as number], zoom: 11.5 });
      instance.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      instance.on("error", () => setFailed(true));
      map.current = instance;
    } catch {
      setFailed(true);
    }
    return () => { markers.current.forEach((marker) => marker.remove()); map.current?.remove(); map.current = null; };
  }, [located.length]);

  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    markers.current.forEach((marker) => marker.remove());
    markers.current = located.map((property, index) => {
      const element = document.createElement("button");
      element.className = `map-pin ${property.id === selectedId ? "is-selected" : ""}`;
      element.textContent = String(index + 1);
      element.type = "button";
      element.setAttribute("aria-label", `Select ${property.title}`);
      element.onclick = () => onSelect(property);
      return new maplibregl.Marker({ element }).setLngLat([property.longitude as number, property.latitude as number]).addTo(instance);
    });
  }, [located, onSelect, selectedId]);

  return <section className="location-panel dark-surface" aria-label="Location evidence"><div className="map-copy"><p className="eyebrow">OpenFreeMap · exact supplied coordinates</p><h2>Location is evidence, not decoration.</h2><p>{located.length} of {properties.length} homes include exact coordinates. Missing coordinates remain explicit.</p></div><div ref={container} className="map-canvas" />{failed && <div className="map-fallback"><b>Basemap unavailable</b><p>Exact coordinate evidence remains listed below.</p></div>}<ol className="coordinate-list">{properties.map((property) => <li key={property.id}><button type="button" onClick={() => onSelect(property)}><span>{property.title}</span><small>{property.location_status === "exact" ? `${property.latitude}, ${property.longitude}` : "Area-only; exact coordinate unavailable"}</small></button></li>)}</ol></section>;
}
