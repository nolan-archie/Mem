                                                                                                                                              



from __future__ import annotations

import os

import sqlite3

import json

import base64

import uuid

import threading

import shutil              

from dataclasses import dataclass, asdict

from typing import List, Dict, Any, Optional, Callable, Tuple

from pathlib import Path

from datetime import datetime, timezone



import requests

import numpy as np

from .utils.logging import log_action                                      



                  

try:

    import faiss

    FAISS_AVAILABLE = True

except Exception:

    faiss = None

    FAISS_AVAILABLE = False



try:

    from sentence_transformers import SentenceTransformer

    ST_AVAILABLE = True

except Exception:

    SentenceTransformer = None

    ST_AVAILABLE = False



           

ROOT = Path(__file__).resolve().parents[1]

DB_DIR = ROOT / "db"

DB_DIR.mkdir(parents=True, exist_ok=True)

SQLITE_PATH = DB_DIR / "memories.sqlite"

FAISS_INDEX_PATH = DB_DIR / "faiss.index"

DEFAULT_EMBED_URL = os.environ.get("MAINMI_EMBED_URL", "http://127.0.0.1:9000/embed")

DEFAULT_EMBED_MODEL_NAME = os.environ.get("MAINMI_EMBED_MODEL", "all-MiniLM-L6-v2")

DEFAULT_DIM = 384

SQLITE_TIMEOUT = 30



          

def _float32_to_b64(x: np.ndarray) -> str:

    return base64.b64encode(x.astype(np.float32).tobytes()).decode("ascii")



def _b64_to_float32(s: str) -> np.ndarray:

    b = base64.b64decode(s.encode("ascii"))

    return np.frombuffer(b, dtype=np.float32).copy()



def _normalize(vecs: np.ndarray) -> np.ndarray:

    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12

    return (vecs / norms).astype("float32")



               

@dataclass

class MemoryEntry:

    id: str

    text: str

    tags: List[str]

    created_at: str

    embedding_b64: str

    embedding_model: str



    def to_dict(self) -> Dict[str, Any]:

        return asdict(self)



             

class Embedder:

    def __init__(self, service_url: str = DEFAULT_EMBED_URL, local_model_name: str = DEFAULT_EMBED_MODEL_NAME):

        self.service_url = service_url

        self.local_model_name = local_model_name

        self._local_model = None

        self._dim = DEFAULT_DIM



    def _ensure_local(self):

        if self._local_model is None and ST_AVAILABLE:

            try:

                self._local_model = SentenceTransformer(self.local_model_name)

            except Exception:

                self._local_model = None



    @property

    def model_used(self) -> str:

        if self._local_model:

            return self.local_model_name

        if self.service_url:

            return "embed_service"

        return "char_fallback"



    def embed_texts(self, texts: List[str], timeout: int = 60) -> np.ndarray:

        if self.service_url:

            try:

                r = requests.post(self.service_url, json={"texts": texts}, timeout=timeout)

                r.raise_for_status()

                j = r.json()

                arrs = j.get("embeddings") or j.get("embedding") or None

                if arrs is not None:

                    a = np.asarray(arrs, dtype=np.float32)

                    return _normalize(a)

            except Exception:

                pass

        self._ensure_local()

        if self._local_model is not None:

            a = self._local_model.encode(texts, convert_to_numpy=True)

            return _normalize(np.asarray(a, dtype=np.float32))

        vecs = []

        for t in texts:

            v = np.zeros(DEFAULT_DIM, dtype=np.float32)

            for i, ch in enumerate(t[:DEFAULT_DIM]):

                v[i] = (ord(ch) % 100) / 100.0

            vecs.append(v)

        return _normalize(np.vstack(vecs))



    @property

    def dim(self) -> int:

        return int(self._dim)



              

