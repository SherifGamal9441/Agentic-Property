import type { AffordabilityInput } from "./types";

export function calculateScenario(input: AffordabilityInput) {
  const values = Object.values(input);
  if (values.some((value) => !Number.isFinite(value) || value < 0)) throw new Error("Scenario values must be non-negative numbers.");
  if (input.deposit > input.price) throw new Error("Deposit cannot exceed the reported price.");
  if (input.years <= 0) throw new Error("Mortgage term must be positive.");
  const principal = input.price - input.deposit;
  const months = input.years * 12;
  const monthlyRate = input.annualRate / 100 / 12;
  const monthlyPayment = monthlyRate === 0
    ? principal / months
    : principal * monthlyRate * (1 + monthlyRate) ** months / ((1 + monthlyRate) ** months - 1);
  return {
    principal,
    monthlyPayment,
    cashAtPurchase: input.deposit + input.transfer + input.finance + input.moving,
    annualPropertyCost: input.annualService,
  };
}
