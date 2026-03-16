"""
Evaluation harness for CodeRAG-R.
Benchmarks all 3 retrieval modes across a question set.
Generates a results table proving which mode wins for which question type.
This is the research contribution that makes the project publishable.
"""
import json
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class EvalQuestion:
    id: str
    question: str
    question_type: str          # architecture | dependency | search | general
    expected_files: List[str]   # files that should appear in citations
    expected_keywords: List[str] # keywords that should appear in answer
    ideal_mode: str             # tree | graph | vector
    difficulty: str             # easy | medium | hard


@dataclass
class EvalResult:
    question_id: str
    question: str
    question_type: str
    mode_used: str
    forced_mode: str
    answer: str
    citations: List[Dict]
    chunks_retrieved: int
    response_time_ms: float
    # Scoring
    file_hit_score: float       # 0-1: did expected files appear in citations?
    keyword_hit_score: float    # 0-1: did expected keywords appear in answer?
    overall_score: float        # weighted average
    passed: bool


@dataclass
class BenchmarkReport:
    repo_id: str
    repo_name: str
    timestamp: str
    questions_total: int
    results: List[EvalResult] = field(default_factory=list)

    def by_mode(self) -> Dict[str, List[EvalResult]]:
        modes = {}
        for r in self.results:
            modes.setdefault(r.forced_mode, []).append(r)
        return modes

    def by_type(self) -> Dict[str, List[EvalResult]]:
        types = {}
        for r in self.results:
            types.setdefault(r.question_type, []).append(r)
        return types

    def summary_table(self) -> str:
        lines = [
            "=" * 60,
            "CODERAG-R BENCHMARK RESULTS",
            f"Repo: {self.repo_name}  |  {self.timestamp}",
            "=" * 60,
            "",
            "── BY RETRIEVAL MODE ──",
            f"{'Mode':<12} {'Questions':<12} {'Avg Score':<12} {'Pass Rate':<12} {'Avg Time(ms)'}",
            "-" * 60,
        ]
        for mode, results in self.by_mode().items():
            avg_score  = sum(r.overall_score for r in results) / len(results)
            pass_rate  = sum(1 for r in results if r.passed) / len(results)
            avg_time   = sum(r.response_time_ms for r in results) / len(results)
            lines.append(f"{mode:<12} {len(results):<12} {avg_score:.2f}{'':8} {pass_rate:.0%}{'':8} {avg_time:.0f}ms")

        lines += ["", "── BY QUESTION TYPE ──",
                  f"{'Type':<16} {'Tree':<10} {'Graph':<10} {'Vector':<10} {'Best Mode'}",
                  "-" * 60]

        type_mode_scores: Dict[str, Dict[str, List[float]]] = {}
        for r in self.results:
            type_mode_scores.setdefault(r.question_type, {}).setdefault(r.forced_mode, []).append(r.overall_score)

        for qtype, mode_scores in type_mode_scores.items():
            tree_s   = sum(mode_scores.get("tree",   [0])) / max(len(mode_scores.get("tree",   [1])), 1)
            graph_s  = sum(mode_scores.get("graph",  [0])) / max(len(mode_scores.get("graph",  [1])), 1)
            vector_s = sum(mode_scores.get("vector", [0])) / max(len(mode_scores.get("vector", [1])), 1)
            best = max([("tree", tree_s), ("graph", graph_s), ("vector", vector_s)], key=lambda x: x[1])
            lines.append(f"{qtype:<16} {tree_s:.2f}{'':6} {graph_s:.2f}{'':6} {vector_s:.2f}{'':6} {best[0].upper()}")

        overall_pass = sum(1 for r in self.results if r.passed) / max(len(self.results), 1)
        overall_score = sum(r.overall_score for r in self.results) / max(len(self.results), 1)
        lines += ["", "=" * 60,
                  f"OVERALL  Score: {overall_score:.2f}  Pass rate: {overall_pass:.0%}  Questions: {len(self.results)}",
                  "=" * 60]
        return "\n".join(lines)


# ── Default question set ──────────────────────────────────────────────────────
DEFAULT_QUESTIONS: List[EvalQuestion] = [
    # Architecture questions — Tree should win
    EvalQuestion("arch_1", "What is the overall architecture of this codebase?",
                 "architecture", [], ["controller", "route", "model", "middleware"], "tree", "easy"),
    EvalQuestion("arch_2", "What does the main entry point file do?",
                 "architecture", [], ["server", "app", "main", "entry"], "tree", "easy"),
    EvalQuestion("arch_3", "How is the project structured and what are the main components?",
                 "architecture", [], ["model", "controller", "route", "service"], "tree", "medium"),
    EvalQuestion("arch_4", "What middleware is used in this application?",
                 "architecture", [], ["middleware", "protect", "auth", "cors"], "tree", "medium"),
    EvalQuestion("arch_5", "Explain the authentication flow from registration to login.",
                 "architecture", [], ["register", "login", "token", "jwt"], "tree", "hard"),

    # Dependency questions — Graph should win
    EvalQuestion("dep_1", "What functions does the database connection module export?",
                 "dependency", [], ["connect", "export", "module", "db"], "graph", "easy"),
    EvalQuestion("dep_2", "What would break if I changed the authentication middleware?",
                 "dependency", [], ["protect", "route", "auth", "middleware"], "graph", "hard"),
    EvalQuestion("dep_3", "What calls the main controller functions?",
                 "dependency", [], ["router", "route", "controller", "call"], "graph", "medium"),
    EvalQuestion("dep_4", "Trace the call chain from the API endpoint to the database.",
                 "dependency", [], ["route", "controller", "model", "db", "mongoose"], "graph", "hard"),
    EvalQuestion("dep_5", "What imports and uses the User model?",
                 "dependency", [], ["user", "model", "require", "import"], "graph", "medium"),

    # Search questions — Vector should win
    EvalQuestion("search_1", "Find all error handling code.",
                 "search", [], ["error", "catch", "try", "throw"], "vector", "easy"),
    EvalQuestion("search_2", "Where is JWT token verification implemented?",
                 "search", [], ["jwt", "verify", "token", "secret"], "vector", "easy"),
    EvalQuestion("search_3", "Find all async functions that handle HTTP requests.",
                 "search", [], ["async", "req", "res", "await"], "vector", "medium"),
    EvalQuestion("search_4", "Where is password hashing or encryption done?",
                 "search", [], ["password", "hash", "bcrypt", "encrypt", "salt"], "vector", "medium"),
    EvalQuestion("search_5", "Find all database query operations.",
                 "search", [], ["find", "findOne", "save", "create", "update"], "vector", "hard"),
]