class MemoryRAG:

    def __init__(self, sqlite_path: Path = SQLITE_PATH, embedder: Optional[Embedder] = None, faiss_index_path: Optional[Path] = FAISS_INDEX_PATH):

        self.sqlite_path = sqlite_path

        self.embedder = embedder or Embedder()

        self.faiss_index_path = faiss_index_path

        self.lock = threading.RLock()

        self._init_db()

        self._meta: List[MemoryEntry] = []

        self._load_meta()

        self._index = None

        self._dim = self.embedder.dim or DEFAULT_DIM

        self._init_faiss()



    def _init_db(self):

        with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    tags TEXT,
                    created_at TEXT,
                    embedding_b64 TEXT,
                    embedding_model TEXT
                );
            """)

            conn.commit()



    def _load_meta(self):

        with self.lock:

            with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

                cur = conn.execute("SELECT id, text, tags, created_at, embedding_b64, embedding_model FROM memories ORDER BY created_at ASC")

                rows = cur.fetchall()

            self._meta = []

            for r in rows:

                tags = json.loads(r[2]) if r[2] else []

                self._meta.append(MemoryEntry(id=r[0], text=r[1], tags=tags, created_at=r[3], embedding_b64=r[4], embedding_model=r[5]))

            if self._meta and self._meta[0].embedding_b64:

                self._dim = int(_b64_to_float32(self._meta[0].embedding_b64).shape[0])



    def _init_faiss(self):

        with self.lock:

            self._index = None

            if not FAISS_AVAILABLE or not self._meta:

                return

            try:

                if self.faiss_index_path.exists():

                    self._index = faiss.read_index(str(self.faiss_index_path))

                else:

                    self._index = faiss.IndexFlatIP(self._dim)

                    arr = np.vstack([_b64_to_float32(m.embedding_b64) for m in self._meta]).astype("float32")

                    self._index.add(arr)

                    faiss.write_index(self._index, str(self.faiss_index_path))

            except Exception:

                self._index = None



    def _save_faiss(self):

        if FAISS_AVAILABLE and self._index and self.faiss_index_path:

            try:

                faiss.write_index(self._index, str(self.faiss_index_path))

            except Exception:

                pass



    def add_memory(self, text: str, tags: Optional[List[str]] = None, meta: Optional[Dict[str, Any]] = None) -> MemoryEntry:

        tags = tags or []

        meta = meta or {}

        mid = meta.get("id") or str(uuid.uuid4())

        created_at = meta.get("created_at") or datetime.now(timezone.utc).isoformat()

        vec = self.embedder.embed_texts([text])[0]

        b64 = _float32_to_b64(vec)

        entry = MemoryEntry(

            id=mid, text=text, tags=tags, created_at=created_at,

            embedding_b64=b64, embedding_model=self.embedder.model_used                      

        )

        with self.lock:

            with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

                conn.execute(

                    "INSERT OR REPLACE INTO memories (id, text, tags, created_at, embedding_b64, embedding_model) VALUES (?, ?, ?, ?, ?, ?)",

                    (entry.id, entry.text, json.dumps(entry.tags), entry.created_at, entry.embedding_b64, entry.embedding_model)

                )

                conn.commit()

            self._meta.append(entry)

            if FAISS_AVAILABLE:

                try:

                    if self._index is None:

                        self._dim = int(vec.shape[0])

                        self._index = faiss.IndexFlatIP(self._dim)

                    self._index.add(np.expand_dims(vec, 0))

                    self._save_faiss()

                except Exception:

                    pass

        log_action("memory_add", {"id": mid, "len": len(text)})

        return entry



    def list_memories(self, limit: int = 200) -> List[Dict[str, Any]]:

        with self.lock:

            return [m.to_dict() for m in self._meta[-limit:][::-1]]                           



    def search(self, query: str, k: int = 6) -> List[Dict[str, Any]]:

        qvec = self.embedder.embed_texts([query])[0]

        with self.lock:

            if FAISS_AVAILABLE and self._index:

                try:

                    D, I = self._index.search(np.expand_dims(qvec, 0), k)

                    return [

                        {"id": self._meta[idx].id, "text": self._meta[idx].text, "tags": self._meta[idx].tags,

                         "created_at": self._meta[idx].created_at, "score": float(score)}

                        for score, idx in zip(D[0], I[0]) if 0 <= idx < len(self._meta)

                    ]

                except Exception:

                    pass

            scored = [(float(np.dot(_b64_to_float32(m.embedding_b64), qvec)), m) for m in self._meta if m.embedding_b64]

            scored.sort(key=lambda x: x[0], reverse=True)

            return [{"id": m.id, "text": m.text, "tags": m.tags, "created_at": m.created_at, "score": score}

                    for score, m in scored[:k]]



    def delete_memory(self, memory_id: str) -> bool:

        from sqlite3 import OperationalError

        with self.lock:

            try:

                with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

                    cur = conn.cursor()

                    cur.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

                    conn.commit()

                    deleted = cur.rowcount > 0

                if deleted:

                    self._load_meta()

                    if FAISS_AVAILABLE:

                        self._init_faiss()

                    log_action("memory_delete", {"id": memory_id})

                    return True

                else:

                    log_action("memory_delete_fail", {"id": memory_id, "reason": "not_found"}, "warn")

                    return False

            except OperationalError as e:

                log_action("memory_delete_error", {"err": str(e)}, "error")

                return False



    def delete_by_text(self, substring: str, limit: Optional[int] = None) -> int:

        substring = substring.lower()

        with self.lock:

            ids_to_delete = [m.id for m in self._meta if substring in m.text.lower()]

            if limit:

                ids_to_delete = ids_to_delete[:limit]

            if not ids_to_delete:

                return 0

            deleted_count = 0

            try:

                with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

                    cur = conn.cursor()

                    for _id in ids_to_delete:

                        cur.execute("DELETE FROM memories WHERE id = ?", (_id,))

                        deleted_count += cur.rowcount

                    conn.commit()

                self._load_meta()

                if FAISS_AVAILABLE:

                    self._init_faiss()

                log_action("memory_delete_batch", {"count": deleted_count, "substring": substring[:20]})

                return deleted_count

            except Exception as e:

                log_action("memory_delete_batch_error", {"err": str(e)}, "error")

                return 0



    def delete_all(self) -> int:

        with self.lock:

            n = len(self._meta)

            try:

                with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

                    cur = conn.cursor()

                    cur.execute("DELETE FROM memories")

                    conn.commit()

                self._load_meta()

                if FAISS_AVAILABLE:

                    self._init_faiss()

                log_action("memory_delete_all", {"count": n})

                return n

            except Exception as e:

                log_action("memory_delete_all_error", {"err": str(e)}, "error")

                return 0



    def reembed_all(self, batch_size: int = 128, updater: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:

        with self.lock:

            total = len(self._meta)

            if total == 0:

                return {"ok": True, "reembedded": 0, "backup": None}

            backup_path = str(self.sqlite_path) + f".bak_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

            try:

                shutil.copy2(self.sqlite_path, backup_path)

            except Exception:

                backup_path = None

            ids, texts = [m.id for m in self._meta], [m.text for m in self._meta]

            processed = 0

            for i in range(0, total, batch_size):

                batch_texts = texts[i:i + batch_size]

                emb_batch = self.embedder.embed_texts(batch_texts)

                with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

                    cur = conn.cursor()

                    for j, emb in enumerate(emb_batch):

                        b64 = _float32_to_b64(emb)

                        cur.execute("UPDATE memories SET embedding_b64 = ?, embedding_model = ? WHERE id = ?",

                                    (b64, self.embedder.model_used, ids[i + j]))

                        processed += 1

                if updater:

                    updater(processed, total)

            self._load_meta()

            if FAISS_AVAILABLE:

                self._init_faiss()

            log_action("memory_reembed", {"count": processed})

            return {"ok": True, "reembedded": processed, "backup": backup_path}



    def summarize_and_compact(self, max_entries: int = 1000, summarizer: Optional[Callable[[List[str]], str]] = None) -> Dict[str, Any]:

        with self.lock:

            n = len(self._meta)

            if n <= max_entries:

                return {"ok": True, "reason": "no_action", "count": n}

            remove_count = max(1, n - (max_entries // 2))

            to_summarize = [m.text for m in self._meta[:remove_count]]

            if summarizer:

                try:

                    summary_text = summarizer(to_summarize)

                except Exception:

                    summary_text = " ".join([t[:100] for t in to_summarize[:50]])[:2000]            

            else:

                pieces = [t.strip().split(".")[0] for t in to_summarize[:200] if t.strip()]

                summary_text = " / ".join(pieces[:100])[:2000]

            summary_id = str(uuid.uuid4())

            created_at = datetime.now(timezone.utc).isoformat()

            vec = self.embedder.embed_texts([summary_text])[0]

            b64 = _float32_to_b64(vec)

            tags = ["summary", f"compacted_from_{remove_count}"]

            with sqlite3.connect(self.sqlite_path, timeout=SQLITE_TIMEOUT) as conn:

                cur = conn.cursor()

                cur.execute("BEGIN")

                for _id in [m.id for m in self._meta[:remove_count]]:

                    cur.execute("DELETE FROM memories WHERE id = ?", (_id,))

                cur.execute("INSERT INTO memories (id, text, tags, created_at, embedding_b64, embedding_model) VALUES (?, ?, ?, ?, ?, ?)",

                            (summary_id, summary_text, json.dumps(tags), created_at, b64, self.embedder.model_used))

                conn.commit()

            self._load_meta()

            if FAISS_AVAILABLE:

                self._init_faiss()

            log_action("memory_compact", {"removed": remove_count, "new_count": len(self._meta)})

            return {"ok": True, "compacted": remove_count, "new_count": len(self._meta)}



MR = MemoryRAG()



                  

if __name__ == "__main__":

    import argparse, pprint

    p = argparse.ArgumentParser(prog="memory_rag")

    sub = p.add_subparsers(dest="cmd")

                                           

    args = p.parse_args()

                                     
