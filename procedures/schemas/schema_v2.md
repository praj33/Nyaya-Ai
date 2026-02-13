# Procedural Intelligence Schema v2.0

## Purpose
Schema v2.0 upgrades procedural datasets from descriptive flows
to executable procedural intelligence consumable by:
- Nyaya Core reasoning engine
- Reinforcement Learning systems
- Backend orchestration logic
- Procedural UI state machines

This schema introduces execution semantics without legal advice
or interpretive reasoning.

---

## Versioning
- dataset_version: "2.0"
- backward compatible with v1.1
- v1.1 files remain frozen

---

## Core Canonical Fields (v2.0)

### 1. canonical_step
Represents the procedural state.
Must map to a deterministic system node.

Examples:
- CRIME_REPORTING
- PRE_TRIAL_RELEASE_DECISION
- SETTLEMENT_ATTEMPT
- TRIAL
- JUDGMENT
- APPEAL

---

### 2. canonical_outcome
Represents the result of a step transition.

Examples:
- RELEASE_GRANTED
- DETENTION_ORDERED
- SETTLEMENT_REACHED
- CASE_DISMISSED
- ESCALATION_TRIGGERED

---

### 3. probability_range
Safe outcome bands (non-predictive).

Structure:
```json
{ "min": 0.2, "max": 0.6 }
