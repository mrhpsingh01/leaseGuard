"""
Hybrid Statutory Retriever for LeaseGuard
Combines Okapi BM25 lexical token matching and Dense Cosine Vector similarity
using Reciprocal Rank Fusion (RRF) to ground lease clauses in official Georgia statutes.
"""

import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from typing import Optional
from apps.api.models.lease import RetrievalScore
from apps.api.services.statute_store import StatuteStore, embed, statute_corpus_text

class OkapiBM25:
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = []
        self.doc_freqs: Dict[str, int] = {}
        self.doc_term_freqs: List[Dict[str, int]] = []
        
        total_len = 0
        for doc in corpus:
            tokens = self.tokenize(doc)
            self.doc_lengths.append(len(tokens))
            total_len += len(tokens)
            
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freqs.append(tf)

            for t in tf:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avgdl = total_len / max(self.corpus_size, 1)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r'[A-Za-z0-9\-]+', text.lower())

    def idf(self, term: str) -> float:
        n = self.doc_freqs.get(term, 0)
        return math.log((self.corpus_size - n + 0.5) / (n + 0.5) + 1.0)

    def score_query(self, query: str) -> List[float]:
        q_tokens = self.tokenize(query)
        scores = [0.0] * self.corpus_size

        for i, tf in enumerate(self.doc_term_freqs):
            dl = self.doc_lengths[i]
            doc_score = 0.0
            for t in q_tokens:
                if t in tf:
                    f = tf[t]
                    idf = self.idf(t)
                    num = f * (self.k1 + 1.0)
                    denom = f + self.k1 * (1.0 - self.b + self.b * (dl / max(self.avgdl, 1e-6)))
                    doc_score += idf * (num / denom)
            scores[i] = doc_score
        return scores


class HybridRetrieverService:
    """BM25 (lexical) + cosine vector (dense, pgvector or in-memory) fused with Reciprocal Rank Fusion."""

    def __init__(self, statutes_path: Optional[str] = None, store: Optional[StatuteStore] = None):
        self.store = store or StatuteStore(statutes_path=statutes_path)
        self.statutes: List[Dict[str, Any]] = self.store.statutes
        self.corpus_texts = [statute_corpus_text(s) for s in self.statutes]
        self.bm25 = OkapiBM25(self.corpus_texts)
        self.vector_matrix = np.vstack([embed(t) for t in self.corpus_texts])

    @property
    def storage_mode(self) -> str:
        return self.store.mode

    def _dense_scores(self, query: str) -> List[float]:
        pg = self.store.pg_cosine_scores(query)
        if pg is not None and all(s["rule_id"] in pg for s in self.statutes):
            return [pg[s["rule_id"]] for s in self.statutes]
        return (self.vector_matrix @ embed(query)).tolist()  # both L2-normalised -> cosine

    def retrieve(self, query: str, top_k: int = 3, rrf_k: int = 60) -> List[Tuple[Dict[str, Any], RetrievalScore]]:
        bm25_raw_scores = self.bm25.score_query(query)
        dense_raw_scores = self._dense_scores(query)

        bm25_rank_map = {int(idx): rank + 1 for rank, idx in enumerate(np.argsort(bm25_raw_scores, kind="stable")[::-1])}
        dense_rank_map = {int(idx): rank + 1 for rank, idx in enumerate(np.argsort(dense_raw_scores, kind="stable")[::-1])}

        candidates = []
        for i, statute in enumerate(self.statutes):
            rrf_score = 1.0 / (rrf_k + bm25_rank_map[i]) + 1.0 / (rrf_k + dense_rank_map[i])
            meta = RetrievalScore(
                rule_id=statute["rule_id"],
                statute_section=statute["section"],
                bm25_score=round(float(bm25_raw_scores[i]), 4),
                vector_score=round(float(dense_raw_scores[i]), 4),
                rrf_score=round(float(rrf_score), 6),
                bm25_rank=bm25_rank_map[i],
                vector_rank=dense_rank_map[i],
            )
            candidates.append((statute, meta, rrf_score))

        candidates.sort(key=lambda x: x[2], reverse=True)
        return [(c[0], c[1]) for c in candidates[:top_k]]
