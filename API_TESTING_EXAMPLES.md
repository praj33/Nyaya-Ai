# API Testing Examples - Nyaya AI

## Base URL
```
http://localhost:8000
```

## 1. Health Check
**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "nyaya-api-gateway"
}
```

---

## 2. Root Information
**GET** `/`

**Response:**
```json
{
  "service": "Nyaya Legal AI API Gateway",
  "version": "1.0.0",
  "description": "Sovereign-compliant multi-agent legal intelligence platform",
  "endpoints": {
    "query": "POST /nyaya/query",
    "multi_jurisdiction": "POST /nyaya/multi_jurisdiction",
    "explain_reasoning": "POST /nyaya/explain_reasoning",
    "feedback": "POST /nyaya/feedback",
    "trace": "GET /nyaya/trace/{trace_id}",
    "procedure_analyze": "POST /nyaya/procedures/analyze",
    "procedure_summary": "GET /nyaya/procedures/summary/{country}/{domain}",
    "evidence_assess": "POST /nyaya/procedures/evidence/assess",
    "failure_analyze": "POST /nyaya/procedures/failure/analyze",
    "procedure_compare": "POST /nyaya/procedures/compare",
    "procedure_list": "GET /nyaya/procedures/list",
    "procedure_schemas": "GET /nyaya/procedures/schemas",
    "health": "GET /health",
    "docs": "GET /docs"
  }
}
```

---

## 3. List Available Procedures
**GET** `/nyaya/procedures/list`

**Response:**
```json
{
  "available_procedures": {
    "india": ["criminal", "civil", "family", "consumer_commercial"],
    "uae": ["criminal", "civil", "family", "consumer_commercial"],
    "uk": ["criminal", "civil", "family", "consumer_commercial"],
    "ksa": ["criminal", "civil", "family", "consumer_commercial"]
  },
  "total_countries": 4,
  "trace_id": "uuid-string"
}
```

---

## 4. Get Procedure Summary
**GET** `/nyaya/procedures/summary/india/criminal`

**Response:**
```json
{
  "country": "india",
  "domain": "criminal",
  "last_verified": "2025-01",
  "total_steps": 9,
  "authorities": ["Police", "Magistrate Court", "Sessions Court", "High Court", "Supreme Court"],
  "timelines": {
    "best_case": "6–12 months",
    "average": "1–3 years",
    "worst_case": "5+ years"
  },
  "key_steps": [
    {
      "step": 1,
      "title": "Filing of FIR",
      "canonical_step": "CRIME_REPORTING"
    },
    {
      "step": 2,
      "title": "Investigation",
      "canonical_step": "INVESTIGATION"
    }
  ],
  "sources": [...]
}
```

---

## 5. Analyze Procedure
**POST** `/nyaya/procedures/analyze`

**Request Body:**
```json
{
  "country": "india",
  "domain": "criminal",
  "current_step": "CRIME_REPORTING"
}
```

**Response:**
```json
{
  "country": "india",
  "domain": "criminal",
  "procedure_overview": {
    "authorities": ["Police", "Magistrate Court", "Sessions Court"],
    "total_steps": 9,
    "timelines": {
      "best_case": "6–12 months",
      "average": "1–3 years",
      "worst_case": "5+ years"
    },
    "documents_required": ["FIR", "Police case diary", "Charge sheet"]
  },
  "steps": [...],
  "escalation_paths": [...],
  "current_step_analysis": {
    "step_number": 1,
    "title": "Filing of FIR",
    "canonical_step": "CRIME_REPORTING",
    "description": "Information relating to the commission of a cognizable offence is recorded by the police under Section 154 of the CrPC.",
    "actor": "Police"
  }
}
```

---

## 6. Assess Evidence Readiness
**POST** `/nyaya/procedures/evidence/assess`

**Request Body:**
```json
{
  "canonical_step": "CRIME_REPORTING",
  "available_documents": ["complaint_or_information", "identity_proof"]
}
```

**Response:**
```json
{
  "evidence_state": "EVIDENCE_COMPLETE",
  "mandatory_documents": ["complaint_or_information", "identity_proof"],
  "available_documents": ["complaint_or_information", "identity_proof"],
  "missing_documents": [],
  "confidence_penalty": 0.0,
  "readiness_percentage": 100.0
}
```

**Example with Missing Documents:**
```json
{
  "canonical_step": "CRIME_REPORTING",
  "available_documents": ["complaint_or_information"]
}
```

**Response:**
```json
{
  "evidence_state": "EVIDENCE_PARTIAL",
  "mandatory_documents": ["complaint_or_information", "identity_proof"],
  "available_documents": ["complaint_or_information"],
  "missing_documents": ["identity_proof"],
  "confidence_penalty": -0.3,
  "readiness_percentage": 50.0
}
```

---

## 7. Analyze Failure Risk
**POST** `/nyaya/procedures/failure/analyze`

**Request Body:**
```json
{
  "failure_code": "MISSING_MANDATORY_DOCUMENTS"
}
```

**Response:**
```json
{
  "failure_code": "MISSING_MANDATORY_DOCUMENTS",
  "failure_type": "COMPLAINANT_FAILURE",
  "description": "Mandatory documents not filed or submitted",
  "recoverable": true,
  "severity": "Medium"
}
```

**Other Failure Codes to Try:**
- `NON_APPEARANCE_BY_COMPLAINANT`
- `JURISDICTION_REJECTED`
- `LIMITATION_PERIOD_EXPIRED`
- `SERVICE_OF_NOTICE_FAILED`

---

## 8. Compare Procedures Across Countries
**POST** `/nyaya/procedures/compare`

**Request Body:**
```json
{
  "countries": ["india", "uae", "uk"],
  "domain": "criminal"
}
```

**Response:**
```json
{
  "domain": "criminal",
  "countries": ["india", "uae", "uk"],
  "procedures": {
    "india": {
      "country": "india",
      "domain": "criminal",
      "total_steps": 9,
      "timelines": {...},
      "key_steps": [...]
    },
    "uae": {
      "country": "uae",
      "domain": "criminal",
      "total_steps": 8,
      "timelines": {...},
      "key_steps": [...]
    },
    "uk": {
      "country": "uk",
      "domain": "criminal",
      "total_steps": 10,
      "timelines": {...},
      "key_steps": [...]
    }
  }
}
```

---

## 9. Get All Schemas
**GET** `/nyaya/procedures/schemas`

**Response:**
```json
{
  "canonical_taxonomy": {
    "canonical_steps": {
      "CRIME_REPORTING": "Initial reporting of alleged offence",
      "INVESTIGATION": "Fact-finding and evidence collection by authorities",
      ...
    },
    "canonical_outcomes": {...},
    "canonical_domains": {...}
  },
  "evidence_readiness": {
    "version": "2.0",
    "canonical_evidence_states": {...},
    "confidence_penalties": {...},
    "mandatory_documents_by_step": {...}
  },
  "failure_paths": {
    "version": "2.0",
    "canonical_failure_types": {...},
    "failure_states": [...]
  },
  "system_compliance": {
    "version": "2.0",
    "dataset_metadata": {...},
    "integrity_fields": {...}
  },
  "trace_id": "uuid-string"
}
```

---

## 10. Legal Query (with Procedure Intelligence)
**POST** `/nyaya/query`

**Request Body:**
```json
{
  "query": "What are the steps for filing a criminal complaint in India?",
  "jurisdiction_hint": "India",
  "domain_hint": "criminal",
  "user_context": {
    "role": "citizen",
    "confidence_required": true
  }
}
```

**Response:**
```json
{
  "domain": "criminal",
  "jurisdiction": "IN",
  "confidence": 0.85,
  "legal_route": ["jurisdiction_router_agent", "india_legal_agent"],
  "constitutional_articles": [],
  "provenance_chain": [],
  "reasoning_trace": {
    "routing_decision": {...},
    "agent_processing": {...},
    "procedure_intelligence": {
      "total_steps": 9,
      "timelines": {
        "best_case": "6–12 months",
        "average": "1–3 years",
        "worst_case": "5+ years"
      },
      "authorities": ["Police", "Magistrate Court", "Sessions Court"],
      "key_steps": [...]
    }
  },
  "trace_id": "uuid-string"
}
```

---

## 11. Multi-Jurisdiction Query
**POST** `/nyaya/multi_jurisdiction`

**Request Body:**
```json
{
  "query": "What are the rights of employees?",
  "jurisdictions": ["India", "UK", "UAE"]
}
```

**Response:**
```json
{
  "comparative_analysis": {
    "India": {...},
    "UK": {...},
    "UAE": {...}
  },
  "confidence": 0.78,
  "trace_id": "uuid-string"
}
```

---

## Testing with cURL

### Windows PowerShell
```powershell
# Health Check
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET

