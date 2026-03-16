from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    groq_api_key: str = ""
    chroma_persist_dir: str = "./data/chroma"
    repos_dir: str = "./data/repos"
    hf_model: str = "all-MiniLM-L6-v2"
    groq_model: str = "llama-3.1-70b-versatile"
    max_tokens: int = 1500
    temperature: float = 0.1
    top_k_retrieval: int = 8
    graph_neighbor_depth: int = 2

    class Config:
        env_file = ".env"


settings = Settings()

Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
Path(settings.repos_dir).mkdir(parents=True, exist_ok=True)
