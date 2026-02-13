# Nyaya AI - Integrated Legal Intelligence Platform

## 🔍 System Overview

Nyaya AI is a unified sovereign-compliant multi-agent legal intelligence platform that combines:
- **Legal Query Processing**: Multi-jurisdictional legal analysis across India, UK, UAE, and KSA
- **Procedure Intelligence**: Structured legal procedure datasets with step-by-step guidance
- **Sovereign Enforcement**: Complete audit trail with cryptographic signing
- **Reinforcement Learning**: Continuous improvement through user feedback

## 🏗️ Integrated Architecture

### Core Components

1. **API Gateway (FastAPI)** - Entry point for all requests
2. **Sovereign Agents** - Legal, Constitutional, and Jurisdiction Router agents
3. **Jurisdiction Router** - Intelligent routing to appropriate legal systems
4. **Enforcement Engine** - Governance and compliance controls
5. **Procedure Intelligence** - Legal procedure analysis and guidance
6. **RL Engine** - Reinforcement learning for continuous improvement
7. **Provenance Chain** - Immutable audit trail with cryptographic signing
8. **Data Bridge** - Legal dataset loader and validator

### New: Procedure Intelligence Module

The integrated system now includes comprehensive legal procedure datasets covering:
- **4 Jurisdictions**: India, UAE, UK, Saudi Arabia (KSA)
- **4 Legal Domains**: Criminal, Civil, Family, Consumer/Commercial
- **Canonical Taxonomy**: Standardized procedure steps and outcomes
- **Evidence Readiness**: Document requirements and confidence penalties
- **Failure Path Intelligence**: Risk analysis and recoverability assessment

## 📡 API Endpoints

### Legal Query Endpoints

#### POST `/nyaya/query`
Execute a single-jurisdiction legal query with procedure intelligence.

**Request:**
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

#### POST `/nyaya/multi_jurisdiction`
Execute parallel legal analysis across multiple jurisdictions.

#### POST `/nyaya/explain_reasoning`
Explain reasoning without re-executing agents.

#### POST `/nyaya/feedback`
Submit RL feedback with sovereign enforcement.

#### GET `/nyaya/trace/{trace_id}`
Get full sovereign audit trail.

### Procedure Intelligence Endpoints

#### POST `/nyaya/procedures/analyze`
Analyze a legal procedure for a specific country and domain.

**Request:**
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
    "documents_required": ["FIR", "Police case diary", "Charge sheet", ...]
  },
  "steps": [...],
  "escalation_paths": [...],
  "current_step_analysis": {
    "step_number": 1,
    "title": "Filing of FIR",
    "canonical_step": "CRIME_REPORTING",
    "description": "Information relating to the commission of a cognizable offence...",
    "actor": "Police"
  }
}
```

#### GET `/nyaya/procedures/summary/{country}/{domain}`
Get a summary of a legal procedure.

**Example:** `GET /nyaya/procedures/summary/india/criminal`

#### POST `/nyaya/procedures/evidence/assess`
Assess evidence readiness for a given procedural step.

**Request:**
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

#### POST `/nyaya/procedures/failure/analyze`
Analyze failure risk for a given failure code.

**Request:**
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

#### POST `/nyaya/procedures/compare`
Compare procedures across multiple countries.

**Request:**
```json
{
  "countries": ["india", "uae", "uk"],
  "domain": "criminal"
}
```

#### GET `/nyaya/procedures/list`
List all available procedures by country and domain.

#### GET `/nyaya/procedures/schemas`
Get all available schemas (canonical taxonomy, evidence readiness, failure paths, system compliance).

### System Endpoints

#### GET `/health`
Health check endpoint.

#### GET `/`
Root endpoint with API information and all available endpoints.

## 🚀 Running the Backend

### Prerequisites
- Python 3.7+
- FastAPI
- Uvicorn

### Installation

1. Navigate to the Nyaya_AI directory:
```bash
cd C:\Users\Gauri\Desktop\Nyaya-Ai\Nyaya_AI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Start the Server

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Or simply:
```bash
python api/main.py
```

The server will start at `http://localhost:8000`

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root Info**: http://localhost:8000/

## 📊 Data Structure

### Procedure Data Location
```
Nyaya_AI/
├── procedures/
│   ├── data/
│   │   ├── india/
│   │   │   ├── criminal.json
│   │   │   ├── civil.json
│   │   │   ├── family.json
│   │   │   └── consumer_commercial.json
│   │   ├── uae/
│   │   ├── uk/
│   │   └── ksa/
│   ├── schemas/
│   │   ├── canonical_taxonomy_v1.2.json
│   │   ├── evidence_readiness_v2.json
│   │   ├── failure_paths_v2.json
│   │   └── system_compliance_v2.json
│   ├── loader.py
│   ├── intelligence.py
│   └── integration.py
```

