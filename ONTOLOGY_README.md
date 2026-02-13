# Nyaya AI Statute Ontology System

## Overview

The Statute Ontology System ensures legally coherent responses by preventing cross-law contamination and enforcing domain-specific statute filtering.

## Architecture

### Components

1. **Indian Legal Ontology** (`core/ontology/indian_legal_ontology.json`)
   - Defines all Indian acts with metadata
   - Specifies domain rules and exclusions
   - Auto-inclusion rules for special cases (e.g., terrorism)

2. **Statute Resolver** (`core/ontology/statute_resolver.py`)
   - Filters sections based on domain and query
   - Qualifies sections with full act metadata
   - Prevents duplicate sections across acts

3. **Enhanced Router** (`api/router.py`)
   - Integrates ontology filtering into query pipeline
   - Returns fully qualified statutes
   - Provides structured confidence scores

## Ontology Structure

### Act Definition

```json
{
  "act_id": "bns_sections",
  "name": "Bharatiya Nyaya Sanhita",
  "year": 2023,
  "abbreviation": "BNS",
  "jurisdiction": "IN",
  "domain": ["criminal"],
  "section_range": ["1", "358"],
  "keywords": ["criminal", "offence", "punishment"],
  "priority": 1,
  "active": true
}
```

### Domain Rules

```json
{
  "criminal": {
    "primary_acts": ["bns_sections", "it_act_2000", "uapa_1967"],
    "procedural_acts": ["bnss_sections", "crpc_sections"],
    "exclude_domains": ["family", "civil"]
  }
}
```

## Domain Filtering Logic

### Criminal Domain
- **Includes**: BNS, IT Act, UAPA, BNSS (procedural)
- **Excludes**: Family law, Civil law (except procedural)

### Family Domain
- **Includes**: Hindu Marriage Act, Special Marriage Act, Domestic Violence Act
- **Excludes**: Criminal law (except procedural)

### Civil Domain
- **Includes**: Consumer Protection, Labour Laws, Property Laws, Motor Vehicles, Farmers Protection
- **Excludes**: None (most permissive)

### Cyber Domain
- **Includes**: IT Act 2000, BNSS (procedural)
- **Excludes**: Family law

### Terrorism Domain (Auto-triggered)
- **Includes**: UAPA 1967, BNS, IT Act
- **Excludes**: Family law, Civil law

## Auto-Inclusion Rules

### Terrorism Keywords
When query contains: `terrorism`, `terrorist`, `extremism`, `unlawful activities`, `national security`, `anti-terror`

**Action**: Automatically include UAPA 1967 and switch domain to `terrorism`

## Response Format

### Qualified Statute Schema

```json
{
  "act": "Bharatiya Nyaya Sanhita",
  "year": 2023,
  "section": "113",
  "title": "Terrorist act"
}
```

### Structured Confidence

```json
{
  "overall": 0.92,
  "jurisdiction": 0.95,
  "domain": 0.90,
  "statute_match": 0.85,
  "procedural_match": 0.80
}
```

## Example Queries

### Query: "terrorist attack"

**Domain Detected**: terrorism (auto-triggered)

**Statutes Returned**:
1. Section 113 of Bharatiya Nyaya Sanhita, 2023 (BNS): Terrorist act
2. Section 15 of Unlawful Activities (Prevention) Act, 1967 (UAPA): Terrorist act
3. Section 66F of Information Technology Act, 2000 (IT Act): Cyber terrorism

**Excluded**: IPC 113 (replaced by BNS), CrPC 113 (wrong domain), Family law sections

### Query: "divorce in India"

**Domain Detected**: family

**Statutes Returned**:
1. Section 13 of Hindu Marriage Act, 1955 (HMA): Divorce
2. Section 27 of Special Marriage Act, 1954 (SMA): Divorce

**Excluded**: Criminal law sections, Civil law sections

### Query: "hacking my computer"

**Domain Detected**: cyber

**Statutes Returned**:
1. Section 66 of Information Technology Act, 2000 (IT Act): Computer hacking
2. Section 66C of Information Technology Act, 2000 (IT Act): Identity theft

**Excluded**: BNS sections (not cyber-specific), Family law sections

## Act Priority System

- **Priority 1**: Current/primary acts (BNS, BNSS, UAPA, IT Act, all special acts)
- **Priority 2**: Replaced/secondary acts (IPC, CrPC, procedural acts)

Higher priority acts are preferred when multiple acts cover the same domain.

## Backward Compatibility

- All existing endpoints continue to work
- Old response format supported via `confidence` field (uses `overall` value)
- New `statutes` field added without breaking changes
- Structured `confidence` object is backward compatible

## Integration Guide

### Using Statute Resolver

```python
from core.ontology.statute_resolver import StatuteResolver

resolver = StatuteResolver()

# Get relevant acts for a query
acts = resolver.get_relevant_acts(
    query="terrorist attack",
    domain="criminal",
    jurisdiction="IN"
)
# Returns: ["uapa_1967", "bns_sections", "it_act_2000"]

# Filter sections
qualified = resolver.filter_sections(
    sections=raw_sections,
    domain="criminal",
    query="terrorist attack"
)
# Returns: List[QualifiedStatute]
```

### Response Building

```python
statutes = [
    StatuteSchema(
        act=qs.act,
        year=qs.year,
        section=qs.section,
        title=qs.title
    )
    for qs in qualified_statutes
]

confidence = ConfidenceSchema(
    overall=0.92,
    jurisdiction=0.95,
    domain=0.90,
    statute_match=0.85,
    procedural_match=0.80
)
```

## Benefits

1. **No Cross-Law Contamination**: Criminal queries don't return family law sections
2. **Fully Qualified Statutes**: Every section includes act name, year, and abbreviation
3. **Domain Consistency**: Sections are filtered by domain rules
4. **Auto-Inclusion**: Terrorism queries automatically include UAPA
5. **Priority Handling**: BNS preferred over IPC, BNSS over CrPC
6. **Duplicate Prevention**: Same section from multiple acts appears only once

## Future Enhancements

1. Add UK and UAE ontologies
2. Implement cross-jurisdiction comparison
3. Add constitutional article mapping
4. Implement case law integration
5. Add temporal validity (act amendment tracking)
