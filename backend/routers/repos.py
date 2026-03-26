from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import tempfile, os
from typing import Optional
from models.schemas import RepoCreate
from services.indexer import get_indexer

router = APIRouter()


@router.get("/")
async def list_repos():
    return get_indexer().get_all_repos()


@router.post("/github")
async def add_github(body: RepoCreate):
    if not body.github_url.startswith("https://github.com"):
        raise HTTPException(400, "Only https://github.com URLs are supported")
    return await get_indexer().index_from_github(body.github_url, body.name)


@router.post("/upload")
async def upload_zip(file: UploadFile = File(...), name: str = Form(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files are supported")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        tmp.write(await file.read())
        tmp.close()
        return await get_indexer().index_from_zip(tmp.name, name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


@router.get("/{repo_id}")
async def get_repo(repo_id: str):
    repo = get_indexer().get_repo(repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    return repo


@router.delete("/{repo_id}")
async def delete_repo(repo_id: str):
    if not get_indexer().get_repo(repo_id):
        raise HTTPException(404, "Repository not found")
    get_indexer().delete_repo(repo_id)
    return {"message": "Deleted"}


@router.get("/{repo_id}/files")
async def file_tree(repo_id: str):
    tree = get_indexer().get_file_tree(repo_id)
    if tree is None:
        raise HTTPException(404, "Files not found")
    return tree


@router.get("/{repo_id}/file")
async def file_content(repo_id: str, path: str):
    content = get_indexer().get_file_content(repo_id, path)
    if content is None:
        raise HTTPException(404, "File not found")
    return {"content": content, "path": path}


@router.get("/{repo_id}/summary")
async def get_summary(repo_id: str):
    summary = get_indexer().get_summary(repo_id)
    return {"summary": summary}