### Legal Data Location
```
Nyaya_AI/
├── db/
│   ├── indian_law_dataset.json
│   ├── uae_law_dataset.json
│   ├── uk_law_dataset.json
│   ├── bns_sections.json
│   ├── ipc_sections.json
│   └── ... (other legal datasets)
```

## 🔐 Security & Compliance

- **HMAC-SHA256 Signing**: All events cryptographically signed
- **Hash Chain Ledger**: Immutable audit trail
- **Nonce Protection**: Prevents replay attacks
- **Enforcement Engine**: Governance controls on all operations
- **Provenance Chain**: Complete traceability of all decisions

## 🎯 Key Features

### 1. Unified Legal Intelligence
- Single API for legal queries and procedure guidance
- Automatic enrichment of legal responses with procedure context
- Cross-jurisdictional comparison capabilities

### 2. Procedure Intelligence
- Step-by-step legal procedure guidance
- Evidence readiness assessment
- Failure risk analysis
- Timeline and cost estimates
- Escalation path mapping

### 3. Sovereign Compliance
- All operations logged and signed
- Complete audit trail
- Deterministic governance decisions
- Non-advisory, source-based information only

### 4. Continuous Learning
- RL engine for performance improvement
- User feedback integration
- Confidence scoring and adjustment

## 📝 Example Use Cases

### Use Case 1: Filing a Criminal Complaint
```python
# Step 1: Query legal requirements
POST /nyaya/query
{
  "query": "How do I file a criminal complaint in India?",
  "jurisdiction_hint": "India",
  "domain_hint": "criminal",
  "user_context": {"role": "citizen", "confidence_required": true}
}

# Step 2: Get detailed procedure
POST /nyaya/procedures/analyze
{
  "country": "india",
  "domain": "criminal",
  "current_step": "CRIME_REPORTING"
}

# Step 3: Assess evidence readiness
POST /nyaya/procedures/evidence/assess
{
  "canonical_step": "CRIME_REPORTING",
  "available_documents": ["complaint_or_information"]
}
```

### Use Case 2: Cross-Jurisdictional Comparison
```python
# Compare criminal procedures across jurisdictions
POST /nyaya/procedures/compare
{
  "countries": ["india", "uae", "uk"],
  "domain": "criminal"
}
```

### Use Case 3: Risk Assessment
```python
# Analyze failure risk
POST /nyaya/procedures/failure/analyze
{
  "failure_code": "LIMITATION_PERIOD_EXPIRED"
}
```

## 🤝 Integration Points

### For Frontend Developers (Hrujul)
- All endpoints return standardized JSON responses
- Procedure intelligence automatically enriches legal query responses
- Separate endpoints for detailed procedure analysis
- Evidence assessment for document checklist features
- Failure analysis for risk warnings

### For Data Engineers (Aditya)
- Procedure data in `procedures/data/` directory
- Legal data in `db/` directory
- All data loaded through `data_bridge` and `procedures.loader`
- Schema validation built-in
- Easy to add new jurisdictions or domains

### For ML Engineers (Raj)
- RL feedback endpoint: `POST /nyaya/feedback`
- Performance metrics in `performance_memory.db`
- Confidence scoring integrated with evidence readiness
- Trace system for analyzing decision patterns

## 🔧 Configuration

Edit `.env` file:
```bash
HOST=0.0.0.0
PORT=8000
HMAC_SECRET_KEY=your-secret-key-here
SIGNING_METHOD=HMAC_SHA256
LOG_LEVEL=info
```

## 📚 Documentation Files

- `README.md` - This file (integrated system overview)
- `ARCHITECTURE.md` - System architecture diagrams
- `ENFORCEMENT_ENGINE.md` - Enforcement engine details
- `SOVEREIGN_GOVERNANCE_COMPLIANCE.md` - Governance compliance
- `TRACE_EXAMPLES.md` - Provenance chain examples
- `nyaya-legal-procedure-datasets/README.md` - Procedure datasets documentation

## ✅ System Status

- ✅ All endpoints operational
- ✅ Procedure intelligence integrated
- ✅ Legal query enrichment active
- ✅ Evidence assessment functional
- ✅ Failure analysis operational
- ✅ Cross-jurisdictional comparison ready
- ✅ Sovereign enforcement active
- ✅ Provenance chain validated
- ✅ RL feedback system operational

## 🚨 Important Notes

### What NOT to Break
- **Sovereign Compliance**: Never remove event signing or hash chaining
- **Provenance Chain**: Maintain immutable audit trail
- **Enforcement Engine**: Preserve all governance controls
- **API Contracts**: Keep backward compatibility
- **Data Integrity**: Never modify source JSON files
- **Procedure Schemas**: Maintain v1.1 and v2.0 compatibility

### Adding New Data
- Add new legal datasets to `db/` directory
- Add new procedures to `procedures/data/{country}/` directory
- Follow existing JSON structure
- Run validation before deployment

---

**Status**: Production Ready
**Version**: 1.0.0 (Integrated)
**Last Updated**: 2025-01
**Maintained by**: Nyaya AI Team
