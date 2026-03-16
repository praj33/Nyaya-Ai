"""Optional Groq-backed query understanding and section reranking.

The database remains the source of truth. This module can:
- expand a user query into better search terms
- rerank candidate sections that were already retrieved from the local DB
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib import error, request

from dotenv import load_dotenv, find_dotenv
from core.llm.profile_utils import build_issue_priority_map, normalize_issue_values

_dotenv_path = find_dotenv(usecwd=False)
load_dotenv(_dotenv_path or None)

VALID_JURISDICTIONS = {"IN", "UK", "UAE"}
VALID_DOMAINS = {
    "criminal",
    "family",
    "civil",
    "consumer",
    "commercial",
    "terrorism",
    "constitutional",
    "banking",
    "employment",
    "tax",
    "cyber",
    "civil_property",
}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "for", "from",
    "get", "give", "help", "how", "i", "if", "in", "is", "it", "me", "my", "of",
    "on", "or", "please", "the", "to", "under", "what", "when", "where", "which",
    "who", "why", "with", "would", "should", "could", "tell", "about", "need",
}

ACT_HINT_RULES = {
    "it_act_2000": [
        "cyber",
        "hacking",
        "phishing",
        "computer",
        "data breach",
        "identity theft",
        "it act",
        "social media",
    ],
    "ipc_sections": ["ipc", "indian penal code"],
    "bns_sections": ["bns", "bharatiya nyaya sanhita", "nyaya sanhita"],
    "crpc_sections": ["crpc", "code of criminal procedure", "fir", "arrest without warrant", "anticipatory bail"],
    "bnss_sections": ["bnss", "bharatiya nagarik suraksha sanhita"],
    "cpc_sections": ["cpc", "code of civil procedure", "civil suit", "injunction suit"],
    "indian_evidence_act": ["evidence act", "indian evidence act"],
    "consumer_protection_act": ["consumer", "defective product", "refund", "warranty", "replacement"],
    "hindu_marriage_act": ["divorce", "marriage", "alimony", "maintenance", "custody", "hindu marriage act", "hindu marriage"],
    "special_marriage_act": ["special marriage", "special marriage act", "interfaith marriage"],
    "domestic_violence_act": ["domestic violence", "protection order", "husband is beating me", "physical abuse", "economic abuse"],
    "dowry_prohibition_act": ["dowry", "dowry harassment", "dowry demand"],
    "pocso_act_2012": [
        "pocso",
        "child abuse",
        "child sexual",
        "minor sexual",
        "pedophile",
        "paedophile",
        "molested child",
        "sex with child",
        "rape of child",
        "child molestation",
        "sexual offence against child",
    ],
    "labour_employment_laws": [
        "salary",
        "termination",
        "employee",
        "employer",
        "wages",
        "boss",
        "unpaid salary",
        "not paying me",
        "pending salary",
        "payment of wages",
    ],
    "property_real_estate_laws": [
        "property",
        "tenant",
        "landlord",
        "builder",
        "rera",
        "rera act",
        "real estate (regulation and development) act",
        "building",
        "possession",
        "project",
        "construction delay",
        "not built",
        "delay in possession",
    ],
    "limitation_act": ["limitation act", "adverse possession", "time limit", "limitation"],
    "registration_act": ["registration act", "registered document", "sale deed registration"],
    "transfer_of_property_act": ["transfer of property", "sale deed", "title deed", "encroachment"],
    "sarfaesi": ["sarfaesi", "sarfaesi act", "npa", "bank auction", "secured creditor", "drt", "emi"],
    "income_tax_act_1961": [
        "income tax",
        "income-tax",
        "income tax act",
        "tax avoidance",
        "tax evasion",
        "tds",
        "under-reported income",
        "misreported income",
        "gaar",
    ],
    "cgst_act_2017": [
        "gst",
        "gst act",
        "cgst",
        "cgst act",
        "central goods and services tax",
        "igst",
        "sgst",
        "fake invoice",
        "bogus invoice",
        "input tax credit",
        "itc",
        "refund fraud",
    ],
    "motor_vehicles_act": ["rash driving", "road accident", "motor vehicle act", "traffic", "drunk driving"],
    "uapa_1967": ["uapa", "unlawful activities", "terrorism", "terrorist"],
}


class GroqRetrievalAugmentor:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        self.timeout_seconds = float(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))
        self.enabled = os.getenv("GROQ_ENABLED", "true").lower() not in {"0", "false", "no"}
        self.query_understanding_enabled = os.getenv(
            "GROQ_QUERY_UNDERSTANDING_ENABLED", "true"
        ).lower() not in {"0", "false", "no"}
        self.section_rerank_enabled = os.getenv(
            "GROQ_SECTION_RERANK_ENABLED", "true"
        ).lower() not in {"0", "false", "no"}
        self.candidate_limit = int(os.getenv("GROQ_SECTION_RERANK_CANDIDATES", "18"))
        self.debug = os.getenv("GROQ_DEBUG", "false").lower() not in {"0", "false", "no"}

    def _disabled_reason(self, mode: str) -> Optional[str]:
        if not self.enabled:
            return "GROQ_ENABLED is false"
        if not self.api_key:
            return "GROQ_API_KEY missing"
        if mode == "understanding" and not self.query_understanding_enabled:
            return "GROQ_QUERY_UNDERSTANDING_ENABLED is false"
        if mode == "rerank" and not self.section_rerank_enabled:
            return "GROQ_SECTION_RERANK_ENABLED is false"
        return None

    def understand_query(
        self,
        *,
        query: str,
        jurisdiction_hint: Optional[str] = None,
        domain_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        jurisdiction_hint = self._normalize_hint(jurisdiction_hint)
        domain_hint = self._normalize_hint(domain_hint)
        fallback = self._build_local_understanding(
            query=query,
            jurisdiction_hint=jurisdiction_hint,
            domain_hint=domain_hint,
        )
        disabled_reason = self._disabled_reason("understanding")
        if disabled_reason:
            fallback["source"] = "local"
            fallback["model"] = None
            fallback["disabled_reason"] = disabled_reason
            return fallback

        prompt = "\n".join(
            [
                "Return strict JSON only.",
                "You are extracting search guidance for a legal retrieval system.",
                "Do not answer the legal question.",
                "Only infer helpful search terms from the user's request.",
                "Schema:",
                "{",
                '  "summary": "short summary",',
                '  "intent": "penalty|procedure|rights|remedy|general",',
                '  "keywords": ["..."],',
                '  "search_queries": ["..."],',
                '  "section_hints": ["..."],',
                '  "act_hints": ["..."],',
                '  "suggested_jurisdiction": "IN|UK|UAE|null",',
                '  "suggested_domain": "criminal|family|civil|consumer|commercial|terrorism|constitutional|null"',
                "}",
                "",
                f"User query: {query}",
                f"Jurisdiction hint: {jurisdiction_hint or 'None'}",
                f"Domain hint: {domain_hint or 'None'}",
            ]
        )

        try:
            data = self._post_chat_completion(prompt)
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            parsed = self._extract_json_object(content)
            normalized = self._normalize_understanding(parsed, fallback)
            normalized["source"] = "groq"
            normalized["model"] = data.get("model", self.model)
            return normalized
        except (ValueError, OSError, error.HTTPError, error.URLError, json.JSONDecodeError) as exc:
            fallback["source"] = "local_fallback"
            fallback["model"] = None
            if self.debug:
                fallback["groq_error"] = f"{type(exc).__name__}: {exc}"
            return fallback

    def rerank_sections(
        self,
        *,
        query: str,
        sections: List[Any],
        jurisdiction: str,
        domain: str,
        understanding: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        understanding = understanding or {}
        fallback_sections = self._local_rerank(query, sections, understanding)[:top_k]
        disabled_reason = self._disabled_reason("rerank")
        if len(sections) <= 1 or disabled_reason:
            return {
                "sections": fallback_sections,
                "source": "local",
                "model": None,
                "reason": disabled_reason or "insufficient candidates",
            }

        candidates = sections[: self.candidate_limit]
        candidate_rows = []
        for idx, section in enumerate(candidates, start=1):
            candidate_rows.append(
                {
                    "candidate_id": idx,
                    "section_number": getattr(section, "section_number", ""),
                    "act_id": getattr(section, "act_id", ""),
                    "text_preview": getattr(section, "text", "")[:240],
                }
            )

        prompt = "\n".join(
            [
                "Return strict JSON only.",
                "Rerank these candidate legal sections for the user's query.",
                "You must only rank the provided candidate_ids.",
                "Prefer exact offence match, exact act match, direct punishment/procedure relevance, and section-number hints.",
                "Schema:",
                '{ "ranked_candidate_ids": [1,2,3], "reason": "short reason" }',
                "",
                f"User query: {query}",
                f"Jurisdiction: {jurisdiction}",
                f"Domain: {domain}",
                f"Understanding summary: {understanding.get('summary', '')}",
                f"Keywords: {understanding.get('keywords', [])}",
                f"Act hints: {understanding.get('act_hints', [])}",
                f"Section hints: {understanding.get('section_hints', [])}",
                "",
                "Candidates:",
                json.dumps(candidate_rows, ensure_ascii=True),
            ]
        )

        try:
            data = self._post_chat_completion(prompt)
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            parsed = self._extract_json_object(content)
            ranked_ids = parsed.get("ranked_candidate_ids", [])
            ordered = self._map_ranked_candidates(candidates, ranked_ids)
            if not ordered:
                raise ValueError("No valid candidate ids returned")
            return {
                "sections": ordered[:top_k],
                "source": "groq",
                "model": data.get("model", self.model),
                "reason": parsed.get("reason", ""),
            }
        except (ValueError, OSError, error.HTTPError, error.URLError, json.JSONDecodeError):
            return {
                "sections": fallback_sections,
                "source": "local_fallback",
                "model": None,
                "reason": "fallback deterministic ranking",
            }

    def _build_local_understanding(
        self,
        *,
        query: str,
        jurisdiction_hint: Optional[str],
        domain_hint: Optional[str],
    ) -> Dict[str, Any]:
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", query.lower())
        keywords = []
        for token in tokens:
            normalized = token.strip("_-")
            if len(normalized) <= 2 or normalized in STOPWORDS or normalized.isdigit():
                continue
            if normalized not in keywords:
                keywords.append(normalized)

        section_hints = self._extract_section_hints(query)
        act_hints = self._extract_act_hints(query.lower())
        suggested_jurisdiction = self._detect_jurisdiction(query.lower(), jurisdiction_hint)
        suggested_domain = self._detect_domain(query.lower(), domain_hint)
        intent = self._detect_intent(query.lower())

        search_queries = [query.strip()]
        if keywords:
            search_queries.append(" ".join(keywords[:8]))
        if act_hints and keywords:
            search_queries.append(" ".join(act_hints[:2] + keywords[:6]))
        if section_hints:
            search_queries.append(f"{query.strip()} section {' '.join(section_hints[:4])}")
        if "property_real_estate_laws" in act_hints and any(term in query.lower() for term in ["delay", "delayed", "not built", "not build", "possession", "project", "building"]):
            search_queries.append("builder delayed possession rera refund interest")
            for term in ["builder", "possession", "delay", "rera", "refund", "interest"]:
                if term not in keywords:
                    keywords.append(term)
        if "labour_employment_laws" in act_hints and any(term in query.lower() for term in ["boss", "salary", "wages", "not paying", "unpaid", "paying me"]):
            search_queries.append("salary unpaid wages employer payment of wages")
            for term in ["salary", "wages", "employer", "payment", "unpaid"]:
                if term not in keywords:
                    keywords.append(term)
        if "sarfaesi" in act_hints:
            search_queries.append("sarfaesi section 13(2) 13(4) section 17 section 18 drt appeal")
        if "transfer_of_property_act" in act_hints and any(term in query.lower() for term in ["land", "property", "title", "possession"]):
            search_queries.append("property title possession injunction transfer of property specific relief registration")

        deduped_queries = []
        seen = set()
        for item in search_queries:
            candidate = " ".join(item.split())
            if candidate and candidate not in seen:
                seen.add(candidate)
                deduped_queries.append(candidate)

        summary_parts = []
        if suggested_domain:
            summary_parts.append(f"{suggested_domain} issue")
        if keywords:
            summary_parts.append(", ".join(keywords[:4]))
        summary = " | ".join(summary_parts) if summary_parts else "general legal query"

        return {
            "summary": summary,
            "intent": intent,
            "keywords": keywords[:12],
            "search_queries": deduped_queries[:5],
            "section_hints": section_hints[:8],
            "act_hints": act_hints[:8],
            "suggested_jurisdiction": suggested_jurisdiction,
            "suggested_domain": suggested_domain,
        }

    def _normalize_understanding(self, parsed: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(fallback)

        summary = parsed.get("summary")
        if isinstance(summary, str) and summary.strip():
            normalized["summary"] = summary.strip()[:300]

        intent = parsed.get("intent")
        if isinstance(intent, str) and intent.strip():
            normalized["intent"] = intent.strip().lower()[:40]

        for key in ("keywords", "search_queries", "section_hints", "act_hints"):
            values = parsed.get(key)
            if isinstance(values, list):
                cleaned = []
                for value in values:
                    if isinstance(value, str):
                        item = value.strip()
                        if item and item not in cleaned:
                            cleaned.append(item)
                if cleaned:
                    if key == "section_hints":
                        normalized[key] = self._normalize_section_hints(cleaned)[:12]
                    elif key == "act_hints":
                        normalized[key] = self._normalize_act_hints(cleaned)[:12]
                    else:
                        normalized[key] = cleaned[:12]

        jurisdiction = parsed.get("suggested_jurisdiction")
        if isinstance(jurisdiction, str):
            jurisdiction = jurisdiction.strip().upper()
            if jurisdiction in VALID_JURISDICTIONS:
                normalized["suggested_jurisdiction"] = jurisdiction

        domain = parsed.get("suggested_domain")
        if isinstance(domain, str):
            domain = self._map_legacy_domain(domain.strip().lower())
            if domain in VALID_DOMAINS:
                normalized["suggested_domain"] = domain

        return normalized

    def _local_rerank(self, query: str, sections: List[Any], understanding: Dict[str, Any]) -> List[Any]:
        query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        keyword_terms = set(normalize_issue_values(understanding.get("keywords", [])))
        section_hints = set(normalize_issue_values(understanding.get("section_hints", [])))
        act_hints = set(normalize_issue_values(understanding.get("act_hints", [])))
        preferred_sections = build_issue_priority_map(understanding.get("preferred_sections", []))
        preferred_title_terms = set(normalize_issue_values(understanding.get("preferred_title_terms", [])))
        excluded_title_terms = set(normalize_issue_values(understanding.get("excluded_title_terms", [])))
        preferred_act_names = build_issue_priority_map(understanding.get("preferred_act_names", []))
        preferred_act_fragments = build_issue_priority_map(understanding.get("preferred_act_fragments", []))
        preferred_section_acts = {
            str(section).strip().lower(): normalize_issue_values(act_names)
            for section, act_names in (understanding.get("preferred_section_acts", {}) or {}).items()
            if str(section).strip()
        }
        legal_issue = str(understanding.get("legal_issue", "")).replace("_", " ").lower()
        primary_act_name = str(understanding.get("primary_act_name", "")).lower()
        primary_act_fragment = str(understanding.get("primary_act_fragment", "")).lower()

        scored = []
        for index, section in enumerate(sections):
            section_text = getattr(section, "text", "").lower()
            act_id = getattr(section, "act_id", "").lower()
            section_number = getattr(section, "section_number", "").lower()
            title = str(getattr(section, "title", "")).lower()
            act_name = str(getattr(section, "act", "")).lower()
            metadata_text = ""
            if getattr(section, "metadata", None):
                metadata_text = json.dumps(section.metadata, sort_keys=True).lower()
                act_name = str(section.metadata.get("act_name", act_name)).lower()

            score = max(0, 100 - index)
            score += sum(8 for term in query_terms if len(term) > 2 and term in section_text)
            score += sum(10 for term in keyword_terms if term in section_text or term in act_id or term in title)
            score += sum(40 for hint in section_hints if hint == section_number or hint in section_number)
            score += sum(18 for hint in act_hints if hint in act_id)
            if primary_act_name and primary_act_name in act_name:
                score += 28
            if primary_act_fragment and primary_act_fragment in act_id:
                score += 28
            if act_name in preferred_act_names:
                score += 10 + (preferred_act_names[act_name] * 10)
            fragment_matches = [
                priority
                for fragment, priority in preferred_act_fragments.items()
                if fragment in act_id
            ]
            if fragment_matches:
                score += 8 + (max(fragment_matches) * 8)
            section_act_targets = preferred_section_acts.get(section_number, [])
            section_act_match = not section_act_targets or act_name in section_act_targets
            if preferred_sections and section_number in preferred_sections and section_act_match:
                score += 60 + (preferred_sections[section_number] * 18)
            elif preferred_sections and section_number in preferred_sections and not section_act_match:
                score -= 36
            elif preferred_sections:
                score -= 24
            if legal_issue and legal_issue in f"{title} {section_text}":
                score += 16
            score += sum(14 for term in preferred_title_terms if term and (term in title or term in section_text))
            if excluded_title_terms and any(term in title or term in section_text for term in excluded_title_terms):
                score -= 24
            if metadata_text:
                score += sum(4 for term in keyword_terms if term in metadata_text)

            scored.append((section, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [section for section, _ in scored]

    def _post_chat_completion(self, prompt: str) -> Dict[str, Any]:
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "system",
                        "content": "Return concise structured output. Do not invent legal authorities.",
                    },
                    {"role": "user", "content": prompt},
                ],
            }
        ).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "NyayaAI/1.0",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _extract_json_object(content: str) -> Dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            text = re.sub(r"```$", "", text).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("No JSON object found in Groq response")
        return json.loads(text[start : end + 1])

    @staticmethod
    def _map_ranked_candidates(candidates: List[Any], ranked_ids: List[Any]) -> List[Any]:
        id_map = {index: section for index, section in enumerate(candidates, start=1)}
        ordered = []
        seen = set()
        for item in ranked_ids:
            try:
                numeric_id = int(item)
            except (TypeError, ValueError):
                continue
            if numeric_id in id_map and numeric_id not in seen:
                ordered.append(id_map[numeric_id])
                seen.add(numeric_id)
        for index, section in enumerate(candidates, start=1):
            if index not in seen:
                ordered.append(section)
        return ordered

    @staticmethod
    def _extract_section_hints(query: str) -> List[str]:
        hints = []
        for pattern in (
            r"\bsection(?:s)?\s+([0-9A-Za-z, /\-]+)",
            r"\barticle(?:s)?\s+([0-9A-Za-z, /\-]+)",
        ):
            for match in re.findall(pattern, query, flags=re.IGNORECASE):
                parts = re.split(r"[,/ ]+", match)
                for part in parts:
                    value = part.strip()
                    if value and any(char.isdigit() for char in value) and value not in hints:
                        hints.append(value)
        return hints

    @staticmethod
    def _normalize_section_hints(values: List[str]) -> List[str]:
        hints: List[str] = []
        for value in values:
            text = str(value).lower()
            for match in re.findall(r"\b\d+(?:\(\d+\))?[a-z]{0,2}\b", text):
                if match not in hints:
                    hints.append(match)
        return hints

    @staticmethod
    def _normalize_act_hints(values: List[str]) -> List[str]:
        normalized = normalize_issue_values(values)
        for hint in list(normalized):
            for act_id, triggers in ACT_HINT_RULES.items():
                if any(trigger in hint for trigger in triggers):
                    if act_id not in normalized:
                        normalized.append(act_id)
        return normalized

    @staticmethod
    def _extract_act_hints(query_lower: str) -> List[str]:
        hints = []
        for act_id, triggers in ACT_HINT_RULES.items():
            if any(trigger in query_lower for trigger in triggers):
                hints.append(act_id)
        return hints

    @staticmethod
    def _detect_jurisdiction(query_lower: str, jurisdiction_hint: Optional[str]) -> Optional[str]:
        if jurisdiction_hint:
            hint = jurisdiction_hint.strip().upper()
            if hint in VALID_JURISDICTIONS:
                return hint
            if hint == "INDIA":
                return "IN"
        if any(term in query_lower for term in ["india", "indian", "ipc", "bns", "fir", "crpc", "bnss"]):
            return "IN"
        if any(term in query_lower for term in ["uk", "britain", "england", "cps", "crown court"]):
            return "UK"
        if any(term in query_lower for term in ["uae", "dubai", "abu dhabi", "emirates", "aed"]):
            return "UAE"
        return None

    @staticmethod
    def _detect_domain(query_lower: str, domain_hint: Optional[str]) -> Optional[str]:
        if domain_hint:
            hint = GroqRetrievalAugmentor._map_legacy_domain(domain_hint.strip().lower())
            if hint in VALID_DOMAINS:
                return hint
        if any(term in query_lower for term in ["theft", "murder", "rape", "assault", "fir", "arrest", "cybercrime"]):
            return "criminal"
        if any(term in query_lower for term in ["divorce", "custody", "marriage", "alimony"]):
            return "family"
        if any(term in query_lower for term in ["consumer", "defective", "refund", "consumer court"]):
            return "consumer"
        if any(term in query_lower for term in ["salary", "termination", "employment", "boss", "wages", "unpaid salary", "not paying me"]):
            return "civil"
        if any(term in query_lower for term in ["tax", "gst", "cgst", "igst", "sgst", "tds", "input tax credit", "itc", "assessment"]):
            return "civil"
        if any(term in query_lower for term in ["property", "eviction", "rent", "contract", "damages", "sale deed", "injunction"]):
            return "civil"
        return None

    @staticmethod
    def _map_legacy_domain(domain: str) -> str:
        if domain in {"civil_property", "banking", "employment", "tax"}:
            return "civil"
        if domain == "cyber":
            return "criminal"
        return domain

    @staticmethod
    def _detect_intent(query_lower: str) -> str:
        if any(term in query_lower for term in ["punishment", "penalty", "sentence", "fine", "jail"]):
            return "penalty"
        if any(term in query_lower for term in ["how", "procedure", "file", "process", "steps", "where do i"]):
            return "procedure"
        if any(term in query_lower for term in ["rights", "can i", "am i entitled", "remedy", "compensation"]):
            return "rights"
        if any(term in query_lower for term in ["remedy", "recover", "compensation", "damages"]):
            return "remedy"
        return "general"

    @staticmethod
    def _normalize_hint(value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, "value"):
            value = value.value
        return str(value)


groq_retrieval_augmentor = GroqRetrievalAugmentor()
