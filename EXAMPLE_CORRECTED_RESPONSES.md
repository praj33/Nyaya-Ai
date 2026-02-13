# Example Corrected Responses

## Before Ontology System

### Query: "terrorist attack"

**Response (Incorrect)**:
```json
{
  "domain": "criminal",
  "jurisdiction": "IN",
  "confidence": 0.92,
  "reasoning_trace": {
    "legal_analysis": "Legal Analysis for IN Jurisdiction:\n\nApplicable Legal Provisions:\n==================================================\n\n1. Section 113 (In Bns Sections):\n   Terrorist act\n\n2. Section acid_attack (In Indian Law Dataset):\n   Acid attack\n\n3. Section 66F (In It Act 2000):\n   Punishment for cyber terrorism - Life imprisonment\n\n4. Section 113 (In Crpc Sections):\n   Summons or warrant in case of person not so present\n\n5. Section 113 (In Ipc Sections):\n   Liability of abettor for an effect caused by the act abetted\n\n6. Section grievous_hurt (In Indian Law Dataset):\n   Voluntarily causing grievous hurt"
  }
}
```

**Issues**:
- Mixed irrelevant sections (acid attack, grievous hurt)
- CrPC 113 (procedural, wrong context)
- IPC 113 (abettor liability, wrong context)
- No UAPA sections (primary terrorism law)
- Raw section numbers without act qualification

---

## After Ontology System

### Query: "terrorist attack"

**Response (Correct)**:
```json
{
  "domain": "terrorism",
  "jurisdiction": "IN",
  "confidence": {
    "overall": 0.95,
    "jurisdiction": 0.95,
    "domain": 0.95,
    "statute_match": 0.90,
    "procedural_match": 0.85
  },
  "statutes": [
    {
      "act": "Unlawful Activities (Prevention) Act",
      "year": 1967,
      "section": "15",
      "title": "Terrorist act - Whoever commits a terrorist act shall be punished with imprisonment for not less than 5 years"
    },
    {
      "act": "Unlawful Activities (Prevention) Act",
      "year": 1967,
      "section": "16",
      "title": "Punishment for terrorist act - Death or life imprisonment"
    },
    {
      "act": "Bharatiya Nyaya Sanhita",
      "year": 2023,
      "section": "113",
      "title": "Terrorist act"
    },
    {
      "act": "Information Technology Act",
      "year": 2000,
      "section": "66F",
      "title": "Punishment for cyber terrorism - Life imprisonment"
    }
  ],
  "reasoning_trace": {
    "legal_analysis": "Legal Analysis for IN Jurisdiction:\n\nApplicable Legal Provisions:\n==================================================\n\n1. Section 15 of Unlawful Activities (Prevention) Act, 1967 (UAPA):\n   Terrorist act - Whoever commits a terrorist act shall be punished with imprisonment for not less than 5 years\n\n2. Section 16 of Unlawful Activities (Prevention) Act, 1967 (UAPA):\n   Punishment for terrorist act - Death or life imprisonment\n\n3. Section 113 of Bharatiya Nyaya Sanhita, 2023 (BNS):\n   Terrorist act\n\n4. Section 66F of Information Technology Act, 2000 (IT Act):\n   Punishment for cyber terrorism - Life imprisonment"
  }
}
```

**Improvements**:
- UAPA automatically included (primary terrorism law)
- Domain auto-switched to "terrorism"
- All sections fully qualified with act name and year
- Irrelevant sections filtered out
- No cross-law contamination
- Structured confidence breakdown

---

## Query: "divorce in India"

### Before
```json
{
  "domain": "family",
  "confidence": 0.85,
  "reasoning_trace": {
    "legal_analysis": "1. Section 13 (In Hindu Marriage Act):\n   Divorce\n\n2. Section 498A (In Ipc Sections):\n   Husband or relative of husband subjecting woman to cruelty"
  }
}
```

**Issues**:
- Criminal section (498A) mixed with family law
- No act qualification

### After
```json
{
  "domain": "family",
  "confidence": {
    "overall": 0.92,
    "jurisdiction": 0.95,
    "domain": 0.95,
    "statute_match": 0.85,
    "procedural_match": 0.90
  },
  "statutes": [
    {
      "act": "Hindu Marriage Act",
      "year": 1955,
      "section": "13",
      "title": "Divorce - Grounds for divorce"
    },
    {
      "act": "Special Marriage Act",
      "year": 1954,
      "section": "27",
      "title": "Divorce - Grounds for divorce under special marriage"
    }
  ],
  "reasoning_trace": {
    "legal_analysis": "Legal Analysis for IN Jurisdiction:\n\nApplicable Legal Provisions:\n==================================================\n\n1. Section 13 of Hindu Marriage Act, 1955 (HMA):\n   Divorce - Grounds for divorce\n\n2. Section 27 of Special Marriage Act, 1954 (SMA):\n   Divorce - Grounds for divorce under special marriage"
  }
}
```

**Improvements**:
- Criminal sections excluded (domain rule)
- Only family law acts included
- Fully qualified statutes

---