# List Procedures
Invoke-WebRequest -Uri "http://localhost:8000/nyaya/procedures/list" -Method GET

# Analyze Procedure
$body = @{
    country = "india"
    domain = "criminal"
    current_step = "CRIME_REPORTING"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/nyaya/procedures/analyze" -Method POST -Body $body -ContentType "application/json"
```

### Command Prompt (using curl)
```bash
# Health Check
curl http://localhost:8000/health

# List Procedures
curl http://localhost:8000/nyaya/procedures/list

# Analyze Procedure
curl -X POST http://localhost:8000/nyaya/procedures/analyze -H "Content-Type: application/json" -d "{\"country\":\"india\",\"domain\":\"criminal\",\"current_step\":\"CRIME_REPORTING\"}"
```

---

## Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Health Check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# List Procedures
response = requests.get(f"{BASE_URL}/nyaya/procedures/list")
print(response.json())

# Analyze Procedure
payload = {
    "country": "india",
    "domain": "criminal",
    "current_step": "CRIME_REPORTING"
}
response = requests.post(f"{BASE_URL}/nyaya/procedures/analyze", json=payload)
print(response.json())

# Assess Evidence
payload = {
    "canonical_step": "CRIME_REPORTING",
    "available_documents": ["complaint_or_information", "identity_proof"]
}
response = requests.post(f"{BASE_URL}/nyaya/procedures/evidence/assess", json=payload)
print(response.json())
```

---

## Quick Test Sequence

1. **Start Server**: Run `start_backend.bat`
2. **Health Check**: `curl http://localhost:8000/health`
3. **Open Swagger**: http://localhost:8000/docs
4. **Test Each Endpoint**: Use Swagger UI "Try it out" feature
5. **Verify Responses**: Check all responses return valid JSON

---

**Note**: All endpoints return JSON. Use Swagger UI at http://localhost:8000/docs for the easiest testing experience.
