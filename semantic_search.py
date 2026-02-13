"""
Semantic Legal Search using Sentence Transformers
Provides AI-powered query-to-section matching for Nyaya AI
"""

from typing import List, Tuple
import numpy as np

class SemanticLegalSearch:
    def __init__(self):
        self.model = None
        self.embeddings_cache = {}
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize sentence transformer model (lazy loading)"""
        try:
            from sentence_transformers import SentenceTransformer
            # Use lightweight model optimized for semantic search
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("OK: Semantic search enabled with sentence-transformers")
        except ImportError:
            print("⚠ sentence-transformers not installed. Using keyword-based search.")
            print("  Install with: pip install sentence-transformers")
            self.model = None
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text with caching"""
        if self.model is None:
            return None
        
        if text not in self.embeddings_cache:
            self.embeddings_cache[text] = self.model.encode(text, convert_to_numpy=True)
        
        return self.embeddings_cache[text]
    
    def compute_similarity(self, query: str, section_text: str) -> float:
        """Compute semantic similarity between query and section"""
        if self.model is None:
            return 0.0
        
        query_emb = self.get_embedding(query)
        section_emb = self.get_embedding(section_text)
        
        # Cosine similarity
        similarity = np.dot(query_emb, section_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(section_emb)
        )
        
        return float(similarity)
    
    def rank_sections(self, query: str, sections: List, top_k: int = 10) -> List[Tuple]:
        """Rank sections by semantic similarity to query"""
        if self.model is None or not sections:
            return [(s, 0.0) for s in sections[:top_k]]
        
        # Compute similarities
        scored_sections = []
        for section in sections:
            similarity = self.compute_similarity(query, section.text)
            scored_sections.append((section, similarity))
        
        # Sort by similarity
        scored_sections.sort(key=lambda x: x[1], reverse=True)
        
        return scored_sections[:top_k]
    
    def find_best_act(self, query: str, act_descriptions: dict) -> str:
        """Find best matching act for query using semantic similarity"""
        if self.model is None:
            return None
        
        best_act = None
        best_score = 0.0
        
        for act_name, description in act_descriptions.items():
            similarity = self.compute_similarity(query, description)
            if similarity > best_score:
                best_score = similarity
                best_act = act_name
        
        # Return act only if similarity is above threshold
        return best_act if best_score > 0.3 else None
