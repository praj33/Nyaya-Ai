import sys
sys.path.append('.')

from data_bridge.loader import JSONLoader
from core.vector.faiss_index import FAISSStatuteIndex
import os

def build_statute_index():
    """Build FAISS index from all statutes in database"""
    
    # Load all sections
    print("Loading statutes from database...")
    loader = JSONLoader("db")
    sections, acts, cases = loader.load_and_normalize_directory()
    
    print(f"Loaded {len(sections)} sections from {len(acts)} acts")
    
    # Build FAISS index
    print("\nBuilding FAISS index...")
    faiss_index = FAISSStatuteIndex()
    faiss_index.build_index(sections)
    
    # Save index
    index_dir = "data/vector_index"
    os.makedirs(index_dir, exist_ok=True)
    
    index_path = os.path.join(index_dir, "statutes.index")
    metadata_path = os.path.join(index_dir, "statutes_metadata.pkl")
    
    faiss_index.save_index(index_path, metadata_path)
    
    print("\nIndex building complete!")
    print(f"Total vectors: {faiss_index.index.ntotal}")
    
    # Test search
    print("\nTesting search...")
    test_query = "what is the punishment for theft"
    results = faiss_index.search(test_query, k=5, jurisdiction="IN")
    
    print(f"\nTop 5 results for: '{test_query}'")
    for i, (meta, score) in enumerate(results, 1):
        print(f"{i}. Section {meta['section']} ({meta['act']}) - Score: {score:.3f}")
        print(f"   {meta['title']}")

if __name__ == "__main__":
    build_statute_index()
