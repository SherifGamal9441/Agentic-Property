# Research: Premium Buyer Polish

## Decision: Keep buyer-decision state in the existing workspace

**Rationale**: The workspace already owns selected property, comparison, saved-search, and map state. Extending that state is smaller and less error-prone than introducing a store or backend persistence layer.

**Alternatives considered**: Global client store, account-backed saved research. Rejected: both exceed device-local scope and add privacy/auth work.

## Decision: Retain the current relative map

**Rationale**: Supplied coordinates support relative positioning, selection, and exact-coordinate grouping. The existing map matches the visual language and has no provider dependency.

**Alternatives considered**: Commercial map, public tile service, travel-time/amenity integration. Rejected: not needed for supplied listing evidence and could imply unsupported accuracy or introduce service obligations.

## Decision: Model shortlist separately from comparison

**Rationale**: A buyer may save many possibilities while comparing only one to four. Comparison can add directly for low friction, while the UI always explains the distinction.

**Alternatives considered**: One shared list. Rejected: it cannot satisfy separate actions or preserve a wider decision set.

## Decision: Use existing listing fields for sorting and confidence

**Rationale**: Fit score, price, size, coordinates, and location status already exist in the returned property contract. Missing values can remain visibly unreported.

**Alternatives considered**: New calculated market metrics. Rejected: no new source evidence is required for this buyer-interface iteration.
