from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import QueryRequest
from services.indexer import get_indexer
from services.query_engine import get_engine
from services.query_router import get_router

router = APIRouter()


@router.post("/stream")
async def stream_query(body: QueryRequest):
    indexer = get_indexer()
    repo = indexer.get_repo(body.repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    if repo["status"] != "ready":
        raise HTTPException(400, f"Repository is not ready (status: {repo['status']})")

    graph = indexer.get_graph(body.repo_id)
    summary = indexer.get_summary(body.repo_id)
    engine = get_engine()
    query_router = get_router()

    async def event_stream():
        async for chunk in engine.stream_query(
            question=body.question,
            repo_id=body.repo_id,
            graph=graph,
            ast_summary=summary,
            router=query_router,
            top_k=body.top_k,
            forced_mode=body.mode or "auto",
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
