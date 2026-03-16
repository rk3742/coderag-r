"""
Indexer — orchestrates the full indexing pipeline:
1. Clone GitHub repo or extract zip
2. AST parse with Tree-sitter
3. Build AST structure summary (for LLM router)
4. Build NetworkX dependency graph
5. Embed and store in ChromaDB
"""
import os
import json
import shutil
import asyncio
import zipfile
import uuid
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from services.ast_parser import ASTParser
from services.graph_builder import DependencyGraph
from services.vector_store import VectorStore
from models.schemas import IndexingStatus
from config import settings


class RepoStore:
    def __init__(self):
        self._path = Path(settings.repos_dir) / "repos.json"
        self._data: Dict = self._load()

    def _load(self) -> Dict:
        if self._path.exists():
            try:
                with open(self._path) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def create(self, name: str, github_url: Optional[str] = None) -> Dict:
        repo_id = str(uuid.uuid4())[:8]
        repo = {
            "id": repo_id, "name": name, "github_url": github_url,
            "status": IndexingStatus.PENDING, "file_count": 0,
            "function_count": 0, "chunk_count": 0, "languages": [],
            "created_at": datetime.utcnow().isoformat(), "error": None,
        }
        self._data[repo_id] = repo
        self._save()
        return repo

    def update(self, repo_id: str, **kwargs):
        if repo_id in self._data:
            self._data[repo_id].update(kwargs)
            self._save()

    def get(self, repo_id: str) -> Optional[Dict]:
        return self._data.get(repo_id)

    def list_all(self) -> list:
        return list(self._data.values())

    def delete(self, repo_id: str):
        self._data.pop(repo_id, None)
        self._save()


