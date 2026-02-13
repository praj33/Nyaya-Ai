# Schema Notes — Procedural Intelligence v1.1

This dataset follows a uniform, additive schema across all jurisdictions and domains.

## Core Principles
- No breaking changes across files
- All procedures follow a step-based structure
- Conditional branching is explicit
- Outcomes, risks, and costs are metadata only

## Mandatory Fields
- country
- domain
- authority
- steps[]
- conditional_branches (where applicable)
- outcome_intelligence
- cost_effort
- risk_flags

## Design Constraints
- No legal advice
- No outcome guarantees
- No probabilistic predictions beyond safe ranges
- Jurisdiction-correct terminology only

This schema is ingestion-ready and deterministic.
