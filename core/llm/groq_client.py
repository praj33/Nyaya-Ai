"""Optional Groq-backed response generation.

Local statutes, procedures, and enforcement remain the source of truth.
This module only turns retrieved data into a clearer narrative answer.
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional
from urllib import error, request

from dotenv import load_dotenv, find_dotenv

_dotenv_path = find_dotenv(usecwd=False)
load_dotenv(_dotenv_path or None)


class GroqResponseGenerator:
    """Builds a user-facing answer from retrieved legal artifacts."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        self.timeout_seconds = float(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))
        self.enabled = os.getenv("GROQ_ENABLED", "true").lower() not in {"0", "false", "no"}
        self.debug = os.getenv("GROQ_DEBUG", "false").lower() not in {"0", "false", "no"}

    def _disabled_reason(self) -> Optional[str]:
        if not self.enabled:
            return "GROQ_ENABLED is false"
        if not self.api_key:
            return "GROQ_API_KEY missing"
        return None

    def generate_answer(
        self,
        *,
        query: str,
        jurisdiction: str,
        domain: str,
        statutes: List[Any],
        case_laws: List[Any],
        procedural_steps: List[str],
        remedies: List[str],
        timeline: List[Dict[str, str]],
        evidence_requirements: List[str],
        enforcement_decision: str,
        legal_analysis: str,
        query_understanding: Optional[Dict[str, Any]] = None,
        retrieval_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Optional[str]]:
        """Return a Groq answer when configured, else a deterministic local answer."""
        fallback_answer = self._build_local_answer(
            query=query,
            jurisdiction=jurisdiction,
            domain=domain,
            statutes=statutes,
            case_laws=case_laws,
            procedural_steps=procedural_steps,
            remedies=remedies,
            timeline=timeline,
            evidence_requirements=evidence_requirements,
            enforcement_decision=enforcement_decision,
            legal_analysis=legal_analysis,
            query_understanding=query_understanding,
            retrieval_metadata=retrieval_metadata,
        )

        disabled_reason = self._disabled_reason()
        if disabled_reason:
            if self.debug:
                print(f"GroqResponseGenerator disabled: {disabled_reason}")
            response = {
                "text": fallback_answer,
                "source": "local",
                "model": None,
            }
            if self.debug:
                response["reason"] = disabled_reason
            return response

        try:
            prompt = self._build_prompt(
                query=query,
                jurisdiction=jurisdiction,
                domain=domain,
                statutes=statutes,
                case_laws=case_laws,
                procedural_steps=procedural_steps,
                remedies=remedies,
                timeline=timeline,
                evidence_requirements=evidence_requirements,
                enforcement_decision=enforcement_decision,
                legal_analysis=legal_analysis,
                query_understanding=query_understanding,
                retrieval_metadata=retrieval_metadata,
            )
            payload = json.dumps(
                {
                    "model": self.model,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a legal response formatter. Use only the supplied statutes, "
                                "procedures, case laws, and enforcement result. Do not invent laws, "
                                "sections, punishments, timelines, or procedure steps. If data is missing, "
                                "say it is unavailable in the retrieved records."
                            ),
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
                data = json.loads(response.read().decode("utf-8"))
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if not text:
                raise ValueError("Groq returned an empty answer")

            return {
                "text": text,
                "source": "groq",
                "model": data.get("model", self.model),
            }
        except (ValueError, OSError, error.HTTPError, error.URLError) as exc:
            if self.debug:
                print(f"GroqResponseGenerator fallback: {exc}")
            response = {
                "text": fallback_answer,
                "source": "local_fallback",
                "model": None,
            }
            if self.debug:
                response["error"] = f"{type(exc).__name__}: {exc}"
            return response

    def _build_prompt(
        self,
        *,
        query: str,
        jurisdiction: str,
        domain: str,
        statutes: List[Any],
        case_laws: List[Any],
        procedural_steps: List[str],
        remedies: List[str],
        timeline: List[Dict[str, str]],
        evidence_requirements: List[str],
        enforcement_decision: str,
        legal_analysis: str,
        query_understanding: Optional[Dict[str, Any]],
        retrieval_metadata: Optional[Dict[str, Any]],
    ) -> str:
        statute_lines = []
        for statute in statutes[:5]:
            statute_lines.append(
                f"- Section {self._read_field(statute, 'section')} of "
                f"{self._read_field(statute, 'act')} ({self._read_field(statute, 'year')}): "
                f"{self._read_field(statute, 'title')}"
            )

        case_lines = []
        for case in case_laws[:3]:
            case_lines.append(
                f"- {self._read_field(case, 'title')} ({self._read_field(case, 'year')}), "
                f"{self._read_field(case, 'court')}: {self._read_field(case, 'principle')}"
            )

        timeline_lines = [
            f"- {step.get('step', 'Unknown step')} (ETA: {step.get('eta', 'Varies')})"
            for step in timeline[:4]
        ]

        procedure_lines = [f"- {step}" for step in procedural_steps[:5]]
        remedy_lines = [f"- {remedy}" for remedy in remedies[:5]]
        evidence_lines = [f"- {item}" for item in evidence_requirements[:5]]

        return "\n".join(
            [
                "Write a concise legal answer in plain English.",
                "Structure: short answer, key statutes, procedure, enforcement status, practical next steps.",
                "Mention exact section numbers and act names only from the provided data.",
                "",
                f"User query: {query}",
                f"Jurisdiction: {jurisdiction}",
                f"Domain: {domain}",
                f"Enforcement decision: {enforcement_decision}",
                f"Query understanding: {(query_understanding or {}).get('summary', 'None')}",
                f"User intent: {(query_understanding or {}).get('intent', 'general')}",
                f"Search terms used: {(retrieval_metadata or {}).get('search_queries', [])}",
                "",
                "Retrieved statutes:",
                "\n".join(statute_lines) if statute_lines else "- None retrieved",
                "",
                "Retrieved case laws:",
                "\n".join(case_lines) if case_lines else "- None retrieved",
                "",
                "Procedure timeline from files:",
                "\n".join(timeline_lines) if timeline_lines else "- None retrieved",
                "",
                "Detailed procedural steps from files:",
                "\n".join(procedure_lines) if procedure_lines else "- None retrieved",
                "",
                "Evidence requirements from files:",
                "\n".join(evidence_lines) if evidence_lines else "- None retrieved",
                "",
                "Remedies:",
                "\n".join(remedy_lines) if remedy_lines else "- None retrieved",
                "",
                "Existing deterministic legal analysis:",
                legal_analysis[:2500],
            ]
        )

    def _build_local_answer(
        self,
        *,
        query: str,
        jurisdiction: str,
        domain: str,
        statutes: List[Any],
        case_laws: List[Any],
        procedural_steps: List[str],
        remedies: List[str],
        timeline: List[Dict[str, str]],
        evidence_requirements: List[str],
        enforcement_decision: str,
        legal_analysis: str,
        query_understanding: Optional[Dict[str, Any]],
        retrieval_metadata: Optional[Dict[str, Any]],
    ) -> str:
        parts = [
            f"Query: {query}",
            f"Jurisdiction: {jurisdiction}. Domain: {domain}. Enforcement: {enforcement_decision}.",
        ]

        if query_understanding and query_understanding.get("summary"):
            parts.append(f"Understood request as: {query_understanding['summary']}.")

        if statutes:
            statute_summaries = []
            for statute in statutes[:3]:
                statute_summaries.append(
                    f"Section {self._read_field(statute, 'section')} of "
                    f"{self._read_field(statute, 'act')} ({self._read_field(statute, 'year')})"
                )
            parts.append("Relevant statutes: " + "; ".join(statute_summaries) + ".")

        if timeline:
            steps = [step.get("step", "Unknown step") for step in timeline[:3]]
            parts.append("Procedure timeline: " + " -> ".join(steps) + ".")
        elif procedural_steps:
            parts.append("Procedure guidance: " + " | ".join(procedural_steps[:3]) + ".")

        if evidence_requirements:
            parts.append("Evidence/documents: " + ", ".join(evidence_requirements[:4]) + ".")

        if remedies:
            visible_remedies = remedies[:5]
            remedies_text = "; ".join(visible_remedies)
            if len(remedies) > 5:
                remedies_text += f"; and {len(remedies) - 5} more"
            parts.append("Possible remedies: " + remedies_text + ".")

        if case_laws:
            first_case = case_laws[0]
            parts.append(
                "Relevant precedent: "
                f"{self._read_field(first_case, 'title')} ({self._read_field(first_case, 'year')})."
            )

        if legal_analysis:
            parts.append("Retrieved analysis: " + legal_analysis.splitlines()[0])
        elif retrieval_metadata and retrieval_metadata.get("search_queries"):
            parts.append(
                "Search basis: " + ", ".join(retrieval_metadata["search_queries"][:3]) + "."
            )

        if not statutes:
            parts.append("No exact statutes were retrieved from the DB for this query, so the response is generic guidance based on the matched legal context.")

        return " ".join(parts)

    @staticmethod
    def _read_field(item: Any, field_name: str) -> str:
        if isinstance(item, dict):
            value = item.get(field_name, "")
        else:
            value = getattr(item, field_name, "")
        return str(value) if value is not None else ""


groq_response_generator = GroqResponseGenerator()
