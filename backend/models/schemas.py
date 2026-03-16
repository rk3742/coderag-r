from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class IndexingStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class RepoCreate(BaseModel):
    github_url: str
    name: Optional[str] = None


class RepoResponse(BaseModel):
    id: str
    name: str
    github_url: Optional[str] = None
    status: IndexingStatus
    file_count: int = 0
    function_count: int = 0
    chunk_count: int = 0
    languages: List[str] = []
    created_at: str
    error: Optional[str] = None


class QueryRequest(BaseModel):
    repo_id: str
    question: str
    top_k: int = 8
    mode: Optional[str] = "auto"  # auto | tree | graph | vector


class Citation(BaseModel):
    file: str
    function_name: str
    start_line: int
    end_line: int
    snippet: str
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    retrieval_method: str
    mode_used: str
    chunks_retrieved: int


class GraphNode(BaseModel):
    id: str
    label: str
    file: str
    line: int
    type: str


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = "calls"


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int


class FileNode(BaseModel):
    name: str
    path: str
    type: str
    language: Optional[str] = None
    children: Optional[List["FileNode"]] = None


FileNode.model_rebuild()
