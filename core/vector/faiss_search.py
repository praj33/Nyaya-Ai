import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict
from core.vector.embedding_model import EmbeddingModel

class FAISSSearch:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.vector_dir = self.data_dir / "vector_index"
        self.embedder = EmbeddingModel()
        self.statute_index = None
        self.statute_metadata = None
        self.caselaw_index = None
        self.caselaw_metadata = None
    
    def load_indexes(self):
        statute_index_path = self.vector_dir / "statutes.index"
        statute_meta_path = self.vector_dir / "statutes_meta.json"
        caselaw_index_path = self.vector_dir / "caselaw.index"
        caselaw_meta_path = self.vector_dir / "caselaw_meta.json"
        
        if statute_index_path.exists() and statute_meta_path.exists():
            self.statute_index = faiss.read_index(str(statute_index_path))
            with open(statute_meta_path, 'r', encoding='utf-8') as f:
                self.statute_metadata = json.load(f)
        
        if caselaw_index_path.exists() and caselaw_meta_path.exists():
            self.caselaw_index = faiss.read_index(str(caselaw_index_path))
            with open(caselaw_meta_path, 'r', encoding='utf-8') as f:
                self.caselaw_metadata = json.load(f)
    
    def search_statutes(self, query: str, k: int = 10) -> List[Tuple[Dict, float]]:
        if self.statute_index is None or self.statute_metadata is None:
            return []
        
        query_embedding = self.embedder.encode([query]).astype('float32')
        distances, indices = self.statute_index.search(query_embedding, k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.statute_metadata):
                results.append((self.statute_metadata[idx], float(dist)))
        
        return results
    
    def search_caselaws(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        if self.caselaw_index is None or self.caselaw_metadata is None:
            return []
        
        query_embedding = self.embedder.encode([query]).astype('float32')
        distances, indices = self.caselaw_index.search(query_embedding, k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.caselaw_metadata):
                results.append((self.caselaw_metadata[idx], float(dist)))
        
        return results
