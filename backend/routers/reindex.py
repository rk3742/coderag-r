from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from services.incremental_indexer import get_incremental_indexer
from services.indexer import get_indexer
from pathlib import Path
from config import settings

router = APIRouter()


class ReIndexRequest(BaseModel):
    repo_id: str


@router.post("/")
async def re_index(body: ReIndexRequest, background_tasks: BackgroundTasks):
    indexer = get_indexer()
    repo = indexer.get_repo(body.repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")

    repo_path    = str(Path(settings.repos_dir) / body.repo_id)
    summary_path = str(Path(settings.repos_dir) / f"{body.repo_id}_summary.txt")
    cache_path   = str(Path(settings.repos_dir) / f"{body.repo_id}_hashes.json")

    if not Path(repo_path).exists():
        raise HTTPException(400, "Repository files not found on disk")

    async def run():
        inc     = get_incremental_indexer()
        graph   = indexer.get_graph(body.repo_id)
        result  = await inc.re_index(
            repo_id=body.repo_id,
            repo_path=repo_path,
            vector_store=inc.parser and __import__('services.vector_store', fromlist=['VectorStore']).VectorStore(),
            graph_store=graph,
            summary_path=summary_path,
            cache_path=cache_path,
        )
        print(f"[ReIndex] {result}")

    background_tasks.add_task(run)
    return {"message": "Re-indexing started", "repo_id": body.repo_id}
