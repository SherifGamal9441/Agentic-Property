# ADR 002: Deterministic scoring

**Status:** Accepted

Fit, coverage, suitability, and sort order are application logic. The LLM never calculates them. This makes hard conflicts, unknown fields, unsupported wishes, and arithmetic reproducible and testable.
