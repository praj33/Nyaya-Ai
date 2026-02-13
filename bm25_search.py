"""
BM25 Ranking for Legal Search
Industry-standard full-text search algorithm used by Elasticsearch
Optimized for large legal databases with 2000+ sections
"""

import math
from typing import List, Dict, Tuple
from collections import Counter
import re

class BM25Ranker:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 ranker
        
        Args:
            k1: Term frequency saturation parameter (1.2-2.0)
            b: Length normalization parameter (0.75 default)
        """
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = {}
        self.idf = {}
        self.doc_len = []
        self.avgdl = 0
        self.N = 0
        
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove special characters, lowercase, split
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [word for word in text.split() if len(word) > 2]
    
    def fit(self, corpus: List[str]):
        """
        Build BM25 index from corpus
        
        Args:
            corpus: List of document texts (section texts)
        """
        self.corpus = corpus
        self.N = len(corpus)
        
        # Calculate document frequencies
        df = {}
        for doc in corpus:
            tokens = set(self.tokenize(doc))
            for token in tokens:
                df[token] = df.get(token, 0) + 1
        
        self.doc_freqs = df
        
        # Calculate IDF (Inverse Document Frequency)
        for word, freq in df.items():
            self.idf[word] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1)
        
        # Calculate document lengths
        self.doc_len = [len(self.tokenize(doc)) for doc in corpus]
        self.avgdl = sum(self.doc_len) / self.N if self.N > 0 else 0
    
    def score(self, query: str, doc_idx: int) -> float:
        """
        Calculate BM25 score for a document given a query
        
        Args:
            query: Search query
            doc_idx: Document index in corpus
            
        Returns:
            BM25 score (higher is better)
        """
        score = 0.0
        doc = self.corpus[doc_idx]
        doc_tokens = self.tokenize(doc)
        doc_len = self.doc_len[doc_idx]
        
        # Count term frequencies in document
        tf = Counter(doc_tokens)
        
        # Calculate BM25 score for each query term
        for term in self.tokenize(query):
            if term not in self.idf:
                continue
            
            # Term frequency in document
            term_freq = tf.get(term, 0)
            
            # BM25 formula
            numerator = term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            
            score += self.idf[term] * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search corpus and return top-k documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_idx, score) tuples sorted by score
        """
        scores = [(idx, self.score(query, idx)) for idx in range(self.N)]
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    def batch_search(self, queries: List[str], top_k: int = 10) -> List[List[Tuple[int, float]]]:
        """
        Search multiple queries efficiently
        
        Args:
            queries: List of search queries
            top_k: Number of results per query
            
        Returns:
            List of result lists
        """
        return [self.search(query, top_k) for query in queries]


class LegalBM25Search:
    """BM25 search optimized for legal sections"""
    
    def __init__(self):
        self.ranker = BM25Ranker(k1=1.5, b=0.75)
        self.sections = []
        self.indexed = False
    
    def index_sections(self, sections: List):
        """
        Index legal sections for BM25 search
        
        Args:
            sections: List of Section objects
        """
        self.sections = sections
        
        # Build corpus from section texts
        corpus = [section.text for section in sections]
        
        # Fit BM25 ranker
        self.ranker.fit(corpus)
        self.indexed = True
        
        print(f"OK: BM25 index built for {len(sections)} sections")
    
    def search(self, query: str, jurisdiction: str = None, top_k: int = 10) -> List[Tuple]:
        """
        Search sections using BM25 ranking
        
        Args:
            query: Search query
            jurisdiction: Filter by jurisdiction (optional)
            top_k: Number of results
            
        Returns:
            List of (section, score) tuples
        """
        if not self.indexed:
            return []
        
        # Get BM25 scores
        results = self.ranker.search(query, top_k=len(self.sections))
        
        # Convert to section objects and filter by jurisdiction
        section_results = []
        for doc_idx, score in results:
            section = self.sections[doc_idx]
            
            # Filter by jurisdiction if specified
            if jurisdiction and section.jurisdiction.value != jurisdiction:
                continue
            
            # Only include sections with positive scores
            if score > 0:
                section_results.append((section, score))
            
            # Stop when we have enough results
            if len(section_results) >= top_k:
                break
        
        return section_results
    
    def multi_field_search(self, query: str, jurisdiction: str = None, 
                          boost_act: str = None, top_k: int = 10) -> List[Tuple]:
        """
        Enhanced search with act boosting
        
        Args:
            query: Search query
            jurisdiction: Filter by jurisdiction
            boost_act: Act ID to boost in results
            top_k: Number of results
            
        Returns:
            List of (section, score) tuples
        """
        results = self.search(query, jurisdiction, top_k * 2)
        
        # Boost specific act if specified
        if boost_act:
            boosted_results = []
            for section, score in results:
                if boost_act in section.act_id.lower():
                    score *= 1.5  # 50% boost for matching act
                boosted_results.append((section, score))
            
            # Re-sort after boosting
            boosted_results.sort(key=lambda x: x[1], reverse=True)
            return boosted_results[:top_k]
        
        return results[:top_k]
