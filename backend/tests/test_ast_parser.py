"""
Tests for the AST parser — the core chunking engine of CodeRAG-R.
Run with: python -m pytest tests/ -v
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ast_parser import ASTParser, CodeChunk

parser = ASTParser()

# ── Helpers ──────────────────────────────────────────────────────────────────

def write_temp(content: str, suffix: str = ".py") -> str:
    """Write content to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    f.write(content)
    f.flush()
    f.close()
    return f.name


# ── TEST 1: Python function extraction ───────────────────────────────────────

def test_python_function_extraction():
    """Parser must extract Python functions or fallback blocks."""
    code = '''
def authenticate_user(email, password):
    """Authenticate a user with email and password."""
    user = find_user_by_email(email)
    if not user:
        return None
    return verify_password(password, user.hashed_password)

def generate_token(user_id):
    """Generate a JWT token for the user."""
    return jwt.encode({"id": user_id}, SECRET_KEY)
'''
    fp = write_temp(code, ".py")
    try:
        chunks = parser.parse_file(fp, "test_repo", os.path.dirname(fp))
        assert len(chunks) > 0, "Parser must return at least one chunk"

        if parser._tree_sitter_available:
            # With Tree-sitter: expect individual functions
            func_names = [c.name for c in chunks if c.chunk_type in ("function", "method")]
            assert "authenticate_user" in func_names, f"Expected authenticate_user, got {func_names}"
            assert "generate_token" in func_names, f"Expected generate_token, got {func_names}"
            print(f"  ✓ Tree-sitter extracted functions: {func_names}")
        else:
            # Fallback mode: expect block chunks containing the code
            all_code = " ".join(c.code for c in chunks)
            assert "authenticate_user" in all_code, "Function name must appear in block code"
            assert "generate_token" in all_code, "Function name must appear in block code"
            print(f"  ✓ Fallback chunker: {len(chunks)} blocks, code contains function names")
    finally:
        os.unlink(fp)


# ── TEST 2: Python class + method extraction ─────────────────────────────────

def test_python_class_method_extraction():
    """Parser must extract class definitions or fallback blocks containing them."""
    code = '''
class UserController:
    """Handles user-related operations."""

    def __init__(self, db):
        self.db = db

    def get_user(self, user_id):
        return self.db.find(user_id)

    def delete_user(self, user_id):
        return self.db.delete(user_id)
'''
    fp = write_temp(code, ".py")
    try:
        chunks = parser.parse_file(fp, "test_repo", os.path.dirname(fp))
        assert len(chunks) > 0, "Parser must return at least one chunk"

        if parser._tree_sitter_available:
            names = [c.name for c in chunks]
            types = [c.chunk_type for c in chunks]
            assert "UserController" in names, f"Class not found. Got: {names}"
            assert "class" in types, "No class chunk type found"
            methods = [c.name for c in chunks if c.chunk_type == "method"]
            assert "get_user" in methods or "get_user" in names, f"Method get_user not found"
            print(f"  ✓ Tree-sitter extracted class + methods: {names}")
        else:
            # Fallback: block chunks should contain the class code
            all_code = " ".join(c.code for c in chunks)
            assert "UserController" in all_code, "Class name must appear in block code"
            assert "get_user" in all_code, "Method name must appear in block code"
            print(f"  ✓ Fallback chunker: {len(chunks)} blocks, code contains class and methods")
    finally:
        os.unlink(fp)


# ── TEST 3: Chunk metadata accuracy ──────────────────────────────────────────

