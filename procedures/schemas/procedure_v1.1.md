# Procedural Intelligence Schema v1.1

## Purpose
This schema extends the existing procedural datasets (v1.0) with
decision-grade intelligence that enables legal reasoning, outcome
simulation, and procedural risk awareness.

The upgrade is additive and backward-compatible.

## Compatibility
- Existing v1.0 procedure JSONs remain valid
- All new fields are optional
- No existing fields are removed or renamed

## New Step-Level Fields (Optional)

### 1. Conditional Branching
Defines decision paths based on procedural outcomes.

```json
"conditional_branches": [
  {
    "condition": "Bail granted",
    "next_step": "Release on conditions",
    "effect": "Accused released pending trial"
  }
]
