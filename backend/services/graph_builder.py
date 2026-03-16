"""
NetworkX-based dependency graph.
Nodes = functions/classes. Edges = call relationships.
Used for graph traversal retrieval mode.
"""
import json
import networkx as nx
from typing import List, Dict, Set, Optional
from services.ast_parser import CodeChunk


class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._name_index: Dict[str, List[str]] = {}

    def build_from_chunks(self, chunks: List[CodeChunk]):
        self.graph.clear()
        self._name_index.clear()

        for chunk in chunks:
            self.graph.add_node(chunk.id, **{
                "name": chunk.name,
                "file": chunk.relative_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "type": chunk.chunk_type,
                "language": chunk.language,
            })
            name = chunk.name.lower()
            self._name_index.setdefault(name, []).append(chunk.id)

        for chunk in chunks:
            for called in chunk.calls:
                for tid in self._name_index.get(called.lower(), []):
                    if tid != chunk.id:
                        self.graph.add_edge(chunk.id, tid, label="calls")

    def get_neighbors(self, chunk_id: str, depth: int = 2) -> Set[str]:
        if chunk_id not in self.graph:
            return set()
        result = set()
        try:
            result.update(nx.single_source_shortest_path_length(self.graph, chunk_id, cutoff=depth).keys())
        except Exception:
            pass
        try:
            result.update(nx.single_source_shortest_path_length(self.graph.reverse(), chunk_id, cutoff=1).keys())
        except Exception:
            pass
        result.discard(chunk_id)
        return result

    def get_stats(self) -> Dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
        }

    def to_vis_data(self, max_nodes: int = 150) -> Dict:
        g = self.graph
        if g.number_of_nodes() > max_nodes:
            top = sorted(g.nodes(), key=lambda n: g.degree(n), reverse=True)[:max_nodes]
            g = g.subgraph(top)
        nodes = [{"id": nid, "label": d.get("name", nid), "file": d.get("file", ""),
                  "line": d.get("start_line", 0), "type": d.get("type", "function")}
                 for nid, d in g.nodes(data=True)]
        edges = [{"source": s, "target": t, "label": "calls"} for s, t in g.edges()]
        return {"nodes": nodes, "edges": edges,
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges()}

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(nx.node_link_data(self.graph), f)

    def load(self, path: str):
        with open(path) as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data)
        self._name_index.clear()
        for nid, nd in self.graph.nodes(data=True):
            name = nd.get("name", "").lower()
            if name:
                self._name_index.setdefault(name, []).append(nid)
