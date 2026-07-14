import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";

import App, { demoProperties } from "./App";

test("opens a selected property in the intelligence drawer", async () => {
  const user = userEvent.setup();
  render(<App />);

  await user.click(screen.getByRole("button", { name: "Marina Vista Residence" }));

  const drawer = screen.getByRole("complementary", { name: /property intelligence/i });
  expect(drawer).toHaveTextContent(
    "Marina Vista Residence",
  );
  expect(within(drawer).getByText(/94% match/i)).toBeInTheDocument();
});

test("returns focus to the property trigger when the drawer closes", async () => {
  const user = userEvent.setup();
  render(<App />);

  const trigger = screen.getByRole("button", { name: "Marina Vista Residence" });
  await user.click(trigger);
  await user.click(screen.getByRole("button", { name: /close property intelligence/i }));

  await waitFor(() => expect(trigger).toHaveFocus());
});

test("dismisses property intelligence with Escape", async () => {
  const user = userEvent.setup();
  render(<App />);

  const trigger = screen.getByRole("button", { name: "Marina Vista Residence" });
  await user.click(trigger);
  await user.keyboard("{Escape}");

  expect(screen.queryByRole("complementary", { name: /property intelligence/i })).not.toBeInTheDocument();
  await waitFor(() => expect(trigger).toHaveFocus());
});

test("labels historical properties as market signals", async () => {
  const user = userEvent.setup();
  const historicalProperty = {
    ...demoProperties[0],
    data_intent: "insights_only" as const,
    data_source: "historical",
    id: "historical-marina-vista",
    title: "Marina Historical Signal",
  };
  render(<App initialProperties={[historicalProperty]} />);

  await user.click(screen.getByRole("button", { name: "Marina Historical Signal" }));

  expect(screen.getByRole("complementary", { name: /property intelligence/i })).toHaveTextContent(
    "Historical market signal",
  );
});

test("renders a property with no reported size without crashing", () => {
  const missingSizeProperty = {
    ...demoProperties[0],
    title: "Size pending",
    size_sqft: null as unknown as number,
  };

  render(<App initialProperties={[missingSizeProperty]} />);

  expect(screen.getByText("—")).toBeInTheDocument();
});

test("limits comparison to three properties and explains the limit", async () => {
  const user = userEvent.setup();
  const comparisonProperties = Array.from({ length: 4 }, (_, index) => ({
    ...demoProperties[index % demoProperties.length],
    id: `comparison-${index}`,
    title: `Comparison home ${index + 1}`,
  }));
  render(<App initialProperties={comparisonProperties} />);

  for (const button of screen.getAllByRole("button", { name: "Compare" })) {
    await user.click(button);
  }

  expect(screen.getByRole("status")).toHaveTextContent("Compare up to three homes at a time.");
  expect(screen.getByRole("region", { name: /comparison shortlist/i })).toHaveTextContent("Comparison home 3");
});

test("opens the corresponding property from a map pin", async () => {
  const user = userEvent.setup();
  render(<App />);

  const map = screen.getByLabelText("Dubai property map");
  await user.click(within(map).getByRole("button", { name: "Open Harbour Cove Apartment" }));

  expect(screen.getByRole("complementary", { name: /property intelligence/i })).toHaveTextContent(
    "Harbour Cove Apartment",
  );
});
