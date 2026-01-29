# NYAYA TRACE PROOF EXAMPLES

## EXAMPLE 1: ALLOW DECISION

```json
{
  "status": "allowed",
  "decision": "ALLOW",
  "trace_proof": {
    "decision_summary": {
      "decision": "ALLOW",
      "rule_id": "CONF-001",
      "policy_source": "System Safety",
      "reasoning_summary": "Confidence threshold met for general domain",
      "trace_id": "abc123-def456-ghi789",
      "timestamp": "2024-01-15T10:30:00Z",
      "proof_hash": "sha256:a1b2c3d4e5f6...",
      "metadata": {}
    },
    "cryptographic_signature": "hmac-sha256:signature123456abcdef...",
    "proof_hash": "sha256:a1b2c3d4e5f6...",
    "verification_data": {
      "algorithm": "HMAC-SHA256",
      "signing_key_used": "enforcement-primary-key",
      "timestamp": "2024-01-15T10:30:05Z"
    }
  },
  "enforcement_metadata": {
    "rule_id": "CONF-001",
    "policy_source": "System Safety", 
    "reasoning": "Confidence threshold met for general domain",
    "governance_approved": true
  }
}
```

## EXAMPLE 2: BLOCK DECISION

```json
{
  "status": "blocked",
  "reason": "governance enforced",
  "decision": "BLOCK",
  "trace_proof": {
    "decision_summary": {
      "decision": "BLOCK",
      "rule_id": "SAFETY-001",
      "policy_source": "System Safety",
      "reasoning_summary": "Request contains dangerous patterns that could compromise system integrity",
      "trace_id": "xyz987-wvu654-tsr321",
      "timestamp": "2024-01-15T11:45:22Z", 
      "proof_hash": "sha256:x1y2z3w4v5u6...",
      "metadata": {
        "matched_pattern": "ignore all rules"
      }
    },
    "cryptographic_signature": "hmac-sha256:blocksignature987654...",
    "proof_hash": "sha256:x1y2z3w4v5u6...",
    "verification_data": {
      "algorithm": "HMAC-SHA256", 
      "signing_key_used": "enforcement-primary-key",
      "timestamp": "2024-01-15T11:45:25Z"
    }
  },
  "enforcement_metadata": {
    "rule_id": "SAFETY-001",
    "policy_source": "System Safety",
    "reasoning": "Request contains dangerous patterns that could compromise system integrity",
    "governance_action": "blocking_dangerous_request"
  }
}
```

## EXAMPLE 3: ESCALATE DECISION

```json
{
  "status": "allowed",
  "decision": "ESCALATE",
  "trace_proof": {
    "decision_summary": {
      "decision": "ESCALATE", 
      "rule_id": "CONST-001",
      "policy_source": "Constitutional",
      "reasoning_summary": "Constitutional matter detected with insufficient confidence (0.6 < 0.8 threshold)",
      "trace_id": "con123-sti456-tut789",
      "timestamp": "2024-01-15T12:20:33Z",
      "proof_hash": "sha256:c1o2n3s4t5i6...",
      "metadata": {
        "domain": "constitutional",
        "confidence_before": 0.6,
        "threshold_required": 0.8
      }
    },
    "cryptographic_signature": "hmac-sha256:escalatesigconst123...",
    "proof_hash": "sha256:c1o2n3s4t5i6...",
    "verification_data": {
      "algorithm": "HMAC-SHA256",
      "signing_key_used": "enforcement-primary-key", 
      "timestamp": "2024-01-15T12:20:35Z"
    }
  },
  "enforcement_metadata": {
    "rule_id": "CONST-001",
    "policy_source": "Constitutional",
    "reasoning": "Constitutional matter detected with insufficient confidence (0.6 < 0.8 threshold)",
    "governance_action": "escalation_required"
  }
}
```

## EXAMPLE 4: RL UPDATE ALLOWED

```json
{
  "status": "recorded", 
  "trace_id": "rl456-update789-track123",
  "message": "Feedback recorded successfully",
  "enforcement_metadata": {
    "decision": "ALLOW",
    "rule_id": "GOVERNANCE-001",
    "policy_source": "Governance",
    "governance_approved": true
  },
  "provenance_chain": [{
    "decision_summary": {
      "decision": "ALLOW",
      "rule_id": "GOVERNANCE-001", 
      "policy_source": "Governance",
      "reasoning_summary": "RL feedback update permitted under governance rules",
      "trace_id": "rl456-update789-track123",
      "timestamp": "2024-01-15T13:15:44Z",
      "proof_hash": "sha256:r1l2u3p4d5a6...",
      "metadata": {
        "update_type": "feedback_learning",
        "rating": 5
      }
    },
    "cryptographic_signature": "hmac-sha256:rlupdatesig456...",
    "proof_hash": "sha256:r1l2u3p4d5a6...",
    "verification_data": {
      "algorithm": "HMAC-SHA256",
      "signing_key_used": "enforcement-primary-key",
      "timestamp": "2024-01-15T13:15:46Z"
    }
  }]
}
```

## EXAMPLE 5: RL UPDATE DENIED

```json
{
  "status": "blocked",
  "reason": "governance enforced", 
  "decision": "BLOCK",
  "trace_proof": {
    "decision_summary": {
      "decision": "BLOCK",
      "rule_id": "SAFETY-001",
      "policy_source": "System Safety",
      "reasoning_summary": "RL update blocked due to safety concerns with feedback pattern",
      "trace_id": "rlblocked999-feedback888-test777", 
      "timestamp": "2024-01-15T14:30:55Z",
      "proof_hash": "sha256:b1l2o3c4k5e6...",
      "metadata": {
        "update_type": "feedback_learning",
        "rating": 1,
        "feedback_content": "system is completely useless"
      }
    },
    "cryptographic_signature": "hmac-sha256:blockedrlsig789...",
    "proof_hash": "sha256:b1l2o3c4k5e6...",
    "verification_data": {
      "algorithm": "HMAC-SHA256",
      "signing_key_used": "enforcement-primary-key",
      "timestamp": "2024-01-15T14:30:57Z"
    }
  },
  "enforcement_metadata": {
    "rule_id": "SAFETY-001",
    "policy_source": "System Safety", 
    "reasoning": "RL update blocked due to safety concerns with feedback pattern",
    "governance_action": "rl_update_denied"
  }
}
```