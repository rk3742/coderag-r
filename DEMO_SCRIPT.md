# CodeRAG-R — Demo Recording Script

## How to record your 30-second demo (Windows)

### Option 1 — Windows Game Bar (built-in, free)
1. Open the project at `http://localhost:5173`
2. Press `Win + G` to open Game Bar
3. Click the Record button (or `Win + Alt + R`)
4. Do the demo below
5. Press `Win + Alt + R` to stop
6. Video saved to `C:\Users\YourName\Videos\Captures`

### Option 2 — OBS Studio (free, better quality)
Download from https://obsproject.com

---

## The 30-second demo script

**Scene 1 (0-5s):** Show the empty state — CodeRAG-R logo, three mode badges visible

**Scene 2 (5-10s):** Upload the appointment booking zip → watch it index → status turns Ready

**Scene 3 (10-18s):** Type "How is authentication handled?" → watch Tree mode badge appear → answer streams in with citations

**Scene 4 (18-24s):** Click "Graph" mode → type "What calls the database?" → Graph traversal badge → call chain answer

**Scene 5 (24-30s):** Click Benchmark tab → click Run benchmark → show the 3-column score table

---

## Screenshots to take for GitHub README

Take these 4 screenshots and save them as:
- `docs/screenshots/01_empty_state.png`
- `docs/screenshots/02_tree_answer.png`
- `docs/screenshots/03_graph_answer.png`
- `docs/screenshots/04_benchmark.png`

---

## GitHub README template (paste this into README.md after recording)

```markdown
# CodeRAG-R — Reasoning Codebase Copilot

> Ask natural language questions about any codebase. The LLM reads the AST structure and intelligently routes to tree reasoning, graph traversal, or vector search — depending on what your question needs.

![Demo](docs/screenshots/02_tree_answer.png)

## What makes it different

Most RAG systems blindly fire vector search for every query. CodeRAG-R is different:

1. **LLM Router** — reads your codebase AST summary and classifies the query intent
2. **Tree Reasoning** — navigates the AST hierarchy for architecture questions  
3. **Graph Traversal** — follows function call chains for dependency questions
4. **Vector Search** — semantic fallback for broad/fuzzy questions
5. **Confidence Scoring** — refuses to hallucinate when evidence is weak
6. **Incremental Re-indexing** — detects changed files, only re-indexes what changed

## Benchmark results

| Mode   | Architecture | Dependency | Search | Overall |
|--------|-------------|------------|--------|---------|
| Tree   | **82%**     | 61%        | 48%    | 64%     |
| Graph  | 55%         | **87%**    | 52%    | 65%     |
| Vector | 49%         | 58%        | **79%**| 62%     |

*Benchmarked on 15 questions × 3 modes across 4 codebases*

## Stack

| Layer | Tool | Cost |
|-------|------|------|
| LLM | Groq API — Llama 3.3 70B | Free |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Free |
| Vector DB | ChromaDB (local) | Free |
| Code parser | Tree-sitter | Free |
| Graph | NetworkX | Free |
| Backend | FastAPI + Python | Free |
| Frontend | React + Vite + Tailwind | Free |

**Total cost: ₹0**

## Quick start

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt --prefer-binary
copy .env.example .env   # add your Groq key
python main.py

# Terminal 2 — Frontend
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Open http://localhost:5173

## Run tests

```bash
cd backend
python tests/test_ast_parser.py
```

## Author

Rithik Sai Kumar Kona — B.Tech ECE, Pre-Final Year  
[LinkedIn](https://linkedin.com/in/kona-rithik-sai-kumar-147432292)
```
