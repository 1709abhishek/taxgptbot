import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from typing import Optional as TypingOptional  # For global instance typing
import networkx as nx

from app.config import get_settings


@dataclass
class GraphResult:
    """Result from graph traversal."""

    content: str
    score: float
    path: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class GraphStore:
    """NetworkX-based knowledge graph for financial entities."""

    def __init__(self, persist_path: str = None):
        settings = get_settings()
        self.persist_path = Path(persist_path or settings.graph_persist_path)

        self.graph = nx.DiGraph()
        self.last_updated: Optional[datetime] = None

        # Load existing graph if available
        self._load()

    def add_extraction(self, extraction: Dict[str, Any]) -> None:
        """Add extracted entities and relationships to the graph."""
        source_chunk_id = extraction.get("source_chunk_id")
        source_file = extraction.get("source_file")

        # Add entity nodes
        for entity in extraction.get("entities", []):
            node_id = self._entity_to_node_id(entity)
            self.graph.add_node(
                node_id,
                type=entity.get("type"),
                name=entity.get("name"),
                source_chunk_id=source_chunk_id,
                source_file=source_file,
                **{k: v for k, v in entity.items() if k not in ["type", "name"]},
            )

        # Add relationship edges
        for rel in extraction.get("relationships", []):
            from_id = rel["from"]
            to_id = rel["to"]
            relation = rel["relation"]

            self.graph.add_edge(
                from_id,
                to_id,
                relation=relation,
                source_chunk_id=source_chunk_id,
            )

        self.last_updated = datetime.now()

    def search(self, query: str, entities: List[str] = None, k: int = 10) -> List[GraphResult]:
        """
        Search graph for relevant information.
        If entities are provided, traverse from those nodes.
        Otherwise, do fuzzy matching on node names.
        """
        results = []

        if entities:
            # Traverse from specific entities
            for entity in entities:
                # Find matching node (case-insensitive exact match first)
                entity_lower = entity.lower()
                matching_node = None

                for node_id in self.graph.nodes():
                    if node_id.lower() == entity_lower:
                        matching_node = node_id
                        break

                # If no exact match, try substring match
                if not matching_node:
                    for node_id, data in self.graph.nodes(data=True):
                        name = data.get("name", node_id)
                        if isinstance(name, str) and entity_lower in name.lower():
                            matching_node = node_id
                            break

                if matching_node:
                    node_data = self.graph.nodes[matching_node]
                    results.append(self._node_to_result(matching_node, node_data, score=1.0))
                    # Then traverse for related nodes
                    node_results = self._traverse_from_entity(matching_node, depth=2)
                    results.extend(node_results)

        # Also do fuzzy search if no entities provided OR to supplement entity search
        if not entities or not results:
            # Fuzzy match query against node names
            query_lower = query.lower()
            query_words = set(query_lower.split())

            for node_id, data in self.graph.nodes(data=True):
                name = data.get("name", node_id)
                if not isinstance(name, str):
                    continue

                name_lower = name.lower()

                # Check for substring match or word overlap
                is_match = (
                    query_lower in name_lower or  # Query is substring of name
                    name_lower in query_lower or  # Name is substring of query
                    len(query_words & set(name_lower.split())) >= 2  # At least 2 words overlap
                )

                if is_match:
                    # Add the matching node itself as a result
                    results.append(self._node_to_result(node_id, data, score=1.0))
                    # Also traverse for related nodes
                    node_results = self._traverse_from_entity(node_id, depth=2)
                    results.extend(node_results)

        # Deduplicate and sort by score
        seen = set()
        unique_results = []
        for result in results:
            key = result.content
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        unique_results.sort(key=lambda x: x.score, reverse=True)
        return unique_results[:k]

    def _node_to_result(self, node_id: str, data: Dict[str, Any], score: float = 1.0) -> GraphResult:
        """Convert a graph node to a GraphResult."""
        # Build content from node data
        node_type = data.get("type", "entity")
        name = data.get("name", node_id)
        value = data.get("value")
        period = data.get("period")

        content_parts = [f"{node_type}: {name}"]
        if value:
            content_parts.append(f"value: {value}")
        if period:
            content_parts.append(f"period: {period}")

        content = " | ".join(content_parts)

        return GraphResult(
            content=content,
            score=score,
            path=[{"node": node_id, "type": node_type, "value": value}],
            metadata={
                "source_chunk_id": data.get("source_chunk_id"),
                "source_file": data.get("source_file"),
            },
        )

    def _traverse_from_entity(self, entity: str, depth: int = 2) -> List[GraphResult]:
        """Traverse graph from an entity to find related information."""
        results = []

        if entity not in self.graph:
            return results

        # BFS traversal up to depth
        visited = {entity}
        queue = [(entity, 0, [{"node": entity, "type": self.graph.nodes[entity].get("type", "unknown")}])]

        while queue:
            current, current_depth, path = queue.pop(0)

            if current_depth >= depth:
                continue

            # Get neighbors
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)

                    edge_data = self.graph.edges[current, neighbor]
                    node_data = self.graph.nodes[neighbor]

                    new_path = path + [
                        {"edge": edge_data.get("relation", "RELATED"), "direction": "->"},
                        {
                            "node": neighbor,
                            "type": node_data.get("type", "unknown"),
                            "value": node_data.get("value"),
                        },
                    ]

                    # Create result for this traversal
                    content = self._path_to_text(new_path)
                    results.append(
                        GraphResult(
                            content=content,
                            score=1.0 / (current_depth + 1),  # Closer = higher score
                            path=new_path,
                            metadata={
                                "source_chunk_id": node_data.get("source_chunk_id"),
                                "source_file": node_data.get("source_file"),
                            },
                        )
                    )

                    queue.append((neighbor, current_depth + 1, new_path))

        return results

    def _entity_to_node_id(self, entity: Dict[str, Any]) -> str:
        """Generate a unique node ID from entity."""
        name = entity.get("name", "unknown")
        entity_type = entity.get("type", "entity")
        value = entity.get("value", "")
        period = entity.get("period", "")

        if value or period:
            return f"{name}_{value}_{period}".replace(" ", "_")
        return name

    def _path_to_text(self, path: List[Dict[str, Any]]) -> str:
        """Convert a graph path to readable text."""
        parts = []
        for item in path:
            if "node" in item:
                value = item.get("value")
                if value:
                    parts.append(f"{item['node']} ({value})")
                else:
                    parts.append(item["node"])
            elif "edge" in item:
                parts.append(f"-[{item['edge']}]->")

        return " ".join(parts)

    def node_count(self) -> int:
        """Get number of nodes in the graph."""
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        """Get number of edges in the graph."""
        return self.graph.number_of_edges()

    def query_transactions(
        self,
        taxpayer_type: str = None,
        state: str = None,
        income_source: str = None,
        deduction_type: str = None,
        tax_year: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Query transaction nodes with optional filters.

        Returns list of transaction data matching the filters.
        """
        transactions = []

        # Find all transaction nodes
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") != "transaction":
                continue

            # Check filters by traversing relationships
            matches = True

            if taxpayer_type:
                # Check if transaction is connected to this taxpayer type
                connected = False
                for neighbor in self.graph.neighbors(node_id):
                    edge = self.graph.edges[node_id, neighbor]
                    if edge.get("relation") == "FILED_BY" and neighbor.lower() == taxpayer_type.lower():
                        connected = True
                        break
                if not connected:
                    matches = False

            if state and matches:
                connected = False
                for neighbor in self.graph.neighbors(node_id):
                    edge = self.graph.edges[node_id, neighbor]
                    if edge.get("relation") == "FILED_IN" and neighbor.lower() == state.lower():
                        connected = True
                        break
                if not connected:
                    matches = False

            if income_source and matches:
                connected = False
                for neighbor in self.graph.neighbors(node_id):
                    edge = self.graph.edges[node_id, neighbor]
                    if edge.get("relation") == "HAS_INCOME" and neighbor.lower() == income_source.lower():
                        connected = True
                        break
                if not connected:
                    matches = False

            if deduction_type and matches:
                connected = False
                for neighbor in self.graph.neighbors(node_id):
                    edge = self.graph.edges[node_id, neighbor]
                    if edge.get("relation") == "CLAIMED_DEDUCTION" and neighbor.lower() == deduction_type.lower():
                        connected = True
                        break
                if not connected:
                    matches = False

            if tax_year and matches:
                connected = False
                for neighbor in self.graph.neighbors(node_id):
                    edge = self.graph.edges[node_id, neighbor]
                    if edge.get("relation") == "FOR_YEAR" and neighbor == str(tax_year):
                        connected = True
                        break
                if not connected:
                    matches = False

            if matches:
                transactions.append({
                    "node_id": node_id,
                    "income": data.get("income", 0),
                    "deductions": data.get("deductions", 0),
                    "taxable_income": data.get("taxable_income", 0),
                    "tax_rate": data.get("tax_rate", 0),
                    "tax_owed": data.get("tax_owed", 0),
                    "date": data.get("date", ""),
                })

        return transactions

    def query_aggregate(
        self,
        taxpayer_type: str = None,
        state: str = None,
        income_source: str = None,
        deduction_type: str = None,
        tax_year: str = None,
    ) -> Dict[str, Any]:
        """
        Query aggregations like avg tax rate, total income, etc.

        Returns aggregated statistics for transactions matching filters.
        """
        transactions = self.query_transactions(
            taxpayer_type=taxpayer_type,
            state=state,
            income_source=income_source,
            deduction_type=deduction_type,
            tax_year=tax_year,
        )

        if not transactions:
            return {
                "count": 0,
                "message": "No matching transactions found",
            }

        # Compute aggregations
        incomes = [t["income"] for t in transactions]
        deductions = [t["deductions"] for t in transactions]
        tax_rates = [t["tax_rate"] for t in transactions]
        taxes_owed = [t["tax_owed"] for t in transactions]

        return {
            "count": len(transactions),
            "total_income": sum(incomes),
            "avg_income": sum(incomes) / len(incomes),
            "total_deductions": sum(deductions),
            "avg_deductions": sum(deductions) / len(deductions),
            "avg_tax_rate": sum(tax_rates) / len(tax_rates),
            "total_tax_owed": sum(taxes_owed),
            "avg_tax_owed": sum(taxes_owed) / len(taxes_owed),
            "filters_applied": {
                "taxpayer_type": taxpayer_type,
                "state": state,
                "income_source": income_source,
                "deduction_type": deduction_type,
                "tax_year": tax_year,
            },
        }

    def get_dimension_values(self, dimension_type: str) -> List[str]:
        """
        Get all unique values for a dimension type.

        Args:
            dimension_type: One of 'taxpayer_type', 'state', 'income_source',
                          'deduction_type', 'tax_year'

        Returns:
            List of unique values for that dimension
        """
        values = set()
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == dimension_type:
                values.add(data.get("name", node_id))
        return sorted(list(values))

    def get_graph_summary(self) -> Dict[str, Any]:
        """Get a summary of the graph structure."""
        summary = {
            "total_nodes": self.node_count(),
            "total_edges": self.edge_count(),
            "node_types": {},
            "relationship_types": {},
        }

        # Count nodes by type
        for _, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            summary["node_types"][node_type] = summary["node_types"].get(node_type, 0) + 1

        # Count edges by relationship type
        for _, _, data in self.graph.edges(data=True):
            rel_type = data.get("relation", "unknown")
            summary["relationship_types"][rel_type] = summary["relationship_types"].get(rel_type, 0) + 1

        return summary

    def persist(self) -> None:
        """Save graph to disk."""
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persist_path, "wb") as f:
            pickle.dump(
                {"graph": self.graph, "last_updated": self.last_updated}, f
            )

    def _load(self) -> None:
        """Load graph from disk if available."""
        if self.persist_path.exists():
            try:
                with open(self.persist_path, "rb") as f:
                    data = pickle.load(f)
                    self.graph = data["graph"]
                    self.last_updated = data.get("last_updated")
            except Exception:
                # Start fresh if loading fails
                self.graph = nx.DiGraph()

    def clear(self) -> None:
        """Clear the graph."""
        self.graph = nx.DiGraph()
        self.last_updated = None
        if self.persist_path.exists():
            self.persist_path.unlink()


# Global instance (no lru_cache to allow proper reloading)
_graph_store_instance: GraphStore = None


def get_graph_store() -> GraphStore:
    """Get singleton graph store."""
    global _graph_store_instance
    if _graph_store_instance is None:
        _graph_store_instance = GraphStore()
    return _graph_store_instance


def reset_graph_store() -> None:
    """Reset the graph store singleton (useful for testing/reload)."""
    global _graph_store_instance
    _graph_store_instance = None