class IndexerService:
    def __init__(self):
        self.parser = ASTParser()
        self.vs = VectorStore()
        self.store = RepoStore()
        self._graphs: Dict[str, DependencyGraph] = {}
        self._summaries: Dict[str, str] = {}

    def get_all_repos(self): return self.store.list_all()
    def get_repo(self, repo_id): return self.store.get(repo_id)

    def get_graph(self, repo_id: str) -> Optional[DependencyGraph]:
        if repo_id not in self._graphs:
            gp = Path(settings.repos_dir) / f"{repo_id}_graph.json"
            if gp.exists():
                g = DependencyGraph()
                g.load(str(gp))
                self._graphs[repo_id] = g
        return self._graphs.get(repo_id)

    def get_summary(self, repo_id: str) -> str:
        if repo_id not in self._summaries:
            sp = Path(settings.repos_dir) / f"{repo_id}_summary.txt"
            if sp.exists():
                with open(sp) as f:
                    self._summaries[repo_id] = f.read()
        return self._summaries.get(repo_id, "")

    def get_file_tree(self, repo_id: str) -> Optional[Dict]:
        rp = Path(settings.repos_dir) / repo_id
        if not rp.exists():
            return None
        return self._build_tree(rp, rp)

    def _build_tree(self, path: Path, root: Path) -> Dict:
        IGNORE = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        LANG_MAP = {".py": "python", ".js": "javascript", ".ts": "typescript",
                    ".jsx": "react", ".tsx": "react-ts", ".json": "json",
                    ".md": "markdown", ".css": "css", ".html": "html"}
        if path.is_file():
            return {"name": path.name, "path": str(path.relative_to(root)),
                    "type": "file", "language": LANG_MAP.get(path.suffix.lower())}
        children = []
        try:
            for child in sorted(path.iterdir()):
                if child.name not in IGNORE and not child.name.startswith("."):
                    children.append(self._build_tree(child, root))
        except PermissionError:
            pass
        return {"name": path.name,
                "path": str(path.relative_to(root)) if path != root else ".",
                "type": "directory", "children": children}

    def get_file_content(self, repo_id: str, file_path: str) -> Optional[str]:
        base = Path(settings.repos_dir) / repo_id
        full = base / file_path
        try:
            full.resolve().relative_to(base.resolve())
        except ValueError:
            return None
        if full.is_file():
            try:
                with open(full, encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def delete_repo(self, repo_id: str):
        rp = Path(settings.repos_dir) / repo_id
        if rp.exists():
            shutil.rmtree(rp)
        for suffix in ["_graph.json", "_summary.txt"]:
            fp = Path(settings.repos_dir) / f"{repo_id}{suffix}"
            if fp.exists():
                fp.unlink()
        self.vs.delete_repo(repo_id)
        self.store.delete(repo_id)
        self._graphs.pop(repo_id, None)
        self._summaries.pop(repo_id, None)

    async def index_from_github(self, github_url: str, repo_name: Optional[str] = None) -> Dict:
        import git
        name = repo_name or github_url.rstrip("/").split("/")[-1].replace(".git", "")
        repo = self.store.create(name, github_url)
        asyncio.create_task(self._run_github(repo["id"], github_url))
        return repo

    async def _run_github(self, repo_id: str, url: str):
        import git
        try:
            self.store.update(repo_id, status=IndexingStatus.INDEXING)
            rp = Path(settings.repos_dir) / repo_id
            await asyncio.to_thread(git.Repo.clone_from, url, str(rp), depth=1)
            await self._index_path(repo_id, str(rp))
        except Exception as e:
            self.store.update(repo_id, status=IndexingStatus.FAILED, error=str(e))

    async def index_from_zip(self, zip_path: str, repo_name: str) -> Dict:
        repo = self.store.create(repo_name)
        asyncio.create_task(self._run_zip(repo["id"], zip_path))
        return repo

    async def _run_zip(self, repo_id: str, zip_path: str):
        try:
            self.store.update(repo_id, status=IndexingStatus.INDEXING)
            rp = Path(settings.repos_dir) / repo_id
            rp.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(str(rp))
            items = list(rp.iterdir())
            actual = items[0] if len(items) == 1 and items[0].is_dir() else rp
            await self._index_path(repo_id, str(actual))
        except Exception as e:
            self.store.update(repo_id, status=IndexingStatus.FAILED, error=str(e))
        finally:
            try:
                os.remove(zip_path)
            except Exception:
                pass

    async def _index_path(self, repo_id: str, repo_path: str):
        print(f"[Indexer] Parsing {repo_path}...")
        chunks = await asyncio.to_thread(self.parser.parse_repo, repo_path, repo_id)
        if not chunks:
            self.store.update(repo_id, status=IndexingStatus.FAILED, error="No parseable code found")
            return
        print(f"[Indexer] {len(chunks)} chunks found")

        # Build AST summary for router
        summary = self.parser.build_ast_summary(chunks)
        sp = Path(settings.repos_dir) / f"{repo_id}_summary.txt"
        with open(sp, "w") as f:
            f.write(summary)
        self._summaries[repo_id] = summary

        # Build dependency graph
        graph = DependencyGraph()
        await asyncio.to_thread(graph.build_from_chunks, chunks)
        self._graphs[repo_id] = graph
        gp = Path(settings.repos_dir) / f"{repo_id}_graph.json"
        await asyncio.to_thread(graph.save, str(gp))
        stats = graph.get_stats()
        print(f"[Indexer] Graph: {stats}")

        # Embed + store
        await asyncio.to_thread(self.vs.index_chunks, chunks, repo_id)

        files = len(set(c.file_path for c in chunks))
        funcs = sum(1 for c in chunks if c.chunk_type in ("function", "method"))
        langs = list(set(c.language for c in chunks))

        self.store.update(
            repo_id, status=IndexingStatus.READY,
            file_count=files, function_count=funcs,
            chunk_count=len(chunks), languages=langs,
        )
        print(f"[Indexer] Done: repo {repo_id}")


_instance: Optional[IndexerService] = None

def get_indexer() -> IndexerService:
    global _instance
    if _instance is None:
        _instance = IndexerService()
    return _instance
