import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";

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
  fit_score: 0.9,
  score_factors: ["Matches Dubai Marina"],
  matched_criteria: ["Matches Dubai Marina"],
  unmatched_criteria: [],
  price_assessment: "fair",
  data_intent: "recommend",
  data_source: "active",
}));

test("starts with an honest empty workspace", () => {
  render(<App />);

  expect(screen.getByRole("link", { name: /start a property brief/i })).toHaveAttribute("href", "#workspace");
  expect(screen.getByText(/guided starts/i)).toBeInTheDocument();
  expect(screen.getByText(/understand your brief/i)).toBeInTheDocument();
  expect(screen.getByText(/start with a property brief/i)).toBeInTheDocument();
  expect(screen.queryByText(/marina vista residence/i)).not.toBeInTheDocument();
});

test("compares up to four properties and rejects a fifth", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties} />);

  for (const button of screen.getAllByRole("button", { name: "Compare" })) {
    await user.click(button);
  }

  expect(screen.getByRole("status")).toHaveTextContent("Compare up to four homes at a time.");
  expect(screen.getByRole("region", { name: /comparison shortlist/i })).toHaveTextContent("Property 4");
  expect(screen.getByRole("region", { name: /comparison shortlist/i })).not.toHaveTextContent("Property 5");
});

test("shows only valid coordinate pins and keeps card selection synchronized", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties} />);

  const map = screen.getByLabelText("Property location view");
  expect(within(map).getAllByRole("button", { name: /open property/i })).toHaveLength(4);
  expect(screen.getByText(/property 5 is shown by area only/i)).toBeInTheDocument();

  await user.click(within(map).getByRole("button", { name: "Open Property 2" }));
  expect(screen.getByRole("complementary", { name: /property intelligence/i })).toHaveTextContent("Property 2");
});

test("shows buyer decision evidence and saves local search", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 2)} />);

  await user.click(screen.getAllByRole("button", { name: "Compare" })[0]);
  await user.click(screen.getByRole("button", { name: "View decision sheet" }));
  expect(screen.getByRole("dialog", { name: /buyer decision sheet/i })).toHaveTextContent("Historical comparable evidence");
  expect(screen.getByRole("dialog", { name: /buyer decision sheet/i })).toHaveTextContent("Total ownership cost assumptions");
  await user.type(screen.getByRole("spinbutton", { name: "Transfer cost" }), "5000");
  expect(screen.getByRole("dialog", { name: /buyer decision sheet/i })).toHaveTextContent("Entered costs: AED 5,000");

  await user.type(screen.getByRole("textbox", { name: "Property brief" }), "Two bedrooms in Dubai Marina");
  await user.click(screen.getByRole("button", { name: /save this search/i }));
  expect(screen.getByRole("status")).toHaveTextContent("Search saved in this browser.");
});

test("flags saved research only when a newer active snapshot is shown", () => {
  localStorage.setItem("aizen-saved-searches", JSON.stringify([{
    id: "saved-1",
    query: "Two bedrooms in Dubai Marina",
    snapshot: "2026-06-01",
    resultIds: ["old-property"],
  }]));

  render(<App initialProperties={properties.slice(0, 1)} />);

  expect(screen.getByRole("status")).toHaveTextContent("A newer active dataset snapshot is available for a saved search.");
});

test("keeps buyer criteria visible and records bounded result feedback", async () => {
  const user = userEvent.setup();
  render(<App initialProperties={properties.slice(0, 1)} />);

  await user.type(screen.getByRole("textbox", { name: "Must-have criteria" }), "waterfront");
  expect(screen.getByText("Must-have: waterfront")).toBeInTheDocument();

  await user.click(screen.getAllByRole("button", { name: "Open Property 1" })[0]);
  await user.click(screen.getByRole("button", { name: "Useful result" }));
  expect(screen.getByRole("status")).toHaveTextContent("Feedback saved in this browser.");
});
