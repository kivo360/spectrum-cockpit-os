"""NetworkX-based graph storage implementation."""

from typing import List, Optional
from uuid import UUID

import networkx as nx

from ..models.task import GraphEdge, GraphNode
from .abstractions import AbstractGraphStorage


class NetworkXGraphStorage(AbstractGraphStorage):
    """NetworkX-based implementation of graph storage."""
    
    def __init__(self) -> None:
        """Initialize with directed graph."""
        self._graph = nx.DiGraph()
        self._nodes: dict[UUID, GraphNode] = {}
    
    async def add_node(self, node: GraphNode) -> bool:
        """Add node to NetworkX graph."""
        if node.id in self._nodes:
            return False
        
        self._nodes[node.id] = node
        self._graph.add_node(node.id)
        return True
    
    async def add_edge(self, edge: GraphEdge) -> bool:
        """Add edge to NetworkX graph."""
        # Check if nodes exist
        if edge.from_id not in self._nodes or edge.to_id not in self._nodes:
            return False
        
        # Check if would create cycle
        if await self._would_create_cycle(edge):
            return False
        
        self._graph.add_edge(
            edge.from_id,
            edge.to_id,
            relationship=edge.relationship
        )
        return True
    
    async def get_node(self, node_id: UUID) -> Optional[GraphNode]:
        """Get node by ID."""
        return self._nodes.get(node_id)
    
    async def remove_node(self, node_id: UUID) -> bool:
        """Remove node and all associated edges."""
        if node_id not in self._nodes:
            return False
        
        # Remove from NetworkX graph (automatically removes edges)
        self._graph.remove_node(node_id)
        
        # Remove from our node storage
        del self._nodes[node_id]
        return True
    
    async def remove_edge(self, edge: GraphEdge) -> bool:
        """Remove specific edge."""
        if not self._graph.has_edge(edge.from_id, edge.to_id):
            return False
        
        # Check if the relationship matches
        edge_data = self._graph.get_edge_data(edge.from_id, edge.to_id)
        if edge_data and edge_data.get("relationship") == edge.relationship:
            self._graph.remove_edge(edge.from_id, edge.to_id)
            return True
        
        return False
    
    async def get_dependencies(self, node_id: UUID) -> List[UUID]:
        """Get nodes this node depends on (successors in NetworkX)."""
        if node_id not in self._graph:
            return []
        return list(self._graph.successors(node_id))
    
    async def get_dependents(self, node_id: UUID) -> List[UUID]:
        """Get nodes that depend on this node (predecessors in NetworkX)."""
        if node_id not in self._graph:
            return []
        return list(self._graph.predecessors(node_id))
    
    async def has_cycle(self) -> bool:
        """Check if graph contains cycles using NetworkX."""
        return not nx.is_directed_acyclic_graph(self._graph)
    
    async def topological_sort(self) -> List[UUID]:
        """Return topologically sorted node IDs."""
        if await self.has_cycle():
            raise ValueError("Graph contains cycles")
        
        try:
            return list(nx.topological_sort(self._graph))
        except nx.NetworkXError as e:
            raise ValueError(f"Topological sort failed: {e}")
    
    async def get_all_nodes(self) -> List[GraphNode]:
        """Get all nodes."""
        return list(self._nodes.values())
    
    async def get_all_edges(self) -> List[GraphEdge]:
        """Get all edges."""
        edges = []
        for from_id, to_id, data in self._graph.edges(data=True):
            edge = GraphEdge(
                from_id=from_id,
                to_id=to_id,
                relationship=data.get("relationship", "depends_on")
            )
            edges.append(edge)
        return edges
    
    async def clear(self) -> None:
        """Clear all nodes and edges."""
        self._graph.clear()
        self._nodes.clear()
    
    async def _would_create_cycle(self, new_edge: GraphEdge) -> bool:
        """Check if adding edge would create cycle."""
        # Temporarily add edge
        self._graph.add_edge(
            new_edge.from_id,
            new_edge.to_id,
            relationship=new_edge.relationship
        )
        
        # Check for cycles
        has_cycle = not nx.is_directed_acyclic_graph(self._graph)
        
        # Remove temporary edge
        self._graph.remove_edge(new_edge.from_id, new_edge.to_id)
        
        return has_cycle
    
    # Additional NetworkX-specific methods
    
    async def get_shortest_path(
        self, from_id: UUID, to_id: UUID
    ) -> Optional[List[UUID]]:
        """Get shortest path between two nodes."""
        try:
            return nx.shortest_path(self._graph, from_id, to_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    async def get_descendants(self, node_id: UUID) -> List[UUID]:
        """Get all descendants of a node."""
        if node_id not in self._graph:
            return []
        return list(nx.descendants(self._graph, node_id))
    
    async def get_ancestors(self, node_id: UUID) -> List[UUID]:
        """Get all ancestors of a node."""
        if node_id not in self._graph:
            return []
        return list(nx.ancestors(self._graph, node_id))
    
    async def is_reachable(self, from_id: UUID, to_id: UUID) -> bool:
        """Check if to_id is reachable from from_id."""
        return nx.has_path(self._graph, from_id, to_id)
    
    async def get_graph_metrics(self) -> dict:
        """Get graph analysis metrics."""
        if len(self._graph) == 0:
            return {
                "node_count": 0,
                "edge_count": 0,
                "density": 0.0,
                "is_dag": True
            }
        
        return {
            "node_count": len(self._graph.nodes),
            "edge_count": len(self._graph.edges),
            "density": nx.density(self._graph),
            "is_dag": nx.is_directed_acyclic_graph(self._graph),
            "strongly_connected_components": len(
                list(nx.strongly_connected_components(self._graph))
            ),
            "weakly_connected_components": len(
                list(nx.weakly_connected_components(self._graph))
            )
        }