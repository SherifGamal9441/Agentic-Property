import { expect, test, type Page } from "@playwright/test";

const presets = [
  ["Ready 2BR in Dubai Marina under AED 2M, no off-plan.", "Dubai Marina", 2, 1_800_000],
  ["Ready 3BR in Al Furjan under AED 3M.", "Al Furjan", 3, 2_700_000],
  ["Furnished 1BR in Business Bay under AED 1.5M.", "Business Bay", 1, 1_300_000],
] as const;

function brief(query: string, area: string, beds: number, price: number) {
  return { version: 1, mode: "property_search", original_query: query, currency: "AED", criteria: [
    { id: "area", label: area, priority: "must_have", field: "area", operator: "contains", value: area, verifiable: true },
    { id: "beds", label: `${beds} bedrooms`, priority: "must_have", field: "bedrooms", operator: "eq", value: beds, verifiable: true },
    { id: "budget", label: `Under AED ${price}`, priority: "must_have", field: "price", operator: "lte", value: price, verifiable: true },
  ] };
}

function property(area: string, beds: number, price: number) {
  return { id: `${area}-${beds}`, title: `${area} Editorial Residence`, area, price, currency: "AED", beds, baths: 2, property_type: "Apartments", furnishing: "Furnished", completion_status: "completed", year_of_completion: 2022, latitude: 25.1, longitude: 55.2, location_status: "exact", source_url: "https://example.test/listing", source_name: "Captured listing source", observed_at: "2026-07-02", snapshot_id: "active-2026-07-02-v1", dataset_snapshot_at: "2026-07-02", data_status: "listing_snapshot", fit_score: 1, evidence_coverage: 1, suitability: "suitable", evaluations: [], matched_criteria: [area, `${beds} bedrooms`], conflicting_criteria: [], unknown_criteria: [], unsupported_criteria: [] };
}

async function routeRun(page: Page, query: string, area: string, beds: number, price: number, noResult = false) {
  await page.route("**/api/briefs/interpret", (route) => route.fulfill({ json: brief(query, area, beds, price) }));
  await page.route("**/api/runs", (route) => route.fulfill({ contentType: "text/event-stream", body: [
    `event: run_started\ndata: {"thread_id":"e2e","snapshot_id":"active-2026-07-02-v1"}\n\n`,
    `event: agent_step\ndata: {"node":"comparison_engine","label":"Evaluating criteria deterministically","status":"completed","duration_ms":4}\n\n`,
    `event: properties\ndata: ${JSON.stringify({ total_matches: noResult ? 0 : 1, shown_count: noResult ? 0 : 1, properties: noResult ? [] : [property(area, beds, price)] })}\n\n`,
    `event: sources\ndata: {"items":[]}\n\n`,
    noResult ? `event: relaxation_options\ndata: {"criteria":[{"criterion_id":"budget","resulting_match_count":4}]}\n\n` : "",
    `event: run_completed\ndata: {"route":"query_routing","data_source":"active","evidence_quality":"strong"}\n\n`,
  ].join("") }));
}

for (const [query, area, beds, price] of presets) {
  test(`preset completes the confirm-first live journey: ${area}`, async ({ page }) => {
    await routeRun(page, query, area, beds, price);
    await page.goto("/");
    await page.getByRole("button", { name: new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")) }).click();
    await page.getByRole("button", { name: "Interpret my brief" }).click();
    await expect(page.getByRole("heading", { name: "Confirm what Aizen understood" })).toBeVisible();
    await page.getByRole("button", { name: "Confirm & search" }).click();
    await expect(page.getByRole("article", { name: `${area} Editorial Residence` })).toBeVisible();
    if (area === "Dubai Marina") {
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.waitForTimeout(150);
      await page.screenshot({ path: "../docs/assets/aizen-home.png" });
    }
  });
}

test("no-result run asks before relaxation", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  await routeRun(page, query, area, beds, price, true);
  await page.goto("/");
  await page.getByLabel("Describe your ideal Dubai home").fill(query);
  await page.getByRole("button", { name: "Interpret my brief" }).click();
  await page.getByRole("button", { name: "Confirm & search" }).click();
  await expect(page.getByText("Aizen did not silently relax your brief.")).toBeVisible();
  await expect(page.getByText("4 resulting matches")).toBeVisible();
});

test("decision state survives refresh and dossier has print state", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  await routeRun(page, query, area, beds, price);
  await page.goto("/");
  await page.getByLabel("Describe your ideal Dubai home").fill(query);
  await page.getByRole("button", { name: "Interpret my brief" }).click();
  await page.getByRole("button", { name: "Confirm & search" }).click();
  await page.getByRole("button", { name: `Add ${area} Editorial Residence to shortlist` }).click();
  await page.reload();
  await expect(page.getByText("1 shortlisted")).toBeVisible();
  await page.getByRole("button", { name: "Open buyer dossier" }).click();
  await page.emulateMedia({ media: "print" });
  await expect(page.getByRole("heading", { name: "Buyer dossier" })).toBeVisible();
});

test("320px mobile has no page overflow and Escape closes evidence", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  await page.setViewportSize({ width: 320, height: 760 });
  await routeRun(page, query, area, beds, price);
  await page.goto("/");
  await page.getByLabel("Describe your ideal Dubai home").fill(query);
  await page.getByRole("button", { name: "Interpret my brief" }).click();
  await page.getByRole("button", { name: "Confirm & search" }).click();
  await expect(page.getByRole("article", { name: `${area} Editorial Residence` })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Review evidence" }).click();
  await expect(page.getByRole("dialog", { name: "Property evidence" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Property evidence" })).toBeHidden();
});