def test_chunk_metadata_accuracy():
    """Each chunk must have correct file path, line numbers, and language."""
    code = '''def hello_world():
    print("hello")
    return True
'''
    fp = write_temp(code, ".py")
    try:
        chunks = parser.parse_file(fp, "repo_123", os.path.dirname(fp))
        assert len(chunks) > 0, "No chunks returned"
        chunk = chunks[0]
        assert chunk.repo_id == "repo_123", f"Wrong repo_id: {chunk.repo_id}"
        assert chunk.language == "python", f"Wrong language: {chunk.language}"
        assert chunk.start_line >= 1, f"start_line must be >= 1, got {chunk.start_line}"
        assert chunk.end_line >= chunk.start_line, "end_line must be >= start_line"
        assert chunk.code.strip() != "", "Code must not be empty"
        print(f"  ✓ Chunk metadata: lang={chunk.language}, lines={chunk.start_line}-{chunk.end_line}")
    finally:
        os.unlink(fp)


# ── TEST 4: Call extraction ───────────────────────────────────────────────────

def test_call_extraction():
    """Parser must extract function calls (Tree-sitter) or code blocks (fallback)."""
    code = '''
def process_booking(user_id, slot_id):
    user = get_user(user_id)
    slot = find_slot(slot_id)
    notify_user(user.email)
    return create_booking(user, slot)
'''
    fp = write_temp(code, ".py")
    try:
        chunks = parser.parse_file(fp, "test_repo", os.path.dirname(fp))
        assert len(chunks) > 0, "Parser must return at least one chunk"

        if parser._tree_sitter_available:
            func_chunks = [c for c in chunks if c.name == "process_booking"]
            assert len(func_chunks) > 0, "process_booking function not found"
            calls = func_chunks[0].calls
            assert len(calls) > 0, f"No calls extracted from process_booking. Calls: {calls}"
            print(f"  ✓ Tree-sitter extracted calls: {calls}")
        else:
            # Fallback: verify the code is captured in blocks
            all_code = " ".join(c.code for c in chunks)
            assert "process_booking" in all_code, "Function must appear in block code"
            assert "get_user" in all_code, "Called function must appear in code"
            # In fallback mode, calls list will be empty — that's expected
            print(f"  ✓ Fallback chunker: {len(chunks)} blocks (Tree-sitter needed for call extraction)")
    finally:
        os.unlink(fp)


# ── TEST 5: AST structure summary ────────────────────────────────────────────

def test_ast_structure_summary():
    """build_ast_summary must return a non-empty string with file and function names."""
    code = '''
def login(email, password):
    return authenticate(email, password)

class AuthService:
    def verify_token(self, token):
        return jwt.decode(token, SECRET)
'''
    fp = write_temp(code, ".py")
    try:
        chunks = parser.parse_file(fp, "test_repo", os.path.dirname(fp))
        assert len(chunks) > 0, "No chunks to summarize"
        summary = parser.build_ast_summary(chunks)
        assert isinstance(summary, str), "Summary must be a string"
        assert len(summary) > 20, f"Summary too short: {repr(summary)}"
        assert "CODEBASE STRUCTURE" in summary, "Summary missing header"
        print(f"  ✓ AST summary generated ({len(summary)} chars)")
        print(f"    Preview: {summary[:120]}...")
    finally:
        os.unlink(fp)


# ── TEST 6: Embedding text generation ────────────────────────────────────────

def test_embedding_text_generation():
    """to_embedding_text must include function name, file path, and code."""
    chunk = CodeChunk(
        id="repo::auth.py::login::10",
        repo_id="repo",
        file_path="/tmp/auth.py",
        relative_path="auth.py",
        name="login",
        chunk_type="function",
        code="def login(email, password):\n    return True",
        start_line=10,
        end_line=12,
        language="python",
        docstring="Handles user login",
        parent_class=None,
        calls=["authenticate"],
    )
    text = chunk.to_embedding_text()
    assert "login" in text, "Function name not in embedding text"
    assert "auth.py" in text, "File path not in embedding text"
    assert "def login" in text, "Code not in embedding text"
    assert "Handles user login" in text, "Docstring not in embedding text"
    print(f"  ✓ Embedding text ({len(text)} chars): {text[:80]}...")


# ── TEST 7: Confidence scorer ─────────────────────────────────────────────────

