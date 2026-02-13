import json
import os
import faiss
import numpy as np
from pathlib import Path
from core.vector.embedding_model import EmbeddingModel

class IndexBuilder:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.vector_dir = self.data_dir / "vector_index"
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        self.embedder = EmbeddingModel()
    
    def build_statute_index(self, statutes):
        texts = []
        metadata = []
        
        for statute in statutes:
            text = f"{statute.get('act', '')} Section {statute.get('section_number', '')} {statute.get('text', '')}"
            texts.append(text)
            metadata.append({
                'act': statute.get('act_id', ''),
                'section': statute.get('section_number', ''),
                'text': statute.get('text', ''),
                'jurisdiction': statute.get('jurisdiction', 'IN')
            })
        
        embeddings = self.embedder.encode(texts)
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype('float32'))
        
        faiss.write_index(index, str(self.vector_dir / "statutes.index"))
        
        with open(self.vector_dir / "statutes_meta.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return index, metadata
    
    def build_caselaw_index(self, caselaws):
        texts = []
        metadata = []
        
        for case in caselaws:
            text = f"{case.get('title', '')} {case.get('summary', '')} {case.get('keywords', '')}"
            texts.append(text)
            metadata.append({
                'title': case.get('title', ''),
                'citation': case.get('citation', ''),
                'year': case.get('year', ''),
                'summary': case.get('summary', ''),
                'keywords': case.get('keywords', [])
            })
        
        embeddings = self.embedder.encode(texts)
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype('float32'))
        
        faiss.write_index(index, str(self.vector_dir / "caselaw.index"))
        
        with open(self.vector_dir / "caselaw_meta.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return index, metadata
