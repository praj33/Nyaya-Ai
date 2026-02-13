# Example Response with Case Law Integration

## Query
```
"my husband is harassing me for dowry"
```

## Response with Case Laws

```json
{
  "domain": "criminal",
  "domains": ["criminal", "family"],
  "jurisdiction": "IN",
  "confidence": {
    "overall": 0.93,
    "jurisdiction": 0.95,
    "domain": 0.95,
    "statute_match": 0.90,
    "procedural_match": 0.90
  },
  "legal_route": [
    "enhanced_legal_advisor",
    "ontology_resolver",
    "case_law_retriever",
    "multi_strategy_search"
  ],
  "statutes": [
    {
      "act": "Bharatiya Nyaya Sanhita",
      "year": 2023,
      "section": "85",
      "title": "Cruelty by husband or relative of husband"
    },
    {
      "act": "Indian Penal Code",
      "year": 1860,
      "section": "498A",
      "title": "Husband or relative of husband subjecting woman to cruelty"
    },
    {
      "act": "Dowry Prohibition Act",
      "year": 1961,
      "section": "3",
      "title": "Penalty for giving or taking dowry"
    },
    {
      "act": "Protection of Women from Domestic Violence Act",
      "year": 2005,
      "section": "18",
      "title": "Protection orders"
    }
  ],
  "case_laws": [
    {
      "title": "State of Karnataka v. Appa Balu Ingale (1993)",
      "court": "Supreme Court of India",
      "year": 1993,
      "principle": "Cruelty under Section 498A IPC includes mental torture and harassment for dowry. Sustained harassment amounts to cruelty even without physical violence."
    },
    {
      "title": "Rajesh Sharma v. State of UP (2017)",
      "court": "Supreme Court of India",
      "year": 2017,
      "principle": "Family Welfare Committees to be set up to prevent misuse of Section 498A. No automatic arrest of accused or their relatives without proper inquiry."
    },
    {
      "title": "Sushil Kumar Sharma v. Union of India (2005)",
      "court": "Supreme Court of India",
      "year": 2005,
      "principle": "Section 498A IPC should not be used as weapon for vendetta. Arrest should not be automatic and mechanical. Police must satisfy themselves about credibility before arrest."
    }
  ],
  "reasoning_trace": {
    "legal_analysis": "Legal Analysis for IN Jurisdiction:\n\nApplicable Legal Provisions:\n==================================================\n\nCRIMINAL STATUTES:\n1. Section 85 of Bharatiya Nyaya Sanhita, 2023 (BNS)\n2. Section 498A of Indian Penal Code, 1860 (IPC)\n3. Section 3 of Dowry Prohibition Act, 1961 (DPA)\n\nRELEVANT JUDICIAL PRECEDENTS:\n==================================================\n\n1. State of Karnataka v. Appa Balu Ingale (1993) - Supreme Court of India\n   Principle: Cruelty under Section 498A IPC includes mental torture and harassment for dowry. Sustained harassment amounts to cruelty even without physical violence.\n\n2. Rajesh Sharma v. State of UP (2017) - Supreme Court of India\n   Principle: Family Welfare Committees to be set up to prevent misuse of Section 498A. No automatic arrest of accused or their relatives without proper inquiry.\n\n3. Sushil Kumar Sharma v. Union of India (2005) - Supreme Court of India\n   Principle: Section 498A IPC should not be used as weapon for vendetta. Arrest should not be automatic and mechanical.",
    "procedural_steps": [
      "IMMEDIATE: File FIR at nearest police station under IPC 498A/BNS 85",
      "Medical examination if physical injuries present",
      "Apply for protection order under Domestic Violence Act Section 18",
      "Police investigation and evidence collection",
      "Criminal trial in Sessions Court"
    ],
    "remedies": [
      "Criminal prosecution with imprisonment up to 3 years",
      "Protection order preventing acts of violence",
      "Monetary relief for losses suffered",
      "Divorce decree on grounds of cruelty",
      "Permanent alimony and maintenance"
    ],
    "sections_found": 4,
    "case_laws_found": 3
  },
  "trace_id": "trace_20260212_120000_000000"
}
```

## Key Features

### 1. Case Law Integration
- **Automatic retrieval**: Relevant precedents fetched based on query keywords
- **Domain filtering**: Only cases from matching domain (criminal/family)
- **Jurisdiction filtering**: Only Indian cases for Indian queries
- **Top-K selection**: Most relevant 3 cases returned

### 2. Case Law Matching
Query: "my husband is harassing me for dowry"

**Matched Keywords**:
- "498a" → State of Karnataka v. Appa Balu Ingale
- "dowry" → All three cases
- "harassment" → State of Karnataka v. Appa Balu Ingale
- "cruelty" → Multiple cases

**Scoring**:
- Keyword exact match: +10 points
- Word overlap: +2 points per word
- Title match: +1 point
- Principle match: +0.5 points

### 3. Response Structure
```
statutes (4) → Primary legal provisions
case_laws (3) → Judicial precedents supporting statutes
procedural_steps → How to proceed
remedies → Available relief
```

### 4. Backward Compatibility
- `case_laws` field defaults to empty array `[]`
- Existing clients ignore new field
- No breaking changes to existing schema

## Benefits

1. **Authoritative Support**: Statutes backed by Supreme Court precedents
2. **Practical Guidance**: Cases show how courts interpret laws
3. **Balanced View**: Cases like Rajesh Sharma (2017) show both sides
4. **Recent Precedents**: Cases from 1993-2017 show evolution of law
5. **Credibility**: Supreme Court decisions carry highest authority

## Case Law Database

### Current Coverage
- **Criminal cases**: 10 cases (rape, 498A, terrorism, cyber, privacy)
- **Family cases**: 10 cases (divorce, custody, maintenance, live-in)
- **Total**: 20 landmark cases

### Expandable
Add more cases by creating JSON files in `/data/caselaw/`:
- `indian_cyber_cases.json`
- `indian_constitutional_cases.json`
- `uk_criminal_cases.json`
- `uae_civil_cases.json`

### Format
```json
{
  "title": "Case Name v. Respondent (Year)",
  "court": "Court Name",
  "year": 2023,
  "jurisdiction": "IN",
  "domain": "criminal",
  "principle": "Legal principle established",
  "keywords": ["keyword1", "keyword2"]
}
```
