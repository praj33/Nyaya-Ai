# Nyaya AI Reinforcement Learning Engine

Internal reinforcement learning backbone that silently improves system performance over time.

## Core Functions

- `update_learning(signal_payload: Dict)` - Processes learning signals and updates confidence adjustments
- `get_adjusted_confidence(case_context: Dict)` - Returns confidence adjusted based on learned patterns

## Learning Signals

Accepts signals with the following schema:
```
{
  "case_id": str,
  "country": str,
  "domain": str,
  "procedure_id": str,
  "confidence_before": float,
  "user_feedback": "positive|neutral|negative",
  "outcome_tag": "resolved|pending|escalated|wrong",
  "timestamp": int
}
```

## Behavior

- Country-agnostic learning that works for India, UAE, UK and future jurisdictions
- Bounded confidence adjustments within [0.0, 1.0]
- Stability factors that reduce volatility over time
- Thread-safe operations
- Persistent learning memory