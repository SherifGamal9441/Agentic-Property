import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

const completedRun = (items: Property[] = []) => new Response([
  `event: run_started\ndata: {"thread_id":"thread-1","snapshot_id":"active-2026-07-02-v1"}\n\n`,
  `event: properties\ndata: ${JSON.stringify({ candidate_count: items.length, audited_count: items.length, total_matches: items.length, shown_count: items.length, properties: items })}\n\n`,
  `event: sources\ndata: {"items":[]}\n\n`,
  `event: guidance\ndata: ${JSON.stringify({ guidance: { version: 1, outcome: items.length ? "matches" : "no_match", best_match_id: items[0]?.id || null, runner_up_id: items[1]?.id || null, reasons: [], caveats: [], next_action: items.length ? "review_best_match" : "edit_brief" } })}\n\n`,
  `event: run_completed\ndata: {"route":"query_routing","data_source":"active","evidence_quality":"strong"}\n\n`,
].join(""), { status: 200, headers: { "Content-Type": "text/event-stream" } });

afterEach(() => {
  localStorage.clear();
  location.hash = "";
  vi.unstubAllGlobals();
});

test("interprets and automatically starts the live run with one action", async () => {
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
  await user.click(screen.getByRole("button", { name: "Find matching homes" }));

  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(screen.queryByText("Confirm what Aizen understood")).not.toBeInTheDocument();
  expect(await screen.findByText("No exact snapshot match")).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: "Edit brief" })).toHaveLength(2);
});

test("shows six ranked homes first and reveals the rest on demand", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties} initialBrief={brief} />);

  expect(screen.getAllByRole("article", { name: /Marina Residence/ })).toHaveLength(6);
  await user.click(screen.getByRole("button", { name: "View 2 more homes" }));
  expect(screen.getAllByRole("article", { name: /Marina Residence/ })).toHaveLength(8);
});

test("presents the active brief as an editorial ledger", () => {
  render(<App initialProperties={properties.slice(0, 1)} initialBrief={brief} />);

  expect(screen.getAllByText(brief.original_query)).toHaveLength(2);
  expect(screen.getByText("2 criteria · 2 must-haves")).toBeInTheDocument();
  expect(screen.getByText("Must-have")).toBeInTheDocument();
});

test("navigation switches workspace and scrolls its heading below the header", async () => {
  const scrollIntoView = vi.fn();
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: scrollIntoView });
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 1)} initialBrief={brief} />);

  const areasButton = screen.getAllByRole("button").find((button) => button.textContent?.trim() === "Areas");
  expect(areasButton).toBeDefined();
  await user.click(areasButton!);

  expect(await screen.findByRole("heading", { name: "Compare reported area evidence" })).toBeInTheDocument();
  await waitFor(() => expect(scrollIntoView).toHaveBeenCalledWith(expect.objectContaining({ block: "start" })));
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

test("brief drawer applies edits and reruns the structured brief", async () => {
  const fetchMock = vi.fn().mockResolvedValue(completedRun(properties.slice(0, 1)));
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 1)} initialBrief={brief} />);

  await user.click(screen.getAllByRole("button", { name: "Edit brief" })[0]);
  await user.clear(screen.getByLabelText("Value for Dubai Marina"));
  await user.type(screen.getByLabelText("Value for Dubai Marina"), "Business Bay");
  await user.click(screen.getByRole("button", { name: "Apply & rerun" }));

  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body)).brief.criteria[0].value).toBe("Business Bay");
});

test("selected homes open a side-by-side evidence matrix", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 2)} initialBrief={brief} />);

  await user.click(screen.getByRole("button", { name: "Compare top matches" }));

  expect(screen.getByLabelText("Property comparison")).toBeInTheDocument();
  expect(screen.getByRole("rowheader", { name: "Evidence coverage" })).toBeInTheDocument();
  expect(within(screen.getByLabelText("Property comparison")).getAllByRole("button", { name: /Remove Marina Residence .* from comparison/ })).toHaveLength(2);
});

test("a running request can be cancelled without replaying results", async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(brief), { status: 200, headers: { "Content-Type": "application/json" } }))
    .mockImplementationOnce((_url, init: RequestInit) => new Promise((_resolve, reject) => init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")))));
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<App />);

  await user.type(screen.getByLabelText("Describe your ideal Dubai home"), brief.original_query);
  await user.click(screen.getByRole("button", { name: "Find matching homes" }));
  await user.click(await screen.findByRole("button", { name: "Cancel run" }));

  expect(await screen.findByRole("heading", { name: "Your brief is ready when you are." })).toBeInTheDocument();
  expect(screen.queryByRole("article", { name: /Marina Residence/ })).not.toBeInTheDocument();
});
