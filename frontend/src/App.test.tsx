import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import App from "./App";
import type { BuyerBrief, Property } from "./types";

const brief: BuyerBrief = {
  version: 1,
  mode: "property_search",
  original_query: "Ready 2BR in Dubai Marina under AED 2M",
  currency: "AED",
  criteria: [
    { id: "area", label: "Dubai Marina", priority: "must_have", field: "area", operator: "contains", value: "Dubai Marina", verifiable: true },
    { id: "budget", label: "Under AED 2M", priority: "must_have", field: "price", operator: "lte", value: 2_000_000, verifiable: true },
  ],
};

const properties: Property[] = Array.from({ length: 8 }, (_, index) => ({
  id: `home-${index + 1}`,
  title: `Marina Residence ${index + 1}`,
  area: "Dubai Marina",
  price: 1_400_000 + index * 10_000,
  currency: "AED",
  beds: 2,
  baths: 2,
  property_type: "Apartments",
  furnishing: "Furnished",
  completion_status: "completed",
  year_of_completion: 2022,
  latitude: 25.08 + index * 0.001,
  longitude: 55.14 + index * 0.001,
  location_status: "exact",
  source_url: `https://example.test/${index}`,
  source_name: "Captured listing source",
  observed_at: "2026-07-02",
  snapshot_id: "active-2026-07-02-v1",
  dataset_snapshot_at: "2026-07-02",
  data_status: "listing_snapshot",
  fit_score: 1,
  evidence_coverage: 1,
  suitability: "suitable",
  evaluations: [],
  matched_criteria: ["Dubai Marina", "Under AED 2M"],
  conflicting_criteria: [],
  unknown_criteria: [],
  unsupported_criteria: [],
}));

afterEach(() => {
  localStorage.clear();
  location.hash = "";
  vi.unstubAllGlobals();
});

test("requires buyer confirmation before starting a run", async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(brief), { status: 200, headers: { "Content-Type": "application/json" } }))
    .mockResolvedValueOnce(new Response([
      `event: run_started\ndata: {"thread_id":"thread-1","snapshot_id":"active-2026-07-02-v1"}\n\n`,
      `event: properties\ndata: {"total_matches":0,"shown_count":0,"properties":[]}\n\n`,
      `event: sources\ndata: {"items":[]}\n\n`,
      `event: run_completed\ndata: {"route":"query_routing","data_source":"active","evidence_quality":"insufficient"}\n\n`,
    ].join(""), { status: 200, headers: { "Content-Type": "text/event-stream" } }));
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<App />);

  await user.type(screen.getByLabelText("Describe your ideal Dubai home"), brief.original_query);
  await user.click(screen.getByRole("button", { name: "Interpret my brief" }));

  expect(await screen.findByText("Confirm what Aizen understood")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  await user.click(screen.getByRole("button", { name: "Confirm & search" }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
});

test("shows six ranked homes first and reveals the rest on demand", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties} initialBrief={brief} />);

  expect(screen.getAllByRole("article", { name: /Marina Residence/ })).toHaveLength(6);
  await user.click(screen.getByRole("button", { name: "View 2 more homes" }));
  expect(screen.getAllByRole("article", { name: /Marina Residence/ })).toHaveLength(8);
});

test("keeps shortlist, comparison, private notes, and dossier synchronized", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 2)} initialBrief={brief} />);

  await user.click(screen.getAllByRole("button", { name: "Review evidence" })[0]);
  await user.click(screen.getByRole("button", { name: "Add to shortlist" }));
  await user.click(screen.getByRole("button", { name: "Add to comparison" }));
  await user.type(screen.getByLabelText("Private note"), "Ask about the building service history.");
  await user.click(screen.getByRole("button", { name: "Close property evidence" }));

  expect(screen.getByText("1 shortlisted")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Open buyer dossier" }));
  expect(screen.getByText("Ask about the building service history.")).toBeInTheDocument();
  expect(screen.getByText("Buyer dossier")).toBeInTheDocument();
});

test("reset showcase clears all Aizen browser state", async () => {
  localStorage.setItem("aizen-shortlist", JSON.stringify(["home-1"]));
  localStorage.setItem("aizen-notes", JSON.stringify({ "home-1": "private" }));
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 1)} initialBrief={brief} />);

  await user.click(screen.getByRole("button", { name: "Reset showcase" }));

  await waitFor(() => expect(Object.keys(localStorage).filter((key) => key.startsWith("aizen-"))).toHaveLength(0));
});

test("offers the recruiter case study through hash navigation", () => {
  location.hash = "#/case-study";
  fireEvent(window, new HashChangeEvent("hashchange"));
  render(<App />);

  expect(screen.getByRole("heading", { name: "From prompt to auditable buyer decision" })).toBeInTheDocument();
  expect(screen.getByText("Eight nodes, one evidence contract")).toBeInTheDocument();
});
