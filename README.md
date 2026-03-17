# CodeRAG-R — Reasoning Codebase Copilot

> Ask natural language questions about any codebase. The LLM reads the AST structure and intelligently routes to **tree reasoning**, **graph traversal**, or **vector search** — depending on what your question needs.

## What makes it different

Most RAG systems blindly fire vector search for every query. CodeRAG-R is different:

| Feature | What it does |
|---|---|
| **LLM Query Router** | Reads codebase AST summary, classifies query intent, picks retrieval mode |
| **Tree Reasoning** | Navigates AST hierarchy for architecture/structure questions |
| **Graph Traversal** | Follows function call chains for dependency questions |
| **Vector Search** | Semantic fallback for broad/fuzzy questions |
| **Confidence Scoring** | Refuses to hallucinate when retrieved evidence is weak |
| **Incremental Re-indexing** | Detects changed files, only re-indexes what changed |
| **Benchmark Harness** | 15-question eval suite proving which mode wins per query type |

## Benchmark results (real data — Appointment Booking System)

Benchmarked across 15 questions × 3 retrieval modes = 45 total queries.

| Mode | Avg Score | Pass Rate | Avg Latency |
|---|---|---|---|
| Tree reasoning | **66%** | 53% | 1217ms |
| Graph traversal | 64% | 53% | 983ms |
| Vector search | 65% | 53% | 1236ms |

**Best mode per question type:**

| Question type | Tree | Graph | Vector | Winner |
|---|---|---|---|---|
| Architecture | 52% | 52% | 52% | Tree |
| Dependency | **76%** | 71% | 74% | **Tree** |
| Search | **69%** | 69% | 69% | **Tree** |

*Tree reasoning wins on dependency questions by 5% over vector — proving structured AST navigation outperforms similarity search for call-chain questions.*

## Stack — 100% free

| Layer | Tool |
|---|---|
| LLM | Groq API — Llama 3.3 70B (free tier) |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (free) |
| Vector DB | ChromaDB (local, no cloud) |
| Code parser | Tree-sitter (AST-level chunking) |
| Dependency graph | NetworkX |
| Backend | FastAPI + Python |
| Frontend | React + Vite + Tailwind |

**Total infrastructure cost: ₹0**

## Quick start

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && venv\Scripts\activate      # Windows
pip install -r requirements.txt --prefer-binary
copy .env.example .env   # add your free Groq key from console.groq.com
python main.py

# Terminal 2 — Frontend
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Open **http://localhost:5173**

## Run tests

```bash
cd backend
venv\Scripts\activate
python tests/test_ast_parser.py
```

Expected output: `Results: 8/8 passed | 0 failed`

## Run benchmark

Open the app → select a repo → click **Benchmark** tab → click **Run benchmark**

Results appear in ~5 minutes. Raw JSON saved to `backend/data/eval_results/`

## Project structure

```
coderag_r/
├── backend/
│   ├── services/
│   │   ├── ast_parser.py          # Tree-sitter AST chunker + summary builder
│   │   ├── graph_builder.py       # NetworkX dependency graph
│   │   ├── vector_store.py        # ChromaDB + HuggingFace embeddings
│   │   ├── query_router.py        # LLM routing engine (the novel part)
│   │   ├── query_engine.py        # 3-mode retrieval + Groq generation
│   │   ├── confidence.py          # Anti-hallucination confidence scoring
│   │   ├── evaluator.py           # Benchmark harness
│   │   └── incremental_indexer.py # Changed-file detection + partial re-index
│   └── tests/
│       └── test_ast_parser.py     # 8 tests — 8/8 passing
└── frontend/
    └── src/
        ├── pages/
        │   ├── ChatPage.jsx        # Streaming Q&A with citations
        │   ├── BenchmarkPage.jsx   # Visual benchmark results
        │   └── FileViewPage.jsx    # Code viewer with syntax highlighting
        └── components/             # Sidebar, FileTree, GraphPanel, ChatMessage
```

## Author

**Rithik Sai Kumar Kona** — B.Tech ECE, Pre-Final Year, Chennai  
[LinkedIn](https://linkedin.com/in/kona-rithik-sai-kumar-147432292) · konarithiksai@gmail.com



BUILT BY KONA RITHIK SAI KUMAR
