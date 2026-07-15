# ADR 001: Structured buyer briefs

**Status:** Accepted

Natural-language requests are ambiguous and browser controls previously became labelled prompt text. A live model may extract a versioned `BuyerBrief`, but Pydantic validates it before search and downstream nodes do not reinterpret its values. The original blocking confirmation interaction is superseded by ADR 010; the structured contract remains authoritative.
