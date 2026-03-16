"""
LLM Query Router — the core novel contribution of CodeRAG-R.

Instead of blindly firing vector search, the router:
1. Reads the AST structure summary of the repo
2. Uses Groq LLM to classify the query intent
3. Returns which retrieval mode to use + a focused sub-query

This is what separates CodeRAG-R from standard RAG.
Inspired by PageIndex's reasoning-first approach, applied to code.
"""
from groq import Groq
from config import settings
from typing import Tuple

ROUTER_SYSTEM = """You are a code retrieval router for a codebase Q&A system.

Given:
1. A codebase structure summary (files, classes, functions)
2. A developer's question

Your job: decide the best retrieval strategy and return a JSON response.

Retrieval modes:
- "tree": Use when the question is about code structure, architecture, how things are organized,
  what a file/class contains, or where something lives. The LLM will navigate the AST tree.
- "graph": Use when the question involves call relationships, dependencies, what calls what,
  what breaks if X changes, or tracing execution flow. Graph traversal will follow call chains.
- "vector": Use for broad/fuzzy questions, finding code by description, similarity search,
  or when you're unsure. Falls back to semantic embedding search.

Also extract a focused sub-query that will be used for retrieval.

Return ONLY valid JSON in this exact format:
{
  "mode": "tree" | "graph" | "vector",
  "reason": "one sentence why",
  "sub_query": "focused retrieval query",
  "target_files": ["file1.py", "file2.py"]  // best guesses from the summary, can be empty
}"""


class QueryRouter:
    def __init__(self):
        self._client = None

    def _groq(self) -> Groq:
        if self._client is None:
            self._client = Groq(api_key=settings.groq_api_key)
        return self._client

    def route(self, question: str, ast_summary: str) -> dict:
        """
        Route a query to the appropriate retrieval mode.
        Returns dict with: mode, reason, sub_query, target_files
        Falls back to vector mode if routing fails.
        """
        if not settings.groq_api_key or not ast_summary:
            return {"mode": "vector", "reason": "No API key or summary", "sub_query": question, "target_files": []}

        prompt = f"""Codebase structure:
{ast_summary[:4000]}

Developer question: {question}

Route this query to the best retrieval mode."""

        try:
            resp = self._groq().chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=256,
                temperature=0.0,
            )
            import json
            raw = resp.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            return {
                "mode": result.get("mode", "vector"),
                "reason": result.get("reason", ""),
                "sub_query": result.get("sub_query", question),
                "target_files": result.get("target_files", []),
            }
        except Exception as e:
            print(f"[Router] Routing failed, using vector: {e}")
            return {"mode": "vector", "reason": f"Router error: {e}", "sub_query": question, "target_files": []}


_router_instance = None

def get_router() -> QueryRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = QueryRouter()
    return _router_instance