def score_result(
    answer: str,
    citations: List[Dict],
    question: EvalQuestion,
) -> tuple:
    """Score an answer against expected files and keywords."""
    # File hit score
    if question.expected_files:
        cited_files = {c.get("file", "").lower() for c in citations}
        hits = sum(1 for ef in question.expected_files
                   if any(ef.lower() in cf for cf in cited_files))
        file_score = hits / len(question.expected_files)
    else:
        file_score = 1.0  # no expected files — skip this metric

    # Keyword hit score
    answer_lower = answer.lower()
    if question.expected_keywords:
        hits = sum(1 for kw in question.expected_keywords if kw.lower() in answer_lower)
        kw_score = hits / len(question.expected_keywords)
    else:
        kw_score = 1.0

    overall = (file_score * 0.4) + (kw_score * 0.6)
    passed  = overall >= 0.5
    return file_score, kw_score, overall, passed


class EvalHarness:
    """
    Runs benchmark evaluation across all three retrieval modes.
    For each question it runs Tree, Graph, and Vector separately
    then compares scores to find which mode wins.
    """

    def __init__(self):
        self.results_dir = Path("./data/eval_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def run(
        self,
        repo_id: str,
        repo_name: str,
        questions: Optional[List[EvalQuestion]] = None,
        modes: List[str] = None,
    ) -> BenchmarkReport:
        from services.indexer import get_indexer
        from services.query_engine import get_engine
        from services.query_router import get_router

        if questions is None:
            questions = DEFAULT_QUESTIONS
        if modes is None:
            modes = ["tree", "graph", "vector"]

        indexer     = get_indexer()
        engine      = get_engine()
        query_router = get_router()
        graph       = indexer.get_graph(repo_id)
        summary     = indexer.get_summary(repo_id)

        report = BenchmarkReport(
            repo_id=repo_id,
            repo_name=repo_name,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            questions_total=len(questions) * len(modes),
        )

        total = len(questions) * len(modes)
        done  = 0

        for q in questions:
            for mode in modes:
                print(f"[Eval] ({done+1}/{total}) Q={q.id} mode={mode}")
                start = time.time()

                answer_parts = []
                citations    = []
                chunks_count = 0
                mode_used    = mode

                try:
                    async for event_str in engine.stream_query(
                        question=q.question,
                        repo_id=repo_id,
                        graph=graph,
                        ast_summary=summary,
                        router=query_router,
                        top_k=8,
                        forced_mode=mode,
                    ):
                        if event_str.startswith("data: "):
                            try:
                                ev = json.loads(event_str[6:])
                                if ev["type"] == "token":
                                    answer_parts.append(ev["content"])
                                elif ev["type"] == "citations":
                                    citations    = ev.get("citations", [])
                                    chunks_count = ev.get("chunks_retrieved", 0)
                                elif ev["type"] == "route":
                                    mode_used = ev.get("mode", mode)
                            except Exception:
                                pass
                except Exception as e:
                    print(f"[Eval] Error: {e}")

                elapsed_ms = (time.time() - start) * 1000
                answer     = "".join(answer_parts)

                file_s, kw_s, overall_s, passed = score_result(answer, citations, q)

                report.results.append(EvalResult(
                    question_id=q.id,
                    question=q.question,
                    question_type=q.question_type,
                    mode_used=mode_used,
                    forced_mode=mode,
                    answer=answer[:500],
                    citations=citations[:3],
                    chunks_retrieved=chunks_count,
                    response_time_ms=elapsed_ms,
                    file_hit_score=file_s,
                    keyword_hit_score=kw_s,
                    overall_score=overall_s,
                    passed=passed,
                ))
                done += 1
                await asyncio.sleep(2)  # respect Groq rate limits

        # Save results
        out_path = self.results_dir / f"{repo_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(out_path, "w") as f:
            json.dump({
                "repo_id": report.repo_id,
                "repo_name": report.repo_name,
                "timestamp": report.timestamp,
                "results": [asdict(r) for r in report.results],
            }, f, indent=2)

        print("\n" + report.summary_table())
        print(f"\n[Eval] Results saved to {out_path}")
        return report


_harness_instance = None

def get_harness() -> EvalHarness:
    global _harness_instance
    if _harness_instance is None:
        _harness_instance = EvalHarness()
    return _harness_instance
