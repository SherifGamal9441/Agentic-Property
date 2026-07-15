import { describe, expect, test } from "vitest";

import { calculateScenario } from "./finance";

describe("affordability scenarios", () => {
  test("uses the standard amortization formula", () => {
    const result = calculateScenario({ price: 1_000_000, deposit: 200_000, annualRate: 4.5, years: 25, transfer: 0, finance: 0, moving: 0, annualService: 0 });

    expect(result.monthlyPayment).toBeCloseTo(4_446.65, 1);
  });

  test("handles zero interest explicitly", () => {
    const result = calculateScenario({ price: 1_000_000, deposit: 100_000, annualRate: 0, years: 25, transfer: 20_000, finance: 5_000, moving: 5_000, annualService: 12_000 });

    expect(result.monthlyPayment).toBe(3_000);
    expect(result.cashAtPurchase).toBe(130_000);
  });

  test("rejects impossible or silently incomplete scenarios", () => {
    expect(() => calculateScenario({ price: 1_000_000, deposit: 1_100_000, annualRate: 4, years: 25, transfer: 0, finance: 0, moving: 0, annualService: 0 })).toThrow("Deposit");
    expect(() => calculateScenario({ price: 1_000_000, deposit: 100_000, annualRate: 4, years: 0, transfer: 0, finance: 0, moving: 0, annualService: 0 })).toThrow("term");
  });
});
