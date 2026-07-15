# Research: Restore Buyer Experience

## Decision: Restore composition with existing CSS and components

**Rationale**: The regression came from replacing the visual hierarchy, not from a missing capability. Existing browser controls and CSS cover the reference composition without another design system.

**Alternatives considered**:

- Add a component or design-library dependency: rejected; restoration needs no new primitive.
- Reintroduce the old demo UI wholesale: rejected; it would restore synthetic claims and lose real-data features.

## Decision: Preserve real-data states inside reference layout

**Rationale**: Empty, loading, historical, and partial-data states must remain honest while sharing the same visual shell.

**Alternatives considered**:

- Separate landing and research applications: rejected; it creates duplicate state and a broken transition.
