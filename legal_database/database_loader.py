"""Legal database loader for comprehensive legal data integration."""
import json
import os
import re
from typing import Dict, Any, List, Optional

from bm25_search import BM25Ranker
from data_bridge.loader import JSONLoader

class LegalDatabaseLoader:
    """Loads and provides access to comprehensive legal databases."""
    
    def __init__(self, db_path: str = "db"):
        if os.path.exists(db_path):
            self.db_path = db_path
        else:
            candidate = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", db_path))
            self.db_path = candidate if os.path.exists(candidate) else db_path
        self.databases = {}
        self.sections = []
        self.acts = []
        self.cases = []
        self.search_sections = []
        self.search_corpus = []
        self.act_name_map = {}
        self.ranker = BM25Ranker(k1=1.5, b=0.75)
        self._load_databases()
        self._load_search_index()
    
    def _load_databases(self):
        """Load all legal databases and domain maps."""
        db_files = {
            'indian_domain_map': 'indian_domain_map.json',
            'uae_domain_map': 'uae_domain_map.json',
            'uk_domain_map': 'uk_domain_map.json'
        }
        
        for key, filename in db_files.items():
            file_path = os.path.join(self.db_path, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.databases[key] = json.load(f)
                except Exception:
                    pass

    def _load_search_index(self):
        """Load and index the full normalized section corpus."""
        try:
            loader = JSONLoader(self.db_path)
            self.sections, self.acts, self.cases = loader.load_and_normalize_directory()
        except Exception:
            self.sections, self.acts, self.cases = [], [], []
            self.search_sections = []
            self.search_corpus = []
            return

        self.act_name_map = self._build_act_name_map()
        self._augment_act_name_map_from_files(loader)
        deduped_sections = {}
        for section in self.sections:
            dedupe_key = (
                section.jurisdiction.value,
                section.act_id,
                self._canonical_section_number(section.section_number),
                self._normalize_text(section.text),
            )
            existing = deduped_sections.get(dedupe_key)
            if existing is None or self._section_quality(section) > self._section_quality(existing):
                deduped_sections[dedupe_key] = section

        self.search_sections = list(deduped_sections.values())
        self.search_corpus = [self._build_search_document(section) for section in self.search_sections]
        if self.search_corpus:
            self.ranker.fit(self.search_corpus)

    def _build_act_name_map(self) -> Dict[str, str]:
        act_name_map = {}
        for act in self.acts:
            metadata = getattr(act, "metadata", {}) or {}
            act_name = (
                metadata.get("code")
                or metadata.get("act_name")
                or metadata.get("law")
                or act.act_name
            )
            if act_name:
                act_name_map[act.act_id] = str(act_name)
        return act_name_map

    def _augment_act_name_map_from_files(self, loader: JSONLoader):
        for root, _, files in os.walk(self.db_path):
            for file_name in files:
                if not file_name.lower().endswith(".json"):
                    continue
                file_path = os.path.join(root, file_name)
                try:
                    data = loader.load_json_file(file_path)
                    jurisdiction = loader.detect_jurisdiction_from_path(file_path).value
                except Exception:
                    continue
                file_act_id = f"{jurisdiction}_{os.path.splitext(file_name)[0]}"
                act_name = data.get("code") or data.get("act_name") or data.get("law")
                if act_name:
                    self.act_name_map[file_act_id] = str(act_name)

    def _build_search_document(self, section) -> str:
        act_name = self._format_act_name(section.act_id)
        metadata_text = self._stringify_metadata(section.metadata)
        canonical_section = self._canonical_section_number(section.section_number)
        return " ".join(
            part
            for part in [
                f"Section {canonical_section}" if canonical_section else "",
                act_name,
                str(section.act_id).replace("_", " "),
                section.text,
                metadata_text,
            ]
            if part
        )

    def _stringify_metadata(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, dict):
            parts = []
            for key, item in value.items():
                parts.append(str(key))
                parts.append(self._stringify_metadata(item))
            return " ".join(part for part in parts if part)
        if isinstance(value, list):
            return " ".join(self._stringify_metadata(item) for item in value)
        return str(value)

    def _section_quality(self, section) -> int:
        score = len(section.text or "")
        normalized = self._canonical_section_number(section.section_number)
        raw = str(section.section_number or "")
        if normalized and normalized != raw:
            score += 10
        if section.metadata:
            score += 5
        return score

    def _normalize_jurisdiction(self, jurisdiction: str) -> Optional[str]:
        if not jurisdiction:
            return None
        value = str(jurisdiction).strip().lower()
        mapping = {
            "india": "IN",
            "indian": "IN",
            "in": "IN",
            "uk": "UK",
            "united kingdom": "UK",
            "britain": "UK",
            "england": "UK",
            "uae": "UAE",
            "united arab emirates": "UAE",
            "emirates": "UAE",
        }
        if value in mapping:
            return mapping[value]
        upper = value.upper()
        return upper if upper in {"IN", "UK", "UAE"} else None

    def _get_domain_map_key(self, jurisdiction: str) -> Optional[str]:
        jurisdiction_code = self._normalize_jurisdiction(jurisdiction)
        return {
            "IN": "indian_domain_map",
            "UK": "uk_domain_map",
            "UAE": "uae_domain_map",
        }.get(jurisdiction_code)

    def _detect_query_profiles(self, query: str) -> Dict[str, bool]:
        query_lower = query.lower()
        tax_terms = [
            "tax", "gst", "cgst", "igst", "sgst", "income tax", "tds",
            "input tax credit", "itc", "tax evasion", "tax avoidance",
        ]
        property_terms = [
            "builder", "building", "flat", "apartment", "project", "possession",
            "construction", "rera", "handover", "property",
        ]
        delay_terms = [
            "delay", "delayed", "not built", "not build", "not completed",
            "not complete", "on time", "given time", "late",
        ]
        employment_terms = [
            "salary", "wages", "employer", "employee", "boss", "paying me",
            "not paying", "unpaid", "payment of wages", "pending salary",
        ]
        return {
            "tax": any(term in query_lower for term in tax_terms),
            "property_delay": any(term in query_lower for term in property_terms) and any(term in query_lower for term in delay_terms),
            "employment_unpaid": any(term in query_lower for term in employment_terms),
        }

    def _build_search_queries(self, query: str, profiles: Dict[str, bool]) -> List[tuple[str, float]]:
        queries = [(query, 1.0)]
        if profiles.get("tax"):
            queries.append(("tax not paid gst income tax tds collected tax not paid penalty", 0.9))
        if profiles.get("property_delay"):
            queries.append(("builder delayed possession rera refund interest project completion", 0.95))
            queries.append(("delay in possession builder not completed construction handover", 0.85))
        if profiles.get("employment_unpaid"):
            queries.append(("salary unpaid wages employer payment of wages delayed salary", 0.95))
            queries.append(("wages not paid boss employer labour minimum wages", 0.85))
        return queries

    def _act_profile_boost(self, act_id: str, profiles: Dict[str, bool]) -> float:
        act_id_lower = str(act_id or "").lower()
        score = 0.0
        if profiles.get("tax"):
            if "income_tax" in act_id_lower or "cgst" in act_id_lower:
                score += 25.0
            if any(value in act_id_lower for value in ["cpc", "crpc", "ipc", "bns"]):
                score -= 15.0
        if profiles.get("property_delay"):
            if "property_real_estate" in act_id_lower:
                score += 30.0
            if any(value in act_id_lower for value in ["cpc", "crpc", "ipc", "bns", "dowry"]):
                score -= 18.0
        if profiles.get("employment_unpaid"):
            if "labour_employment" in act_id_lower:
                score += 30.0
            if any(value in act_id_lower for value in ["cpc", "crpc", "ipc", "bns", "cgst", "income_tax"]):
                score -= 18.0
        return score

    def _format_act_name(self, act_id: str) -> str:
        if act_id in self.act_name_map:
            return self.act_name_map[act_id]
        clean = str(act_id).replace("_", " ").strip()
        clean = re.sub(r"\bIN\b|\bUK\b|\bUAE\b", "", clean).strip()
        return re.sub(r"\s+", " ", clean).title() if clean else "Unknown Act"

    def _canonical_section_number(self, section_number: Any) -> str:
        value = str(section_number or "").strip()
        value = re.sub(r"^(section|article)[_\-\s]+", "", value, flags=re.IGNORECASE)
        return value

    def _normalize_text(self, text: str) -> str:
        return " ".join(str(text or "").lower().split())

    def _extract_section_hints(self, query: str) -> List[str]:
        hints = []
        for pattern in (
            r"\bsection(?:s)?\s+([0-9A-Za-z, /\-]+)",
            r"\barticle(?:s)?\s+([0-9A-Za-z, /\-]+)",
        ):
            for match in re.findall(pattern, query, flags=re.IGNORECASE):
                for part in re.split(r"[,/ ]+", match):
                    value = self._canonical_section_number(part)
                    if value and any(ch.isdigit() for ch in value) and value.lower() not in hints:
                        hints.append(value.lower())
        return hints

    def _act_quality_adjustment(self, act_id: str) -> float:
        act_id_lower = str(act_id or "").lower()
        if "domain_map" in act_id_lower or "routes" in act_id_lower:
            return -25.0
        if "dataset" in act_id_lower or "comprehensive_laws_reference" in act_id_lower:
            return -10.0
        if "sections" in act_id_lower:
            return 6.0
        return 3.0

    def _domain_boost(self, search_text: str, domain: str) -> float:
        domain_keywords = {
            "criminal": ["offence", "punishment", "imprisonment", "fine", "bail", "arrest"],
            "civil": ["agreement", "liability", "compensation", "award", "company", "tax", "refund"],
            "family": ["marriage", "divorce", "custody", "maintenance", "matrimonial"],
            "commercial": ["company", "share", "director", "trade", "commercial", "arbitration"],
            "consumer": ["consumer", "refund", "defective", "warranty", "service"],
        }
        score = 0.0
        for keyword in domain_keywords.get(str(domain).lower(), []):
            if keyword in search_text:
                score += 1.5
        return score
    
    def classify_query_domain(self, query: str, jurisdiction: str) -> Dict[str, Any]:
        """Classify query into legal domain using keyword mapping."""
        jurisdiction_key = self._get_domain_map_key(jurisdiction)
        domain_map = self.databases.get(jurisdiction_key, {})
        
        if not domain_map:
            return {"domain": "criminal", "confidence": 0.5, "subdomains": []}

        profiles = self._detect_query_profiles(query)
        if profiles.get("tax"):
            return {"domain": "civil", "confidence": 0.9, "subdomains": ["tax_matters"], "threshold": 0.7}
        if profiles.get("property_delay"):
            return {"domain": "civil", "confidence": 0.85, "subdomains": ["property_disputes"], "threshold": 0.7}
        if profiles.get("employment_unpaid"):
            return {"domain": "civil", "confidence": 0.85, "subdomains": ["employment_matters"], "threshold": 0.7}
        
        query_lower = query.lower()
        keyword_mapping = domain_map.get("keyword_mapping", {})
        domain_mapping = domain_map.get("domain_mapping", {})
        
        domain_scores = {}
        subdomain_matches = []
        
        for subdomain, keywords in keyword_mapping.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in query_lower)
            if matches > 0:
                subdomain_matches.append(subdomain)
                for domain, config in domain_mapping.items():
                    if subdomain in config.get("subdomains", []):
                        domain_scores[domain] = domain_scores.get(domain, 0) + matches
        
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            confidence = min(0.9, domain_scores[best_domain] * 0.2 + 0.5)
        else:
            best_domain = domain_map.get("fallback_rules", {}).get("default_domain", "criminal")
            confidence = 0.3
        
        return {
            "domain": best_domain,
            "confidence": confidence,
            "subdomains": subdomain_matches,
            "threshold": domain_mapping.get(best_domain, {}).get("confidence_threshold", 0.7)
        }
    
    def get_legal_sections(self, query: str, jurisdiction: str, domain: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get relevant legal sections using the full normalized section corpus."""
        if not self.search_corpus or not query.strip():
            return []

        jurisdiction_code = self._normalize_jurisdiction(jurisdiction)
        profiles = self._detect_query_profiles(query)
        search_queries = self._build_search_queries(query, profiles)
        query_terms = set()
        for search_query, _ in search_queries:
            query_terms.update(term for term in self.ranker.tokenize(search_query) if len(term) > 2)
        section_hints = set(self._extract_section_hints(query))
        candidate_count = min(max(limit * 25, 80), len(self.search_corpus))
        raw_candidates = {}
        for search_query, weight in search_queries:
            ranked_candidates = self.ranker.search(search_query, top_k=candidate_count)
            for doc_idx, bm25_score in ranked_candidates:
                weighted_score = bm25_score * weight
                if doc_idx not in raw_candidates or weighted_score > raw_candidates[doc_idx]:
                    raw_candidates[doc_idx] = weighted_score
        scored = {}
        for doc_idx, bm25_score in raw_candidates.items():
            section = self.search_sections[doc_idx]
            if jurisdiction_code and section.jurisdiction.value != jurisdiction_code:
                continue

            search_text = self.search_corpus[doc_idx].lower()
            canonical_section = self._canonical_section_number(section.section_number)
            overlap = sum(1 for term in query_terms if term in search_text)
            score = (bm25_score * 10.0) + (overlap * 3.0)
            score += self._domain_boost(search_text, domain)
            score += self._act_quality_adjustment(section.act_id)
            score += self._act_profile_boost(section.act_id, profiles)

            if profiles.get("property_delay"):
                score += sum(6.0 for term in ["delay", "possession", "refund", "interest", "rera"] if term in search_text)
            if profiles.get("employment_unpaid"):
                score += sum(6.0 for term in ["wages", "salary", "payment", "employer"] if term in search_text)
            if profiles.get("tax"):
                score += sum(6.0 for term in ["tax", "paid", "penalty", "refund", "credit"] if term in search_text)

            if section_hints:
                canonical_lower = canonical_section.lower()
                if canonical_lower in section_hints:
                    score += 60.0
                elif any(hint in canonical_lower for hint in section_hints):
                    score += 20.0

            act_name = self._format_act_name(section.act_id)
            act_name_lower = act_name.lower()
            score += sum(4.0 for term in query_terms if len(term) > 3 and term in act_name_lower)

            dedupe_key = (
                section.jurisdiction.value,
                act_name,
                canonical_section,
                self._normalize_text(section.text),
            )
            existing = scored.get(dedupe_key)
            if existing is None or score > existing["score"]:
                scored[dedupe_key] = {
                    "section_obj": section,
                    "score": score,
                    "act_name": act_name,
                    "canonical_section": canonical_section,
                }

        ranked_results = sorted(scored.values(), key=lambda item: item["score"], reverse=True)
        formatted = []
        for item in ranked_results[:limit]:
            section = item["section_obj"]
            if "domain_map" in str(section.act_id).lower() or "routes" in str(section.act_id).lower():
                continue
            metadata = section.metadata or {}
            formatted.append({
                "act": item["act_name"],
                "act_id": section.act_id,
                "section": item["canonical_section"] or section.section_number,
                "title": section.text[:200],
                "text": section.text,
                "jurisdiction": section.jurisdiction.value,
                "match_score": round(item["score"], 3),
                "punishment": metadata.get("punishment", ""),
                "elements": metadata.get("elements_required", []),
                "process": metadata.get("process_steps", []),
            })
            if len(formatted) >= limit:
                break

        return formatted

legal_db = LegalDatabaseLoader()
