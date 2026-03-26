"""
ChromaDB vector store with HuggingFace sentence-transformers.
Used as the semantic fallback retrieval mode.
"""
import hashlib
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from services.ast_parser import CodeChunk
from config import settings


class VectorStore:
    def __init__(self):
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._model: SentenceTransformer = None
        self._collections: Dict[str, chromadb.Collection] = {}

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            print(f"[VectorStore] Loading {settings.hf_model}...")
            self._model = SentenceTransformer(settings.hf_model)
        return self._model

    def _collection(self, repo_id: str) -> chromadb.Collection:
        if repo_id not in self._collections:
            safe = hashlib.md5(repo_id.encode()).hexdigest()[:16]
            self._collections[repo_id] = self._client.get_or_create_collection(
                name=f"coderag_{safe}",
                metadata={"repo_id": repo_id, "hnsw:space": "cosine"},
            )
        return self._collections[repo_id]

    def index_chunks(self, chunks: List[CodeChunk], repo_id: str):
        if not chunks:
            return
        col = self._collection(repo_id)
        model = self._get_model()
        texts = [c.to_embedding_text() for c in chunks]
        print(f"[VectorStore] Embedding {len(texts)} chunks...")
        embeddings = model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
        for i in range(0, len(chunks), 100):
            batch = chunks[i:i + 100]
            col.upsert(
                ids=[c.id for c in batch],
                embeddings=embeddings[i:i + 100],
                metadatas=[{
                    "file": c.relative_path,
                    "name": c.name,
                    "type": c.chunk_type,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "language": c.language,
                    "parent_class": c.parent_class or "",
                    "calls": ",".join(c.calls[:10]),
                } for c in batch],
                documents=[c.code[:500] for c in batch],
            )
        print(f"[VectorStore] Indexed {len(chunks)} chunks.")

    def search(self, query: str, repo_id: str, top_k: int = 8) -> List[Dict]:
        col = self._collection(repo_id)
        count = col.count()
        if count == 0:
            return []
        model = self._get_model()
        emb = model.encode([query]).tolist()
        res = col.query(
            query_embeddings=emb,
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        out = []
        for i, cid in enumerate(res["ids"][0]):
            meta = res["metadatas"][0][i]
            out.append({
                "id": cid,
                "code": res["documents"][0][i],
                "file": meta.get("file", ""),
                "name": meta.get("name", ""),
                "type": meta.get("type", ""),
                "start_line": meta.get("start_line", 0),
                "end_line": meta.get("end_line", 0),
                "language": meta.get("language", ""),
                "parent_class": meta.get("parent_class", ""),
                "relevance_score": round(1 - res["distances"][0][i], 4),
                "retrieval_method": "vector",
            })
        return out

    def get_by_ids(self, ids: List[str], repo_id: str) -> List[Dict]:
        if not ids:
            return []
        col = self._collection(repo_id)
        try:
            res = col.get(ids=ids, include=["documents", "metadatas"])
            return [{
                "id": cid,
                "code": res["documents"][i],
                "file": res["metadatas"][i].get("file", ""),
                "name": res["metadatas"][i].get("name", ""),
                "type": res["metadatas"][i].get("type", ""),
                "start_line": res["metadatas"][i].get("start_line", 0),
                "end_line": res["metadatas"][i].get("end_line", 0),
                "language": res["metadatas"][i].get("language", ""),
                "parent_class": res["metadatas"][i].get("parent_class", ""),
                "relevance_score": 0.5,
                "retrieval_method": "graph",
            } for i, cid in enumerate(res["ids"])]
        except Exception:
            return []

    def delete_repo(self, repo_id: str):
        try:
            col = self._collection(repo_id)
            self._client.delete_collection(col.name)
            self._collections.pop(repo_id, None)
        except Exception:
            pass

    def count(self, repo_id: str) -> int:
        try:
            return self._collection(repo_id).count()
        except Exception:
            return 0
