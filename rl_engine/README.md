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
  "outcome_valid": bool,  // From Raj's validation
  "timestamp": str
}
```

## Hardening Features

### Decay Model
- Time-weighted decay with 30-day half-life for confidence adjustments
- Historical learning fades automatically
- Decay applied deterministically on read/update

### Confidence Anchoring
- Learning anchored to confidence_before (from Aditya)
- Legal correctness from Raj takes primary weight
- UI feedback has secondary weight only

### Anomaly Detection
- Repeated extreme feedback detection
- Suspicious pattern recognition
- Engagement abuse pattern detection
- Anomalous signals are rejected, not softened

### Protection Mechanisms
- Absolute cap on confidence change per update (0.03)
- Volatility caps to prevent oscillation
- UI vs Raj priority rules enforced

### UI vs Raj Priority Rules
- Raj says invalid → No learning occurs
- Raj says valid + UI negative → UI ignored/down-weighted
- Raj says invalid + UI positive → UI ignored
- UI anomalous → No learning occurs

## Behavior

- Country-agnostic learning that works for India, UAE, UK and future jurisdictions
- Bounded confidence adjustments within [0.0, 1.0]
- Stability factors that reduce volatility over time
- Thread-safe operations
- Persistent learning memory
- Time-decay protection against drifting
- Anomaly detection to prevent poisoning by malicious users
- Raj's legal validation always dominates UI feedback