# CodeRAG-R — Complete Setup Instructions

## What you're running
- **Backend**: FastAPI + Python (port 8000)
- **Frontend**: React + Vite (port 5173)
- **LLM**: Groq API (free — get key at console.groq.com)
- **Embeddings**: HuggingFace all-MiniLM-L6-v2 (downloads automatically, ~90MB)
- **Vector DB**: ChromaDB (runs locally, no cloud needed)
- **Graph**: NetworkX (pure Python)

---

## STEP 1 — Get your free Groq API key

1. Go to https://console.groq.com
2. Sign up (free, no credit card)
3. Click "API Keys" → "Create API Key"
4. Copy the key (starts with `gsk_...`)

---

## STEP 2 — Prerequisites (install once)

### Install Python 3.11+
Download from https://python.org/downloads
During install, CHECK "Add Python to PATH"

Verify in VS Code terminal:
```
python --version
```

### Install Node.js 18+
Download from https://nodejs.org (LTS version)

Verify:
```
node --version
npm --version
```

---

## STEP 3 — Open the project in VS Code

1. Extract the `coderag_r.zip` file
2. Open VS Code
3. File → Open Folder → select the `coderag_r` folder
4. Open the integrated terminal: View → Terminal (or Ctrl + `)

---

## STEP 4 — Set up the backend

### 4a. Open Terminal 1 in VS Code

Click the `+` button in the terminal panel to open a new terminal.

### 4b. Navigate to backend
```bash
cd backend
```

### 4c. Create virtual environment
```bash
python -m venv venv
```

### 4d. Activate virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### 4e. Install dependencies
```bash
pip install -r requirements.txt
```
This takes 3-5 minutes (downloads sentence-transformers, chromadb, etc.)

### 4f. Create your .env file
```bash
copy .env.example .env
```
(On Mac/Linux use: `cp .env.example .env`)

### 4g. Add your Groq API key
Open `backend/.env` in VS Code and replace:
```
GROQ_API_KEY=your_groq_api_key_here
```
with your actual key:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 4h. Start the backend
```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ Backend is running. Leave this terminal open.

---

## STEP 5 — Set up the frontend

### 5a. Open Terminal 2 in VS Code

Click `+` in the terminal panel (keep Terminal 1 running).

### 5b. Navigate to frontend
```bash
cd frontend
```

### 5c. Install npm packages
```bash
npm install
```
Takes 1-2 minutes.

### 5d. Start the frontend
```bash
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

✅ Frontend is running.

---

## STEP 6 — Open the app

Open your browser and go to:
```
http://localhost:5173
```

---

## STEP 7 — Add your first repository

### Option A — GitHub URL (needs internet)
1. Click `+` next to "Repositories" in the sidebar
2. Paste a GitHub URL: e.g. `https://github.com/tiangolo/fastapi`
3. Click "Add repo"
4. Wait for indexing (1-3 minutes depending on repo size)
5. Status changes to ✅ Ready when done

### Option B — Upload ZIP
1. Zip your local project folder
2. Click `+` → "Upload ZIP" tab
3. Select the zip file
4. Give it a name
5. Click "Add repo"

---

## STEP 8 — Start asking questions

Once status shows ✅ Ready:

1. Click on the repo in the sidebar
2. Type a question in the chat box, e.g.:
   - "How is authentication handled in this codebase?"
   - "What functions does the main class call?"
   - "Where is the database connection configured?"

### Retrieval modes (dropdown next to the input):
- **Auto** — LLM reads your AST and picks the best mode (recommended)
- **Tree** — Navigate AST structure (good for architecture questions)
- **Graph** — Follow call chains (good for "what calls what" questions)
- **Vector** — Semantic search fallback (good for fuzzy/broad questions)

### Dependency graph
Click "Dependency graph" at the bottom of the sidebar to see the interactive call graph.

---

## Troubleshooting

### "ModuleNotFoundError" when starting backend
Make sure venv is activated (`venv\Scripts\activate` on Windows)

### "GROQ_API_KEY not set" error
Check your `backend/.env` file has the real key, not the placeholder

### Tree-sitter install fails
Tree-sitter requires C build tools. On Windows install:
- https://visualstudio.microsoft.com/visual-cpp-build-tools/
Then retry `pip install -r requirements.txt`

If it still fails, the project gracefully falls back to line-based chunking — it still works.

### "No relevant code found" response
The repo may still be indexing. Wait for ✅ Ready status.

### Frontend shows blank page
Make sure backend is running on port 8000 before opening the frontend.

### Port already in use
```bash
# Change backend port in main.py:
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

# Change frontend port in vite.config.js:
server: { port: 5174 }
```

---

## Project structure (for reference)

```
coderag_r/
├── backend/
│   ├── main.py              ← FastAPI entry point
│   ├── config.py            ← Settings (reads .env)
│   ├── requirements.txt     ← Python deps
│   ├── .env.example         ← Copy to .env and add your key
│   ├── routers/
│   │   ├── repos.py         ← Repo CRUD + file tree endpoints
│   │   ├── query.py         ← SSE streaming query endpoint
│   │   └── graph.py         ← Dependency graph endpoint
│   ├── services/
│   │   ├── ast_parser.py    ← Tree-sitter AST chunker
│   │   ├── graph_builder.py ← NetworkX dependency graph
│   │   ├── vector_store.py  ← ChromaDB + HuggingFace embeddings
│   │   ├── query_router.py  ← LLM reasoning router (the novel part)
│   │   ├── query_engine.py  ← 3-mode retrieval + Groq generation
│   │   └── indexer.py       ← Orchestrates full indexing pipeline
│   └── models/
│       └── schemas.py       ← Pydantic models
├── frontend/
│   ├── src/
│   │   ├── App.jsx          ← Root layout
│   │   ├── main.jsx         ← React entry
│   │   ├── index.css        ← Tailwind + custom styles
│   │   ├── store/index.js   ← Zustand global state
│   │   ├── utils/api.js     ← API client + SSE streaming
│   │   ├── hooks/           ← useRepoPoll
│   │   ├── components/
│   │   │   ├── layout/      ← Sidebar
│   │   │   ├── repo/        ← FileTree, RepoHeader, AddRepoModal
│   │   │   ├── chat/        ← ChatMessage, ChatInput
│   │   │   └── graph/       ← D3 GraphPanel
│   │   └── pages/
│   │       ├── ChatPage.jsx ← Main Q&A interface
│   │       └── FileViewPage.jsx ← Code viewer
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
```

---

## Commands summary (quick reference)

```bash
# Terminal 1 — Backend
cd backend
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py

# Terminal 2 — Frontend  
cd frontend
npm install
npm run dev
```

Then open: http://localhost:5173
