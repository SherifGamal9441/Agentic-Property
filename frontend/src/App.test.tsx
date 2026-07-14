import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import App, { type Property } from "./App";

const properties: Property[] = Array.from({ length: 5 }, (_, index) => ({
  id: `property-${index + 1}`,
  title: `Property ${index + 1}`,
  area: "Dubai Marina",
  price: 1_500_000 + index * 100_000,
  currency: "AED",
  beds: 2,
  baths: 2,
  property_type: "Apartment",
  size_sqft: 1_000,
  furnishing: "Furnished",
  completion_status: "completed",
  parking_spaces: 1,
  year_of_completion: 2024,
  latitude: index === 4 ? null : 25.08,
  longitude: index === 4 ? null : 55.14 + index * 0.001,
  location_status: index === 4 ? "unavailable" : "exact",
  source_url: "https://example.test/listing",
  source_name: "Listing source",
  observed_at: "2026-07-01",
  dataset_snapshot_at: "2026-07-01",
  data_status: "active_dataset_listing",
  fit_score: 0.9 - index * 0.01,
  score_factors: ["Matches Dubai Marina"],
  matched_criteria: ["Matches Dubai Marina"],
  unmatched_criteria: [],
  price_assessment: "fair",
  data_intent: "recommend",
  data_source: "active",
}));

afterEach(() => { localStorage.clear(); vi.unstubAllGlobals(); });

test("starts with an editorial empty workspace without ingestion jargon", () => {
  render(<App />);

  expect(screen.getByRole("link", { name: /start a property brief/i })).toHaveAttribute("href", "#workspace");
  expect(screen.getByText(/guided starts/i)).toBeInTheDocument();
  expect(screen.getByText(/start with a property brief/i)).toBeInTheDocument();
  expect(screen.queryByText(/csv loaded into database/i)).not.toBeInTheDocument();
});

test("adds and removes shortlist and comparison entries from property detail", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 1)} />);

  await user.click(screen.getAllByRole("button", { name: "Open Property 1" })[0]);
  const drawer = screen.getByRole("dialog", { name: /property intelligence/i });
  await user.click(within(drawer).getByRole("button", { name: "Add to shortlist" }));
  await user.click(within(drawer).getByRole("button", { name: "Add to comparison" }));

  expect(within(drawer).getByRole("button", { name: "Remove from shortlist" })).toBeInTheDocument();
  expect(within(drawer).getByRole("button", { name: "Remove from comparison" })).toBeInTheDocument();
  expect(screen.getByRole("region", { name: /comparison shortlist/i })).toHaveTextContent("Property 1");
});

test("compares up to four properties and rejects a fifth", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties} />);

  for (const button of screen.getAllByRole("button", { name: "Add to comparison" })) await user.click(button);

  expect(screen.getByRole("status")).toHaveTextContent("Compare up to four homes at a time.");
  expect(screen.getByRole("region", { name: /comparison shortlist/i })).toHaveTextContent("Property 4");
  expect(screen.getByRole("region", { name: /comparison shortlist/i })).not.toHaveTextContent("Property 5");
});

test("scopes map evidence and lets buyers choose homes in an overlap group", async () => {
  const user = userEvent.setup();
  const overlapping = [{ ...properties[0], id: "overlap", title: "Overlap home" }, { ...properties[1], id: "overlap-2", title: "Overlap home two", latitude: properties[0].latitude, longitude: properties[0].longitude }];
  render(<App initialProperties={overlapping} />);

  await user.click(screen.getByRole("button", { name: "Show shortlist locations" }));
  expect(screen.getByText(/no exact shortlist locations/i)).toBeInTheDocument();
  await user.click(screen.getAllByRole("button", { name: "Add to shortlist" })[0]);
  await user.click(screen.getByRole("button", { name: "Add to shortlist" }));
  await user.click(screen.getByRole("button", { name: "Show shortlist locations" }));
  await user.click(screen.getByRole("button", { name: /open 2 homes in dubai marina/i }));
  expect(screen.getByText(/choose a home at this location/i)).toBeInTheDocument();
  await user.click(within(screen.getByRole("region", { name: "Location group" })).getByRole("button", { name: "Open Overlap home two" }));
  expect(screen.getByRole("dialog", { name: /property intelligence/i })).toHaveTextContent("Overlap home two");
});

