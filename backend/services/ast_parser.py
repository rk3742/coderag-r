"""
AST-based code chunker using Tree-sitter.
Extracts functions, classes, methods as structured chunks — preserving
boundaries rather than naive line splits. Core differentiator of CodeRAG-R.
"""
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class CodeChunk:
    id: str
    repo_id: str
    file_path: str
    relative_path: str
    name: str
    chunk_type: str        # function | class | method | module
    code: str
    start_line: int
    end_line: int
    language: str
    docstring: Optional[str] = None
    parent_class: Optional[str] = None
    calls: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def to_embedding_text(self) -> str:
        parts = []
        if self.parent_class:
            parts.append(f"Class: {self.parent_class}")
        parts.append(f"{self.chunk_type.capitalize()}: {self.name}")
        if self.docstring:
            parts.append(f"Description: {self.docstring}")
        parts.append(f"File: {self.relative_path} lines {self.start_line}-{self.end_line}")
        parts.append(f"Code:\n{self.code}")
        return "\n".join(parts)

    def to_summary_line(self) -> str:
        parent = f" (in {self.parent_class})" if self.parent_class else ""
        return f"  {self.chunk_type} `{self.name}`{parent} @ {self.relative_path}:{self.start_line}"


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
    ".jsx": "javascript",
    ".tsx": "javascript",
}

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", ".next", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache",
}