def test_confidence_scorer():
    """Confidence scorer must correctly classify high/medium/low/none levels."""
    from services.confidence import compute_confidence

    # High confidence — strong scores
    high_chunks = [{"relevance_score": 0.85, "retrieval_method": "vector"},
                   {"relevance_score": 0.78, "retrieval_method": "graph"},
                   {"relevance_score": 0.72, "retrieval_method": "tree"}]
    score, level, msg = compute_confidence(high_chunks, "test question")
    assert level == "high", f"Expected high, got {level} (score={score})"
    print(f"  ✓ High confidence: score={score}, level={level}")

    # Low confidence — weak scores
    low_chunks = [{"relevance_score": 0.15, "retrieval_method": "vector"},
                  {"relevance_score": 0.12, "retrieval_method": "vector"}]
    score, level, msg = compute_confidence(low_chunks, "test question")
    assert level in ("low", "none"), f"Expected low/none, got {level} (score={score})"
    print(f"  ✓ Low confidence: score={score}, level={level}")

    # Empty — no confidence
    score, level, msg = compute_confidence([], "test question")
    assert level == "none", f"Expected none for empty chunks, got {level}"
    assert score == 0.0, f"Expected 0.0 score for empty, got {score}"
    print(f"  ✓ Empty confidence: score={score}, level={level}")


# ── TEST 8: Graph builder ─────────────────────────────────────────────────────

def test_dependency_graph_build():
    """Graph builder must create nodes and edges from chunk call lists."""
    from services.graph_builder import DependencyGraph

    chunks = [
        CodeChunk(id="repo::main.py::main::1", repo_id="repo", file_path="main.py",
                  relative_path="main.py", name="main", chunk_type="function",
                  code="def main(): setup(); run()", start_line=1, end_line=3,
                  language="python", calls=["setup", "run"]),
        CodeChunk(id="repo::main.py::setup::5", repo_id="repo", file_path="main.py",
                  relative_path="main.py", name="setup", chunk_type="function",
                  code="def setup(): pass", start_line=5, end_line=6,
                  language="python", calls=[]),
        CodeChunk(id="repo::main.py::run::8", repo_id="repo", file_path="main.py",
                  relative_path="main.py", name="run", chunk_type="function",
                  code="def run(): pass", start_line=8, end_line=9,
                  language="python", calls=[]),
    ]

    graph = DependencyGraph()
    graph.build_from_chunks(chunks)
    stats = graph.get_stats()

    assert stats["nodes"] == 3, f"Expected 3 nodes, got {stats['nodes']}"
    assert stats["edges"] >= 2, f"Expected at least 2 edges, got {stats['edges']}"

    # main should have setup and run as neighbors
    neighbors = graph.get_neighbors("repo::main.py::main::1", depth=1)
    assert len(neighbors) >= 1, f"main should have neighbors, got {neighbors}"
    print(f"  ✓ Graph: {stats['nodes']} nodes, {stats['edges']} edges, neighbors={len(neighbors)}")


# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("Python function extraction",   test_python_function_extraction),
        ("Python class + method",        test_python_class_method_extraction),
        ("Chunk metadata accuracy",      test_chunk_metadata_accuracy),
        ("Call extraction",              test_call_extraction),
        ("AST structure summary",        test_ast_structure_summary),
        ("Embedding text generation",    test_embedding_text_generation),
        ("Confidence scorer",            test_confidence_scorer),
        ("Dependency graph build",       test_dependency_graph_build),
    ]

    passed = 0
    failed = 0
    print("\n" + "="*55)
    print("  CodeRAG-R Test Suite")
    print("="*55)

    for name, fn in tests:
        print(f"\nTest: {name}")
        try:
            fn()
            print(f"  PASS ✓")
            passed += 1
        except Exception as e:
            print(f"  FAIL ✗  →  {e}")
            failed += 1

    print("\n" + "="*55)
    print(f"  Results: {passed}/{len(tests)} passed  |  {failed} failed")
    print("="*55 + "\n")

    if failed > 0:
        sys.exit(1)
