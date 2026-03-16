from fastapi import APIRouter, HTTPException
from services.indexer import get_indexer

router = APIRouter()


@router.get("/{repo_id}")
async def get_graph(repo_id: str, max_nodes: int = 150):
    indexer = get_indexer()
    if not indexer.get_repo(repo_id):
        raise HTTPException(404, "Repository not found")
    graph = indexer.get_graph(repo_id)
    if not graph:
        raise HTTPException(404, "Graph not built yet")
    return graph.to_vis_data(max_nodes=max_nodes)