class ASTParser:
    def __init__(self):
        self._parsers = {}
        self._tree_sitter_available = False
        self._setup_parsers()

    def _setup_parsers(self):
        try:
            import tree_sitter_python as tspython
            import tree_sitter_javascript as tsjavascript
            from tree_sitter import Language, Parser

            self._parsers["python"] = (Parser(Language(tspython.language())), None)
            self._parsers["javascript"] = (Parser(Language(tsjavascript.language())), None)
            self._tree_sitter_available = True
            print("[ASTParser] Tree-sitter loaded successfully")
        except Exception as e:
            print(f"[ASTParser] Tree-sitter not available, using fallback chunker: {e}")

    def _decode(self, val) -> str:
        return val.decode("utf8") if isinstance(val, bytes) else str(val)

    def parse_file(self, file_path: str, repo_id: str, repo_root: str) -> List[CodeChunk]:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return []
        language = SUPPORTED_EXTENSIONS[ext]
        relative_path = str(path.relative_to(repo_root))
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except Exception:
            return []
        if not source.strip():
            return []
        if self._tree_sitter_available and language in self._parsers:
            try:
                return self._parse_treesitter(source, file_path, relative_path, repo_id, language)
            except Exception as e:
                print(f"[ASTParser] Tree-sitter failed on {relative_path}: {e}")
        return self._parse_fallback(source, file_path, relative_path, repo_id, language)

    def _parse_treesitter(self, source, file_path, relative_path, repo_id, language) -> List[CodeChunk]:
        parser, _ = self._parsers[language]
        tree = parser.parse(bytes(source, "utf8"))
        lines = source.split("\n")
        if language == "python":
            chunks = self._extract_python(tree, lines, file_path, relative_path, repo_id)
        else:
            chunks = self._extract_js(tree, lines, file_path, relative_path, repo_id, language)
        return chunks if chunks else self._parse_fallback(source, file_path, relative_path, repo_id, language)

    def _get_docstring_python(self, node) -> Optional[str]:
        for child in node.children:
            if child.type == "block":
                for bc in child.children:
                    if bc.type == "expression_statement":
                        for sc in bc.children:
                            if sc.type == "string":
                                raw = self._decode(sc.text)
                                return raw.strip('"""').strip("'''").strip('"').strip("'").strip()[:300]
        return None

    def _get_calls_python(self, node) -> List[str]:
        calls = []
        def walk(n):
            if n.type == "call":
                for c in n.children:
                    if c.type in ("identifier", "attribute"):
                        calls.append(self._decode(c.text).split(".")[-1])
            for c in n.children:
                walk(c)
        walk(node)
        return list(set(calls))[:15]

    def _extract_python(self, tree, lines, file_path, relative_path, repo_id) -> List[CodeChunk]:
        chunks = []

        def visit(node, parent_class=None):
            if node.type in ("function_definition", "async_function_definition"):
                sl, el = node.start_point[0] + 1, node.end_point[0] + 1
                name = next(
                    (self._decode(c.text) for c in node.children if c.type == "identifier"), "unknown"
                )
                code = "\n".join(lines[sl - 1:el])[:3000]
                ctype = "method" if parent_class else "function"
                chunks.append(CodeChunk(
                    id=f"{repo_id}::{relative_path}::{name}::{sl}",
                    repo_id=repo_id, file_path=file_path, relative_path=relative_path,
                    name=name, chunk_type=ctype, code=code, start_line=sl, end_line=el,
                    language="python", docstring=self._get_docstring_python(node),
                    parent_class=parent_class, calls=self._get_calls_python(node),
                ))

            elif node.type == "class_definition":
                sl, el = node.start_point[0] + 1, node.end_point[0] + 1
                name = next(
                    (self._decode(c.text) for c in node.children if c.type == "identifier"), "UnknownClass"
                )
                code = "\n".join(lines[sl - 1:min(sl + 6, el)])
                chunks.append(CodeChunk(
                    id=f"{repo_id}::{relative_path}::class::{name}::{sl}",
                    repo_id=repo_id, file_path=file_path, relative_path=relative_path,
                    name=name, chunk_type="class", code=code, start_line=sl, end_line=el,
                    language="python", docstring=self._get_docstring_python(node),
                ))
                for child in node.children:
                    visit(child, parent_class=name)
                return

            for child in node.children:
                if node.type not in ("function_definition", "async_function_definition"):
                    visit(child)

        visit(tree.root_node)
        return chunks

    def _get_calls_js(self, node) -> List[str]:
        calls = []
        def walk(n):
            if n.type == "call_expression":
                func = n.child_by_field_name("function")
                if func:
                    calls.append(self._decode(func.text).split(".")[-1])
            for c in n.children:
                walk(c)
        walk(node)
        return list(set(calls))[:15]

    def _extract_js(self, tree, lines, file_path, relative_path, repo_id, language) -> List[CodeChunk]:
        chunks = []

        def visit(node, parent_class=None):
            if node.type in ("function_declaration", "method_definition", "arrow_function", "function_expression"):
                sl, el = node.start_point[0] + 1, node.end_point[0] + 1
                name_node = node.child_by_field_name("name")
                name = self._decode(name_node.text) if name_node else "anonymous"
                code = "\n".join(lines[sl - 1:el])[:3000]
                ctype = "method" if parent_class else "function"
                chunks.append(CodeChunk(
                    id=f"{repo_id}::{relative_path}::{name}::{sl}",
                    repo_id=repo_id, file_path=file_path, relative_path=relative_path,
                    name=name, chunk_type=ctype, code=code, start_line=sl, end_line=el,
                    language=language, parent_class=parent_class, calls=self._get_calls_js(node),
                ))

            elif node.type == "class_declaration":
                sl, el = node.start_point[0] + 1, node.end_point[0] + 1
                name_node = node.child_by_field_name("name")
                name = self._decode(name_node.text) if name_node else "UnknownClass"
                code = "\n".join(lines[sl - 1:min(sl + 6, el)])
                chunks.append(CodeChunk(
                    id=f"{repo_id}::{relative_path}::class::{name}::{sl}",
                    repo_id=repo_id, file_path=file_path, relative_path=relative_path,
                    name=name, chunk_type="class", code=code, start_line=sl, end_line=el,
                    language=language,
                ))
                for child in node.children:
                    visit(child, parent_class=name)
                return

            for child in node.children:
                visit(child)

        visit(tree.root_node)
        return chunks

    def _parse_fallback(self, source, file_path, relative_path, repo_id, language) -> List[CodeChunk]:
        chunks = []
        lines = source.split("\n")
        size = 40
        for i in range(0, len(lines), size):
            code = "\n".join(lines[i:i + size])
            if code.strip():
                chunks.append(CodeChunk(
                    id=f"{repo_id}::{relative_path}::block::{i}",
                    repo_id=repo_id, file_path=file_path, relative_path=relative_path,
                    name=f"block_{i // size}", chunk_type="module", code=code,
                    start_line=i + 1, end_line=min(i + size, len(lines)), language=language,
                ))
        return chunks

    def parse_repo(self, repo_path: str, repo_id: str) -> List[CodeChunk]:
        all_chunks = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for fname in files:
                fp = os.path.join(root, fname)
                if Path(fname).suffix.lower() in SUPPORTED_EXTENSIONS:
                    all_chunks.extend(self.parse_file(fp, repo_id, repo_path))
        return all_chunks

    def build_ast_summary(self, chunks: List[CodeChunk], max_chars: int = 6000) -> str:
        """
        Build a compact structural summary of the whole repo.
        This is what the LLM router reads to decide retrieval strategy.
        Format: file → classes → functions, one line each.
        """
        from collections import defaultdict
        by_file = defaultdict(list)
        for c in chunks:
            by_file[c.relative_path].append(c)

        lines = ["CODEBASE STRUCTURE SUMMARY", "=" * 40]
        for fpath, file_chunks in sorted(by_file.items()):
            lines.append(f"\n{fpath}:")
            for c in sorted(file_chunks, key=lambda x: x.start_line):
                lines.append(c.to_summary_line())
            if sum(len(l) for l in lines) > max_chars:
                lines.append("\n... (truncated)")
                break

        return "\n".join(lines)
