# NYAYA SOVEREIGN ENFORCEMENT ENGINE

## PHILOSOPHY

The Sovereign Enforcement Engine is the constitutional law of the Nyaya AI system. It determines what the system may and may not do, regardless of requests, pressures, or circumstances. The engine operates on the principle that:

> **Nyaya may stop. Nyaya may escalate. Nyaya may refuse.**
> 
> **But Nyaya may NEVER act outside law, policy, or truth — even under pressure, ambiguity, or learning updates.**

## GUARANTEES

The enforcement engine provides these mathematical guarantees:

1. **Deterministic Behavior**: Same inputs always produce the same decisions
2. **No Hallucination Paths**: Every response passes through governance approval
3. **No Ungoverned Execution**: Every agent execution requires enforcement permission
4. **Explainable Decisions**: Every decision includes rule_id, policy_source, and reasoning
5. **Tamper Detection**: All decisions are cryptographically signed and hash-chained
6. **Refusal-First Logic**: When uncertain, the system blocks rather than risk violation

## FAILURE MODEL

The enforcement engine follows a fail-safe design:

- **Engine Crash/Timeout**: System defaults to BLOCK decision
- **Rule Evaluation Failure**: Falls back to conservative safety rules  
- **Signature Verification Failure**: Rejects the decision as invalid
- **Unknown Context**: Escalates to human oversight

## ALLOWED BEHAVIORS

The system may execute when enforcement returns:
- `ALLOW`: Normal execution proceeds
- `SOFT_REDIRECT`: Execution proceeds with modifications

## BLOCKED BEHAVIORS  

The system must halt when enforcement returns:
- `BLOCK`: Execution terminates immediately
- `ESCALATE`: Execution redirects to oversight/human review

## ENFORCEMENT DECISIONS

### ALLOW
- **Condition**: Request passes all safety and compliance checks
- **Action**: Normal execution proceeds
- **Proof**: Logged with cryptographic signature

### SOFT_REDIRECT  
- **Condition**: Request needs modification but is essentially valid
- **Action**: Execution proceeds with governance-specified modifications
- **Proof**: Logged with cryptographic signature

### BLOCK
- **Condition**: Request violates safety, compliance, or policy
- **Action**: Execution terminates immediately
- **Proof**: Blocked request logged with cryptographic signature

### ESCALATE
- **Condition**: Request requires human oversight or is ambiguous
- **Action**: Execution redirects to escalation procedures
- **Proof**: Escalation logged with cryptographic signature