test("saves and restores buyer criteria and shortlist on the same device", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 1)} />);

  await user.click(screen.getByRole("button", { name: "Add to shortlist" }));
  await user.type(screen.getByRole("textbox", { name: "Property brief" }), "Two bedrooms in Dubai Marina");
  await user.type(screen.getByRole("textbox", { name: "Must-have criteria" }), "waterfront");
  await user.click(screen.getByRole("button", { name: /save this search/i }));
  await user.click(screen.getByRole("button", { name: "Clear research brief" }));
  await user.click(screen.getByRole("button", { name: "Restore saved brief" }));

  expect(screen.getByRole("textbox", { name: "Property brief" })).toHaveValue("Two bedrooms in Dubai Marina");
  expect(screen.getByRole("textbox", { name: "Must-have criteria" })).toHaveValue("waterfront");
  expect(screen.getByRole("status")).toHaveTextContent("Saved brief restored.");
});

test("shows only valid coordinate pins and keeps selection synchronized", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties} />);

  const map = screen.getByLabelText("Property location view");
  expect(within(map).getAllByRole("button", { name: /open property/i })).toHaveLength(4);
  expect(screen.getByText(/property 5 has area-only location evidence/i)).toBeInTheDocument();

  await user.click(within(map).getByRole("button", { name: "Open Property 2" }));
  expect(screen.getByRole("dialog", { name: /property intelligence/i })).toHaveTextContent("Property 2");
});

test("sorts visible results and keeps buyer decision evidence", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={[properties[1], properties[0]]} />);

  await user.selectOptions(screen.getByRole("combobox", { name: "Sort properties" }), "price-low");
  expect(within(screen.getByRole("region", { name: "Property results" })).getAllByRole("button", { name: /open property/i })[0]).toHaveAccessibleName("Open Property 1");

  await user.click(screen.getAllByRole("button", { name: "Add to comparison" })[0]);
  await user.click(screen.getByRole("button", { name: "View decision sheet" }));
  expect(screen.getByRole("dialog", { name: /buyer decision sheet/i })).toHaveTextContent("Historical market context");
  await user.type(screen.getByRole("spinbutton", { name: "Transfer cost" }), "5000");
  expect(screen.getByRole("dialog", { name: /buyer decision sheet/i })).toHaveTextContent("AED 1,505,000");
});

test("restores a visible research conversation from the current browser session", async () => {
  localStorage.setItem("aizen-thread-id", "8f9d67d9-61de-44d9-a95d-8d0c5c8a9d4f");
  localStorage.setItem("aizen-research-sessions", JSON.stringify([{ threadId: "8f9d67d9-61de-44d9-a95d-8d0c5c8a9d4f", title: "Marina search", lastActivityAt: "2026-07-14T00:00:00.000Z" }]));
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ messages: [{ role: "user", content: "2BR in Dubai Marina" }, { role: "assistant", content: "Here are reported matches." }] }) }));

  render(<App />);

  expect(await screen.findByRole("region", { name: "Research conversation" })).toHaveTextContent("Here are reported matches.");
  expect(screen.getByRole("region", { name: "Research sessions" })).toHaveTextContent("Marina search");
});

test("shows reported historical context and keeps buyer decisions local", async () => {
  const user = userEvent.setup();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ area: "Dubai Marina", matching_basis: ["area", "property_type", "beds"], record_count: 12, period_start: "2025-01-01", period_end: "2026-01-01", price_min: 1_000_000, price_max: 2_000_000, price_per_sqft_min: 1000, price_per_sqft_max: 2000 }) }));
  render(<App initialProperties={properties.slice(0, 1)} />);

  await user.click(screen.getByRole("button", { name: "Save" }));
  expect(screen.getByText("Buyer decision: saved")).toBeInTheDocument();
  await user.click(screen.getAllByRole("button", { name: "Add to comparison" })[0]);
  await user.click(screen.getByRole("button", { name: "View decision sheet" }));

  expect(await screen.findByText(/12 reported transactions/i)).toBeInTheDocument();
  expect(screen.getByRole("dialog", { name: /buyer decision sheet/i })).toHaveTextContent("Historical market context only—not active inventory or a valuation.");
});
