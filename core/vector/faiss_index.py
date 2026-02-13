import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

class FAISSStatuteIndex:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
    
    def build_index(self, sections: List[Any]):
        """Build FAISS index from sections"""
        texts = []
        metadata = []
        
        for section in sections:
            # Combine section number and text for better context
            text = f"Section {section.section_number}: {section.text}"
            texts.append(text)
            
            # Store metadata
            metadata.append({
                "act": section.act_id,
                "section": section.section_number,
                "title": section.text[:100],
                "jurisdiction": section.jurisdiction.value,
                "full_text": section.text
            })
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} sections...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Build FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.index.add(embeddings)
        self.metadata = metadata
        
        print(f"FAISS index built with {self.index.ntotal} vectors")
    
    def search(self, query: str, k: int = 10, jurisdiction: str = None, domain: str = None) -> List[Tuple[Dict[str, Any], float]]:
        """Search FAISS index with optional filtering"""
        if self.index is None:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search with larger k for filtering
        search_k = min(k * 10, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, search_k)
        
        # Filter and collect results
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            
            meta = self.metadata[idx]
            
            # Apply filters
            if jurisdiction and meta["jurisdiction"] != jurisdiction:
                continue
            
            results.append((meta, float(score)))
            
            if len(results) >= k:
                break
        
        return results
    
    def save_index(self, index_path: str, metadata_path: str):
        """Save FAISS index and metadata to disk"""
        if self.index is None:
            raise ValueError("No index to save")
        
        faiss.write_index(self.index, index_path)
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        print(f"Index saved to {index_path}")
        print(f"Metadata saved to {metadata_path}")
    
    def load_index(self, index_path: str, metadata_path: str):
        """Load FAISS index and metadata from disk"""
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            return False
        
        self.index = faiss.read_index(index_path)
        
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        
        print(f"Index loaded with {self.index.ntotal} vectors")
        return True
