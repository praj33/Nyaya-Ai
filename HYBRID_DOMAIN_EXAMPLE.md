# Example Response: Hybrid Criminal-Family Domain

## Query
```
"my husband is harassing me for dowry"
```

## Expected Response

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
      "title": "Penalty for giving or taking dowry - Imprisonment up to 5 years and fine up to Rs. 15,000"
    },
    {
      "act": "Dowry Prohibition Act",
      "year": 1961,
      "section": "4",
      "title": "Penalty for demanding dowry - Imprisonment from 6 months to 2 years and fine up to Rs. 10,000"
    },
    {
      "act": "Protection of Women from Domestic Violence Act",
      "year": 2005,
      "section": "3",
      "title": "Definition of domestic violence"
    },
    {
      "act": "Protection of Women from Domestic Violence Act",
      "year": 2005,
      "section": "18",
      "title": "Protection orders"
    },
    {
      "act": "Protection of Women from Domestic Violence Act",
      "year": 2005,
      "section": "19",
      "title": "Residence orders"
    },
    {
      "act": "Hindu Marriage Act",
      "year": 1955,
      "section": "13",
      "title": "Divorce - Cruelty as ground for divorce"
    }
  ],
  "reasoning_trace": {
    "legal_analysis": "Legal Analysis for IN Jurisdiction:\n\nApplicable Legal Provisions:\n==================================================\n\nCRIMINAL STATUTES (Primary):\n\n1. Section 85 of Bharatiya Nyaya Sanhita, 2023 (BNS):\n   Cruelty by husband or relative of husband\n\n2. Section 498A of Indian Penal Code, 1860 (IPC):\n   Husband or relative of husband subjecting woman to cruelty\n\n3. Section 3 of Dowry Prohibition Act, 1961 (DPA):\n   Penalty for giving or taking dowry - Imprisonment up to 5 years and fine up to Rs. 15,000\n\n4. Section 4 of Dowry Prohibition Act, 1961 (DPA):\n   Penalty for demanding dowry - Imprisonment from 6 months to 2 years and fine up to Rs. 10,000\n\n5. Section 3 of Protection of Women from Domestic Violence Act, 2005 (PWDVA):\n   Definition of domestic violence\n\n6. Section 18 of Protection of Women from Domestic Violence Act, 2005 (PWDVA):\n   Protection orders\n\n7. Section 19 of Protection of Women from Domestic Violence Act, 2005 (PWDVA):\n   Residence orders\n\nFAMILY LAW REMEDIES (Secondary):\n\n8. Section 13 of Hindu Marriage Act, 1955 (HMA):\n   Divorce - Cruelty as ground for divorce\n\nThis is a hybrid criminal-family matter requiring both criminal prosecution and civil remedies.",
    "procedural_steps": [
      "IMMEDIATE: File FIR at nearest police station under IPC 498A/BNS 85 (Cruelty) and Dowry Prohibition Act",
      "Medical examination if physical injuries present (within 24 hours)",
      "Apply for protection order under Domestic Violence Act Section 18",
      "Apply for residence order to secure matrimonial home (DV Act Section 19)",
      "Police investigation and evidence collection",
      "Charge sheet filing by prosecution",
      "Criminal trial in Sessions Court",
      "Parallel: File petition for divorce on grounds of cruelty (Hindu Marriage Act Section 13)",
      "Parallel: Claim maintenance and alimony (HMA Sections 25, 27)",
      "Judgment and sentencing in criminal case",
      "Divorce decree and financial settlement in family court"
    ],
    "remedies": [
      "Criminal prosecution with imprisonment up to 3 years and fine",
      "Protection order preventing husband from committing acts of violence",
      "Residence order securing right to matrimonial home",
      "Monetary relief for losses suffered due to domestic violence",
      "Custody orders for children",
      "Compensation order under Section 357A CrPC",
      "Divorce decree on grounds of cruelty",
      "Permanent alimony and maintenance",
      "Share in matrimonial property"
    ]
  }
}
```

## Key Features

### 1. Hybrid Domain Classification
- **Primary domain**: `criminal`
- **All domains**: `["criminal", "family"]`
- Criminal statutes appear first (prioritized)
- Family law remedies supplement criminal prosecution

### 2. Statute Prioritization
Criminal statutes listed before family statutes:
1. BNS Section 85 (Cruelty)
2. IPC Section 498A (Cruelty)
3. Dowry Prohibition Act Sections 3, 4
4. Domestic Violence Act Sections 3, 18, 19
5. Hindu Marriage Act Section 13 (Divorce)

### 3. Dual Procedural Track
- **Criminal track**: FIR → Investigation → Trial → Sentencing
- **Family track**: Divorce petition → Maintenance claim → Decree
- Both tracks run in parallel

### 4. Comprehensive Remedies
- **Criminal**: Imprisonment, fine, compensation
- **Civil**: Protection orders, residence orders, monetary relief
- **Family**: Divorce, alimony, property division

### 5. Offense Category Detection
Query triggers `marital_cruelty` offense category:
- Keywords matched: "husband", "harassing", "dowry"
- Auto-includes: BNS/IPC, Dowry Prohibition Act, Domestic Violence Act
- Secondary includes: Hindu Marriage Act

## Comparison with Previous System

### Before (Incorrect)
```json
{
  "domain": "family",
  "statutes": [
    {"act": "Hindu Marriage Act", "section": "13"},
    {"act": "Hindu Marriage Act", "section": "25"}
  ]
}
```
**Problem**: Only family law sections, no criminal statutes

### After (Correct)
```json
{
  "domain": "criminal",
  "domains": ["criminal", "family"],
  "statutes": [
    {"act": "Bharatiya Nyaya Sanhita", "section": "85"},
    {"act": "Dowry Prohibition Act", "section": "3"},
    {"act": "Dowry Prohibition Act", "section": "4"},
    {"act": "Protection of Women from Domestic Violence Act", "section": "18"},
    {"act": "Hindu Marriage Act", "section": "13"}
  ]
}
```
**Solution**: Criminal statutes prioritized, family law supplements
