"""
Query Engine — orchestrates retrieval + generation.
Supports 3 modes: tree reasoning, graph traversal, vector search.
The router picks the mode; this engine executes it.
"""
import json
from groq import Groq
from typing import List, Dict, AsyncGenerator
from services.vector_store import VectorStore
from services.graph_builder import DependencyGraph
from services.query_router import QueryRouter
from config import settings

GENERATION_SYSTEM = """You are CodeRAG-R, an expert developer assistant.

You answer questions about codebases using retrieved code context.

Rules:
1. Answer ONLY from the provided context. Never hallucinate code.
2. Always cite sources using this format: [file.py :: function_name :: L{start}-{end}]
3. When tracing call chains or dependencies, list them step by step.
4. If the answer isn't in the context, say so clearly and suggest what to search for.
5. Keep answers focused and practical. Use code blocks for snippets.
6. State which retrieval mode was used (tree/graph/vector) at the end in one line."""


class QueryEngine:
    def __init__(self, vector_store: VectorStore):
        self.vs = vector_store
        self._client: Groq = None

    def _groq(self) -> Groq:
        if self._client is None:
            self._client = Groq(api_key=settings.groq_api_key)
        return self._client

    # ── TREE REASONING MODE ──────────────────────────────────────────────
    def _retrieve_tree(self, sub_query: str, repo_id: str,
                       ast_summary: str, target_files: List[str], top_k: int) -> List[Dict]:
        """
        Tree reasoning: LLM navigates the AST summary to identify
        exactly which files/functions to fetch, then retrieves them by
        targeted vector search scoped to those files.
        """
        if not ast_summary:
            return self.vs.search(sub_query, repo_id, top_k)

        # First do broad vector search
        candidates = self.vs.search(sub_query, repo_id, top_k * 2)

        # If router identified target files, boost those chunks
        if target_files:
            boosted, rest = [], []
            for c in candidates:
                matched = any(tf.lower() in c["file"].lower() for tf in target_files)
                if matched:
                    c["relevance_score"] = min(1.0, c["relevance_score"] + 0.25)
                    c["retrieval_method"] = "tree"
                    boosted.append(c)
                else:
                    rest.append(c)
            candidates = boosted + rest

        for c in candidates:
            c["retrieval_method"] = "tree"

        return candidates[:top_k]

    # ── GRAPH TRAVERSAL MODE ─────────────────────────────────────────────
    def _retrieve_graph(self, sub_query: str, repo_id: str,
                        graph: DependencyGraph, top_k: int) -> List[Dict]:
        """
        Graph traversal: start from vector search seeds,
        then expand via call-graph neighbors.
        """
        seeds = self.vs.search(sub_query, repo_id, top_k // 2 + 2)
        if not seeds:
            return []

        neighbor_ids = set()
        for seed in seeds:
            if graph:
                neighbor_ids.update(graph.get_neighbors(seed["id"], depth=settings.graph_neighbor_depth))

        existing = {c["id"] for c in seeds}
        new_ids = list(neighbor_ids - existing)
        expanded = self.vs.get_by_ids(new_ids[:top_k], repo_id)

        for c in seeds:
            c["retrieval_method"] = "graph-seed"
        for c in expanded:
            c["relevance_score"] = c.get("relevance_score", 0.5) * 0.75
            c["retrieval_method"] = "graph-expanded"

        all_chunks = seeds + expanded
        all_chunks.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return self._dedup(all_chunks)[:top_k]

    # ── VECTOR SEARCH MODE ───────────────────────────────────────────────
    def _retrieve_vector(self, sub_query: str, repo_id: str, top_k: int) -> List[Dict]:
        chunks = self.vs.search(sub_query, repo_id, top_k)
        for c in chunks:
            c["retrieval_method"] = "vector"
        return chunks

    # ── HELPERS ──────────────────────────────────────────────────────────
    def _dedup(self, chunks: List[Dict]) -> List[Dict]:
        seen, out = set(), []
        for c in chunks:
            if c["id"] not in seen:
                seen.add(c["id"])
                out.append(c)
        return out

    def _build_context(self, chunks: List[Dict]) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"--- [{i}] {c['retrieval_method'].upper()} ---\n"
                f"File: {c['file']}  |  {c['type']}: {c['name']}  |  "
                f"Lines {c['start_line']}-{c['end_line']}  |  "
                f"Score: {c.get('relevance_score', 0):.2f}\n\n"
                f"{c['code']}\n"
            )
        return "\n".join(parts)

    def _make_citations(self, chunks: List[Dict]) -> List[Dict]:
        return [{
            "file": c["file"],
            "function_name": c["name"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "snippet": c["code"][:200] + "..." if len(c["code"]) > 200 else c["code"],
            "relevance_score": round(c.get("relevance_score", 0), 3),
        } for c in chunks[:6]]

    # ── PUBLIC API ───────────────────────────────────────────────────────
    def retrieve(self, question: str, repo_id: str, graph: DependencyGraph,
                 ast_summary: str, router: QueryRouter,
                 top_k: int = 8, forced_mode: str = "auto") -> tuple:
        """Returns (chunks, route_info)"""
        if forced_mode != "auto":
            route = {"mode": forced_mode, "reason": "Manually selected", "sub_query": question, "target_files": []}
        else:
            route = router.route(question, ast_summary)

        mode = route["mode"]
        sub_query = route.get("sub_query", question)

        if mode == "tree":
            chunks = self._retrieve_tree(sub_query, repo_id, ast_summary, route.get("target_files", []), top_k)
        elif mode == "graph":
            chunks = self._retrieve_graph(sub_query, repo_id, graph, top_k)
        else:
            chunks = self._retrieve_vector(sub_query, repo_id, top_k)

        return chunks, route

    async def stream_query(
        self, question: str, repo_id: str, graph: DependencyGraph,
        ast_summary: str, router: QueryRouter,
        top_k: int = 8, forced_mode: str = "auto"
    ) -> AsyncGenerator[str, None]:
        """Streaming SSE response with confidence scoring."""
        from services.confidence import compute_confidence, build_confidence_prefix

        chunks, route = self.retrieve(question, repo_id, graph, ast_summary, router, top_k, forced_mode)

        # Confidence scoring — the anti-hallucination layer
        confidence_score, confidence_level, confidence_message = compute_confidence(chunks, question)

        # Send route info
        yield f"data: {json.dumps({'type': 'route', 'mode': route['mode'], 'reason': route.get('reason', ''), 'sub_query': route.get('sub_query', question)})}\n\n"

        # Send confidence
        yield f"data: {json.dumps({'type': 'confidence', 'score': confidence_score, 'level': confidence_level, 'message': confidence_message})}\n\n"

        # If no confidence at all — refuse to hallucinate
        if confidence_level == "none":
            yield f"data: {json.dumps({'type': 'citations', 'citations': [], 'chunks_retrieved': 0})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'content': confidence_message})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        if not chunks:
            yield f"data: {json.dumps({'type': 'error', 'content': 'No relevant code found. Try rephrasing or check the repo is indexed.'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'citations', 'citations': self._make_citations(chunks), 'chunks_retrieved': len(chunks)})}\n\n"

        context = self._build_context(chunks)
        confidence_instruction = build_confidence_prefix(confidence_level, confidence_message, chunks)
        mode_label = route["mode"].upper()

        system_with_confidence = GENERATION_SYSTEM + f"\n\nCONFIDENCE INSTRUCTION: {confidence_instruction}"

        user_msg = (
            f"Retrieval mode used: {mode_label}\n"
            f"Router reasoning: {route.get('reason', '')}\n"
            f"Confidence level: {confidence_level.upper()} (score: {confidence_score})\n\n"
            f"Code context:\n{context}\n\n"
            f"Question: {question}"
        )

        try:
            stream = self._groq().chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_with_confidence},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': delta.content})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


_engine_instance = None

def get_engine() -> QueryEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = QueryEngine(VectorStore())
    return _engine_instance
