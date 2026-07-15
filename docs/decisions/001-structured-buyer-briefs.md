# ADR 001: Structured buyer briefs

**Status:** Accepted

Natural-language requests are ambiguous and browser controls previously became labelled prompt text. A live model may extract a versioned `BuyerBrief`, but Pydantic validates it and the buyer must edit/confirm it before search. Confirmed values are not reinterpreted downstream.
