"""Procedure loader for legal procedure datasets."""
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class ProcedureLoader:
    """Loads and manages legal procedure datasets."""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # Point to nyaya-legal-procedure-datasets
            current_dir = Path(__file__).parent.parent.parent
            base_path = current_dir / "nyaya-legal-procedure-datasets" / "data" / "procedures"
        self.base_path = Path(base_path)
        self.procedures_cache: Dict[str, Dict[str, Any]] = {}
        self.schemas_cache: Dict[str, Any] = {}
        self._load_schemas()
        self._load_procedures()
    
    def _load_schemas(self):
        """Load all schema files."""
        # Schemas are in nyaya-legal-procedure-datasets/data/schema
        schemas_path = self.base_path.parent / "schema"
        if not schemas_path.exists():
            return
        
        for schema_file in schemas_path.glob("*.json"):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_name = schema_file.stem
                    self.schemas_cache[schema_name] = json.load(f)
            except Exception as e:
                print(f"Error loading schema {schema_file}: {e}")
    
    def _load_procedures(self):
        """Load all procedure files."""
        if not self.base_path.exists():
            return
        
        for country_dir in self.base_path.iterdir():
            if not country_dir.is_dir():
                continue
            
            country = country_dir.name
            self.procedures_cache[country] = {}
            
            for proc_file in country_dir.glob("*.json"):
                try:
                    with open(proc_file, 'r', encoding='utf-8') as f:
                        domain = proc_file.stem
                        self.procedures_cache[country][domain] = json.load(f)
                except Exception as e:
                    print(f"Error loading procedure {proc_file}: {e}")
    
    def get_procedure(self, country: str, domain: str) -> Optional[Dict[str, Any]]:
        """Get procedure for a specific country and domain."""
        return self.procedures_cache.get(country, {}).get(domain)
    
    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific schema."""
        return self.schemas_cache.get(schema_name)
    
    def get_canonical_taxonomy(self) -> Dict[str, Any]:
        """Get canonical taxonomy schema."""
        return self.get_schema("canonical_taxonomy_v1.2") or {}
    
    def get_evidence_readiness(self) -> Dict[str, Any]:
        """Get evidence readiness schema."""
        return self.get_schema("evidence_readiness_v2") or {}
    
    def get_failure_paths(self) -> Dict[str, Any]:
        """Get failure paths schema."""
        return self.get_schema("failure_paths_v2") or {}
    
    def get_system_compliance(self) -> Dict[str, Any]:
        """Get system compliance schema."""
        return self.get_schema("system_compliance_v2") or {}
    
    def list_available_procedures(self) -> Dict[str, List[str]]:
        """List all available procedures by country."""
        return {
            country: list(domains.keys())
            for country, domains in self.procedures_cache.items()
        }
    
    def get_procedure_steps(self, country: str, domain: str) -> List[Dict[str, Any]]:
        """Get procedure steps for a specific country and domain."""
        procedure = self.get_procedure(country, domain)
        if procedure and "procedure" in procedure:
            return procedure["procedure"].get("steps", [])
        return []
    
    def get_step_by_canonical(self, country: str, domain: str, canonical_step: str) -> Optional[Dict[str, Any]]:
        """Get a specific step by its canonical name."""
        steps = self.get_procedure_steps(country, domain)
        for step in steps:
            if step.get("canonical_step") == canonical_step:
                return step
        return None
    
    def calculate_evidence_penalty(self, evidence_state: str) -> float:
        """Calculate confidence penalty based on evidence state."""
        evidence_schema = self.get_evidence_readiness()
        penalties = evidence_schema.get("confidence_penalties", {})
        return penalties.get(evidence_state, 0.0)
    
    def get_failure_info(self, failure_code: str) -> Optional[Dict[str, Any]]:
        """Get failure information by failure code."""
        failure_schema = self.get_failure_paths()
        failure_states = failure_schema.get("failure_states", [])
        for failure in failure_states:
            if failure.get("failure_code") == failure_code:
                return failure
        return None


# Global instance
procedure_loader = ProcedureLoader()
