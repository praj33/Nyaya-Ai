# Quick Start Guide - Nyaya AI Integrated System

## 🚀 Starting the Backend

### Option 1: Using the Startup Script (Recommended)
```bash
# Simply double-click or run:
start_backend.bat
```

### Option 2: Manual Start
```bash
cd C:\Users\Gauri\Desktop\Nyaya-Ai\Nyaya_AI
set HMAC_SECRET_KEY=nyaya-ai-secret-key-2025-production-change-this-in-production
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using Python directly
```bash
cd C:\Users\Gauri\Desktop\Nyaya-Ai\Nyaya_AI
set HMAC_SECRET_KEY=nyaya-ai-secret-key-2025-production-change-this-in-production
python -m api.main
```

## 📍 Access Points

Once the server is running:
- **API Root**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🧪 Testing the Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected Response:
```json
{
  "status": "healthy",
  "service": "nyaya-api-gateway"
}
```

### 2. List Available Procedures
```bash
curl http://localhost:8000/nyaya/procedures/list
```

### 3. Get Procedure Summary
```bash
curl http://localhost:8000/nyaya/procedures/summary/india/criminal
```

### 4. Legal Query (with Procedure Intelligence)
```bash
curl -X POST http://localhost:8000/nyaya/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What are the steps for filing a criminal complaint in India?\",
    \"jurisdiction_hint\": \"India\",
    \"domain_hint\": \"criminal\",
    \"user_context\": {
      \"role\": \"citizen\",
      \"confidence_required\": true
    }
  }"
```

### 5. Analyze Procedure
```bash
curl -X POST http://localhost:8000/nyaya/procedures/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"country\": \"india\",
    \"domain\": \"criminal\",
    \"current_step\": \"CRIME_REPORTING\"
  }"
```

### 6. Assess Evidence Readiness
```bash
curl -X POST http://localhost:8000/nyaya/procedures/evidence/assess \
  -H "Content-Type: application/json" \
  -d "{
    \"canonical_step\": \"CRIME_REPORTING\",
    \"available_documents\": [\"complaint_or_information\", \"identity_proof\"]
  }"
```

### 7. Analyze Failure Risk
```bash
curl -X POST http://localhost:8000/nyaya/procedures/failure/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"failure_code\": \"MISSING_MANDATORY_DOCUMENTS\"
  }"
```

### 8. Compare Procedures Across Countries
```bash
curl -X POST http://localhost:8000/nyaya/procedures/compare \
  -H "Content-Type: application/json" \
  -d "{
    \"countries\": [\"india\", \"uae\", \"uk\"],
    \"domain\": \"criminal\"
  }"
```

### 9. Get All Schemas
```bash
curl http://localhost:8000/nyaya/procedures/schemas
```

## 📊 Using Swagger UI (Easiest Method)

1. Open http://localhost:8000/docs in your browser
2. You'll see all endpoints with interactive documentation
3. Click on any endpoint to expand it
4. Click "Try it out" button
5. Fill in the request body
6. Click "Execute"
7. See the response below

## 🔍 Available Endpoints Summary

### Legal Query Endpoints
- `POST /nyaya/query` - Single jurisdiction legal query
- `POST /nyaya/multi_jurisdiction` - Multi-jurisdiction comparison
- `POST /nyaya/explain_reasoning` - Explain reasoning for a trace
- `POST /nyaya/feedback` - Submit feedback
- `GET /nyaya/trace/{trace_id}` - Get audit trail

### Procedure Intelligence Endpoints
- `POST /nyaya/procedures/analyze` - Analyze a procedure
- `GET /nyaya/procedures/summary/{country}/{domain}` - Get procedure summary
- `POST /nyaya/procedures/evidence/assess` - Assess evidence readiness
- `POST /nyaya/procedures/failure/analyze` - Analyze failure risk
- `POST /nyaya/procedures/compare` - Compare procedures across countries
- `GET /nyaya/procedures/list` - List all available procedures
- `GET /nyaya/procedures/schemas` - Get all schemas

### System Endpoints
- `GET /health` - Health check
- `GET /` - API information

## 🗂️ Available Data

### Jurisdictions
- **india** - India
- **uae** - United Arab Emirates
- **uk** - United Kingdom
- **ksa** - Saudi Arabia

### Domains
- **criminal** - Criminal procedures
- **civil** - Civil procedures
- **family** - Family law procedures
- **consumer_commercial** - Consumer and commercial procedures

### Canonical Steps
- CRIME_REPORTING
- INVESTIGATION
- PRE_TRIAL_RELEASE_DECISION
- PROSECUTION_DECISION
- CASE_ALLOCATION
- SETTLEMENT_ATTEMPT
- MEDIATION_ATTEMPT
- TRIAL
- JUDGMENT
- APPEAL

### Evidence States
- EVIDENCE_COMPLETE
- EVIDENCE_PARTIAL
- EVIDENCE_MISSING

### Failure Codes
- MISSING_MANDATORY_DOCUMENTS
- NON_APPEARANCE_BY_COMPLAINANT
- NON_APPEARANCE_BY_DEFENDANT
- JURISDICTION_REJECTED
- INSUFFICIENT_PRIMA_FACIE_CASE
- LIMITATION_PERIOD_EXPIRED
- SERVICE_OF_NOTICE_FAILED
- STATUTORY_TIME_LIMIT_EXCEEDED

## 🛠️ Troubleshooting

### Server won't start
1. Check if port 8000 is already in use
2. Verify Python is installed: `python --version`
3. Verify dependencies: `pip install -r requirements.txt`
4. Check environment variables are set

### Import errors
```bash
# Make sure you're in the correct directory
cd C:\Users\Gauri\Desktop\Nyaya-Ai\Nyaya_AI

# Reinstall dependencies
pip install -r requirements.txt
```

### Environment variable errors
```bash
# Set the secret key manually
set HMAC_SECRET_KEY=nyaya-ai-secret-key-2025-production-change-this-in-production
```

## 📝 Next Steps

1. **Test all endpoints** using Swagger UI at http://localhost:8000/docs
2. **Review the API responses** to understand the data structure
3. **Integrate with frontend** using the documented endpoints
4. **Add more legal data** to the `db/` directory
5. **Add more procedures** to the `procedures/data/` directory

## 🔐 Security Notes

- The default HMAC_SECRET_KEY is for development only
- Change it in production: Edit `.env` file
- Never commit the `.env` file with real secrets
- Use environment variables in production deployment

## 📚 Documentation

- **INTEGRATED_README.md** - Complete system documentation
- **ARCHITECTURE.md** - System architecture
- **README.md** - Original Nyaya AI documentation
- **Swagger UI** - Interactive API documentation at /docs

---

**Status**: Ready to Run
**Port**: 8000
**Host**: localhost (0.0.0.0)
