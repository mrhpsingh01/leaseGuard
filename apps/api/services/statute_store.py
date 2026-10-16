"""
Statute storage for LeaseGuard.

Primary mode  : PostgreSQL + pgvector (when DATABASE_URL is set and reachable).
Fallback mode : SQLite seeded from georgia_statutes.json on startup (zero-config; never crashes cold start).
The dense embedding is a deterministic 384-dim hashed bag-of-ngrams vector (matches schema.sql vector(384)).
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from apps.api import config

EMBED_DIM = 384
_hasher = HashingVectorizer(
    n_features=EMBED_DIM, ngram_range=(1, 2), stop_words="english",
    alternate_sign=False, norm="l2", lowercase=True,
)


def statute_corpus_text(s: Dict[str, Any]) -> str:
    return (f"{s['rule_id']} {s['statute_title']} {s['section']} {s['statutory_requirement']} "
            f"{s['rule_summary']} {s['full_text']} {' '.join(s.get('keywords', []))}")


def embed(text: str) -> np.ndarray:
    return _hasher.transform([text]).toarray()[0]


def _vec_literal(v: np.ndarray) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


class StatuteStore:
    def __init__(self, statutes_path: Optional[str] = None, database_url: Optional[str] = None,
                 sqlite_path: Optional[str] = None):
        self.statutes_path = str(statutes_path or config.STATUTES_PATH)
        self.database_url = database_url if database_url is not None else config.DATABASE_URL
        self.sqlite_path = str(sqlite_path or config.SQLITE_PATH)
        self.mode = "local_fallback"
        self.pg_error: Optional[str] = None
        self.statutes: List[Dict[str, Any]] = []
        self._load()

    def _load_json(self) -> List[Dict[str, Any]]:
        with open(self.statutes_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load(self) -> None:
        seed = self._load_json()
        if self.database_url:
            try:
                self.statutes = self._seed_pgvector(seed)
                self.mode = "pgvector"
                return
            except Exception as exc:  # unreachable DB, missing extension, bad creds...
                self.pg_error = f"{type(exc).__name__}: {exc}"
        self.statutes = self._seed_sqlite(seed)
        self.mode = "local_fallback"

    # ---------------- SQLite fallback ----------------
    def _seed_sqlite(self, seed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.sqlite_path)
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS georgia_statutes ("
                         "rule_id TEXT PRIMARY KEY, section TEXT NOT NULL, payload TEXT NOT NULL)")
            with conn:
                for s in seed:
                    conn.execute("INSERT OR REPLACE INTO georgia_statutes(rule_id, section, payload) VALUES (?,?,?)",
                                 (s["rule_id"], s["section"], json.dumps(s, ensure_ascii=False)))
            rows = conn.execute("SELECT payload FROM georgia_statutes ORDER BY rowid").fetchall()
        finally:
            conn.close()
        order = {s["rule_id"]: i for i, s in enumerate(seed)}
        loaded = [json.loads(r[0]) for r in rows]
        return sorted([s for s in loaded if s["rule_id"] in order], key=lambda s: order[s["rule_id"]])

    # ---------------- pgvector ----------------
    def _pg_connect(self):
        import psycopg2
        return psycopg2.connect(self.database_url, connect_timeout=5)

    def _seed_pgvector(self, seed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        conn = self._pg_connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS georgia_statutes ("
                    "id SERIAL PRIMARY KEY, rule_id VARCHAR(64) UNIQUE NOT NULL, statute_title VARCHAR(255) NOT NULL,"
                    "section VARCHAR(64) NOT NULL, category VARCHAR(64) NOT NULL DEFAULT '', "
                    "statutory_requirement TEXT NOT NULL, rule_summary TEXT NOT NULL, full_text TEXT NOT NULL,"
                    "remedy TEXT NOT NULL DEFAULT '', standard_counter_clause TEXT NOT NULL,"
                    "severity VARCHAR(16) NOT NULL DEFAULT 'HIGH', payload JSONB, embedding vector(384))")
                cur.execute("ALTER TABLE georgia_statutes ADD COLUMN IF NOT EXISTS payload JSONB")
                for s in seed:
                    cur.execute(
                        "INSERT INTO georgia_statutes(rule_id, statute_title, section, category, statutory_requirement,"
                        "rule_summary, full_text, remedy, standard_counter_clause, severity, payload, embedding) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector) "
                        "ON CONFLICT (rule_id) DO UPDATE SET payload=EXCLUDED.payload, embedding=EXCLUDED.embedding",
                        (s["rule_id"], s["statute_title"], s["section"], s.get("category", ""),
                         s["statutory_requirement"], s["rule_summary"], s["full_text"], s.get("remedy", ""),
                         s["standard_counter_clause"], s.get("severity", "HIGH"),
                         json.dumps(s, ensure_ascii=False), _vec_literal(embed(statute_corpus_text(s)))))
        finally:
            conn.close()
        return seed

    def pg_cosine_scores(self, query: str) -> Optional[Dict[str, float]]:
        """Cosine similarity per rule_id computed inside PostgreSQL via pgvector (`<=>`). None on failure."""
        if self.mode != "pgvector":
            return None
        try:
            conn = self._pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT rule_id, 1 - (embedding <=> %s::vector) FROM georgia_statutes",
                                (_vec_literal(embed(query)),))
                    return {r[0]: float(r[1]) for r in cur.fetchall()}
            finally:
                conn.close()
        except Exception:
            return None