## Query: "hacking my computer"

### Before
```json
{
  "domain": "criminal",
  "confidence": 0.88,
  "reasoning_trace": {
    "legal_analysis": "1. Section 66 (In It Act 2000):\n   Computer hacking\n\n2. Section 379 (In Ipc Sections):\n   Punishment for theft\n\n3. Section 304 (In Bns Sections):\n   Theft"
  }
}
```

**Issues**:
- Theft sections (IPC 379, BNS 304) irrelevant
- Domain should be "cyber" not "criminal"

### After
```json
{
  "domain": "cyber",
  "confidence": {
    "overall": 0.93,
    "jurisdiction": 0.95,
    "domain": 0.95,
    "statute_match": 0.90,
    "procedural_match": 0.85
  },
  "statutes": [
    {
      "act": "Information Technology Act",
      "year": 2000,
      "section": "66",
      "title": "Computer hacking - Unauthorized access to computer systems"
    },
    {
      "act": "Information Technology Act",
      "year": 2000,
      "section": "66B",
      "title": "Punishment for dishonestly receiving stolen computer resource"
    },
    {
      "act": "Information Technology Act",
      "year": 2000,
      "section": "66C",
      "title": "Punishment for identity theft"
    }
  ],
  "reasoning_trace": {
    "legal_analysis": "Legal Analysis for IN Jurisdiction:\n\nApplicable Legal Provisions:\n==================================================\n\n1. Section 66 of Information Technology Act, 2000 (IT Act):\n   Computer hacking - Unauthorized access to computer systems\n\n2. Section 66B of Information Technology Act, 2000 (IT Act):\n   Punishment for dishonestly receiving stolen computer resource\n\n3. Section 66C of Information Technology Act, 2000 (IT Act):\n   Punishment for identity theft"
  }
}
```

**Improvements**:
- Domain correctly identified as "cyber"
- Only IT Act sections (cyber-specific)
- General theft sections excluded
- All sections from same act (no contamination)

---

## Query: "my boss is harassing me"

### Before
```json
{
  "domain": "criminal",
  "confidence": 0.85,
  "reasoning_trace": {
    "legal_analysis": "1. Section 354A (In Ipc Sections):\n   Sexual harassment\n\n2. Section 75 (In Bns Sections):\n   Sexual harassment"
  }
}
```

**Issues**:
- Only criminal harassment sections
- Missing labour law provisions for workplace harassment

### After
```json
{
  "domain": "criminal",
  "confidence": {
    "overall": 0.90,
    "jurisdiction": 0.95,
    "domain": 0.90,
    "statute_match": 0.85,
    "procedural_match": 0.85
  },
  "statutes": [
    {
      "act": "Indian Penal Code",
      "year": 1860,
      "section": "354A",
      "title": "Sexual harassment and punishment for sexual harassment"
    },
    {
      "act": "Bharatiya Nyaya Sanhita",
      "year": 2023,
      "section": "75",
      "title": "Sexual harassment"
    },
    {
      "act": "Labour and Employment Laws",
      "year": 1948,
      "section": "30",
      "title": "Workplace harassment - Prevention and redressal"
    },
    {
      "act": "Labour and Employment Laws",
      "year": 1948,
      "section": "31",
      "title": "Sexual harassment at workplace - Vishaka guidelines"
    }
  ],
  "reasoning_trace": {
    "legal_analysis": "Legal Analysis for IN Jurisdiction:\n\nApplicable Legal Provisions:\n==================================================\n\n1. Section 354A of Indian Penal Code, 1860 (IPC):\n   Sexual harassment and punishment for sexual harassment\n\n2. Section 75 of Bharatiya Nyaya Sanhita, 2023 (BNS):\n   Sexual harassment\n\n3. Section 30 of Labour and Employment Laws, 1948 (Labour Laws):\n   Workplace harassment - Prevention and redressal\n\n4. Section 31 of Labour and Employment Laws, 1948 (Labour Laws):\n   Sexual harassment at workplace - Vishaka guidelines"
  }
}
```

**Improvements**:
- Both criminal and labour law provisions
- Workplace-specific sections included
- Comprehensive coverage for workplace harassment

---

## Summary of Improvements

### 1. No Cross-Law Contamination
- Criminal queries don't return family/civil sections
- Family queries don't return criminal sections
- Domain-specific filtering enforced

### 2. Fully Qualified Statutes
- Every section includes act name, year, abbreviation
- Format: "Section X of Act Name, Year (Abbreviation)"
- No ambiguous "Section 113" references

### 3. Auto-Inclusion Rules
- Terrorism keywords → UAPA automatically included
- Domain auto-switches to most specific (terrorism > criminal)

### 4. Priority Handling
- BNS preferred over IPC (newer law)
- BNSS preferred over CrPC (newer law)
- Active acts prioritized over replaced acts

### 5. Structured Confidence
- Overall confidence
- Jurisdiction confidence
- Domain confidence
- Statute match confidence
- Procedural match confidence

### 6. Duplicate Prevention
- Same section from multiple acts appears only once
- Highest priority version selected
