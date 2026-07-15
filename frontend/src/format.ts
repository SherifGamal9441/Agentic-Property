export const money = (value: number | null | undefined) => value == null
  ? "Not reported"
  : new Intl.NumberFormat("en-AE", { style: "currency", currency: "AED", maximumFractionDigits: 0 }).format(value);

export const percent = (value: number | null | undefined) => value == null ? "Unknown" : `${Math.round(value * 100)}%`;
