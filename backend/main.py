from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers import repos, query, graph, eval, reindex

app = FastAPI(title="CodeRAG-R API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router,   prefix="/api/repos",   tags=["Repos"])
app.include_router(query.router,   prefix="/api/query",   tags=["Query"])
app.include_router(graph.router,   prefix="/api/graph",   tags=["Graph"])
app.include_router(eval.router,    prefix="/api/eval",    tags=["Evaluation"])
app.include_router(reindex.router, prefix="/api/reindex", tags=["ReIndex"])


@app.get("/")
async def root():
    return {"message": "CodeRAG-R API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
