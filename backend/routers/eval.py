from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from services.evaluator import get_harness, DEFAULT_QUESTIONS, EvalQuestion
from services.indexer import get_indexer

router = APIRouter()


class EvalRequest(BaseModel):
    repo_id: str
    modes: Optional[List[str]] = ["tree", "graph", "vector"]
    use_default_questions: bool = True
    custom_questions: Optional[List[dict]] = None


class ReIndexRequest(BaseModel):
    repo_id: str


@router.post("/run")
async def run_eval(body: EvalRequest, background_tasks: BackgroundTasks):
    indexer = get_indexer()
    repo = indexer.get_repo(body.repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    if repo["status"] != "ready":
        raise HTTPException(400, "Repository not ready")

    questions = DEFAULT_QUESTIONS
    if not body.use_default_questions and body.custom_questions:
        questions = [EvalQuestion(**q) for q in body.custom_questions]

    async def run():
        harness = get_harness()
        report  = await harness.run(body.repo_id, repo["name"], questions, body.modes)
        print(report.summary_table())

    background_tasks.add_task(run)
    return {
        "message": "Benchmark started in background",
        "questions": len(questions),
        "modes": body.modes,
        "estimated_minutes": round(len(questions) * len(body.modes) * 5 / 60, 1),
    }


@router.get("/results/{repo_id}")
async def get_results(repo_id: str):
    from pathlib import Path
    import json
    results_dir = Path("./data/eval_results")
    files = sorted(results_dir.glob(f"{repo_id}_*.json"), reverse=True)
    if not files:
        raise HTTPException(404, "No evaluation results found for this repo")
    with open(files[0]) as f:
        return json.load(f)


@router.get("/questions")
async def get_default_questions():
    return [{"id": q.id, "question": q.question, "type": q.question_type,
             "ideal_mode": q.ideal_mode, "difficulty": q.difficulty}
            for q in DEFAULT_QUESTIONS]
