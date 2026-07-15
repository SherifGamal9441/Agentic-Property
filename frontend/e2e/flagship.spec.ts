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

function property(area: string, beds: number, price: number, index = 1) {
  return { id: `${area}-${beds}-${index}`, title: `${area} Editorial Residence ${index}`, area, price: price - index * 10_000, currency: "AED", beds, baths: 2, property_type: "Apartments", furnishing: "Furnished", completion_status: "completed", year_of_completion: 2022, latitude: 25.1 + index * .001, longitude: 55.2 + index * .001, location_status: "exact", source_url: `https://example.test/listing-${index}`, source_name: "Captured listing source", observed_at: "2026-07-02", snapshot_id: "active-2026-07-02-v1", dataset_snapshot_at: "2026-07-02", data_status: "listing_snapshot", fit_score: 1, evidence_coverage: 1, suitability: "suitable", evaluations: [], matched_criteria: [area, `${beds} bedrooms`], conflicting_criteria: [], unknown_criteria: [], unsupported_criteria: [] };
}

async function routeRun(page: Page, query: string, area: string, beds: number, price: number, noResult = false) {
  const properties = noResult ? [] : [property(area, beds, price, 1), property(area, beds, price, 2)];
  await page.route("**/api/briefs/interpret", (route) => route.fulfill({ json: brief(query, area, beds, price) }));
  await page.route("**/api/runs", (route) => route.fulfill({ contentType: "text/event-stream", body: [
    `event: run_started\ndata: {"thread_id":"e2e","snapshot_id":"active-2026-07-02-v1"}\n\n`,
    `event: agent_step\ndata: {"node":"comparison_engine","label":"Evaluating criteria deterministically","status":"completed","duration_ms":4}\n\n`,
    `event: properties\ndata: ${JSON.stringify({ candidate_count: noResult ? 4 : 20, audited_count: noResult ? 4 : 20, total_matches: properties.length, shown_count: properties.length, properties })}\n\n`,
    `event: sources\ndata: {"items":[]}\n\n`,
    `event: guidance\ndata: ${JSON.stringify({ guidance: { version: 1, outcome: noResult ? "no_match" : "matches", best_match_id: properties[0]?.id || null, runner_up_id: properties[1]?.id || null, reasons: [], caveats: [], next_action: noResult ? "edit_brief" : "review_best_match" } })}\n\n`,
    noResult ? `event: relaxation_options\ndata: {"criteria":[{"criterion_id":"budget","resulting_match_count":4}]}\n\n` : "",
    `event: run_completed\ndata: {"route":"query_routing","data_source":"active","evidence_quality":"strong"}\n\n`,
  ].join("") }));
}

async function runQuery(page: Page, query: string) {
  await page.getByLabel("Describe your ideal Dubai home").fill(query);
  await page.getByRole("button", { name: "Find matching homes" }).click();
}

for (const [query, area, beds, price] of presets) {
  test(`preset completes the one-action live journey: ${area}`, async ({ page }) => {
    await routeRun(page, query, area, beds, price);
    await page.goto("/");
    await page.getByRole("button", { name: new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")) }).click();
    await page.getByRole("button", { name: "Find matching homes" }).click();
    await expect(page.getByRole("heading", { name: "2 homes meet your brief" })).toBeVisible();
    await expect(page.getByRole("button", { name: `${area} Editorial Residence 1 ↗` }).first()).toBeVisible();
    await expect(page.getByText("Confirm what Aizen understood")).toHaveCount(0);
    if (area === "Dubai Marina") await page.screenshot({ path: "../docs/assets/aizen-home.png", fullPage: true });
  });
}

test("no-result run asks before relaxation", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  await routeRun(page, query, area, beds, price, true);
  await page.goto("/");
  await runQuery(page, query);
  await expect(page.getByRole("heading", { name: "No exact snapshot match" })).toBeVisible();
  await expect(page.getByText("Aizen did not silently relax your brief.", { exact: false })).toBeVisible();
  await expect(page.getByText("4 resulting matches")).toBeVisible();
  await page.getByRole("button", { name: "Review this change" }).click();
  await expect(page.getByRole("dialog", { name: "Edit buyer brief" })).toBeVisible();
});

test("top matches open a synchronized comparison matrix", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  await routeRun(page, query, area, beds, price);
  await page.goto("/");
  await runQuery(page, query);
  await page.getByRole("button", { name: "Compare top matches" }).click();
  await expect(page.getByLabel("Property comparison")).toBeVisible();
  await expect(page.getByRole("columnheader", { name: new RegExp(`${area} Editorial Residence 1`) })).toBeVisible();
  await expect(page.getByRole("rowheader", { name: "Evidence coverage" })).toBeVisible();
});

test("decision state survives refresh and dossier has print state", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  await routeRun(page, query, area, beds, price);
  await page.goto("/");
  await runQuery(page, query);
  await page.getByRole("button", { name: `Add ${area} Editorial Residence 1 to shortlist` }).click();
  await page.reload();
  await expect(page.getByText("1 shortlisted")).toBeVisible();
  await page.getByRole("button", { name: "Open buyer dossier" }).click();
  await page.emulateMedia({ media: "print" });
  await expect(page.getByRole("heading", { name: "Buyer dossier" })).toBeVisible();
});

test("recent search reruns the live endpoint", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  let runCount = 0;
  await routeRun(page, query, area, beds, price);
  page.on("request", (request) => { if (request.url().endsWith("/api/runs")) runCount += 1; });
  await page.goto("/");
  await runQuery(page, query);
  await page.getByText("Recent searches").scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: new RegExp(query) }).last().click();
  await expect.poll(() => runCount).toBe(2);
});

test("320px mobile has no page overflow and Escape closes evidence", async ({ page }) => {
  const [query, area, beds, price] = presets[0];
  await page.setViewportSize({ width: 320, height: 760 });
  await routeRun(page, query, area, beds, price);
  await page.goto("/");
  await runQuery(page, query);
  await expect(page.getByRole("heading", { name: "2 homes meet your brief" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Review best match" }).click();
  await expect(page.getByRole("dialog", { name: "Property evidence" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Property evidence" })).toBeHidden();
});
