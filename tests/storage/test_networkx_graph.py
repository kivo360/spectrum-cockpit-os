"""Tests for NetworkX graph storage implementation."""

import pytest
from uuid import uuid4

from src.models.task import GraphEdge, GraphNode
from src.storage.networkx_graph import NetworkXGraphStorage


class TestNetworkXGraphStorage:
    """Test NetworkX graph storage implementation."""
    
    @pytest.fixture
    def graph_storage(self) -> NetworkXGraphStorage:
        """Create NetworkX graph storage for testing."""
        return NetworkXGraphStorage()
    
    async def test_basic_node_operations(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test basic node operations."""
        node_id = uuid4()
        node = GraphNode(id=node_id, data={"name": "test_task"})
        
        # Test creation
        result = await graph_storage.add_node(node)
        assert result is True
        
        # Test retrieval
        retrieved = await graph_storage.get_node(node_id)
        assert retrieved == node
        
        # Test duplicate prevention
        result = await graph_storage.add_node(node)
        assert result is False
    
    async def test_basic_edge_operations(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test basic edge operations."""
        # Create nodes first
        node1_id, node2_id = uuid4(), uuid4()
        node1 = GraphNode(id=node1_id, data={"name": "task1"})
        node2 = GraphNode(id=node2_id, data={"name": "task2"})
        
        await graph_storage.add_node(node1)
        await graph_storage.add_node(node2)
        
        # Create edge
        edge = GraphEdge(from_id=node1_id, to_id=node2_id)
        result = await graph_storage.add_edge(edge)
        assert result is True
        
        # Test dependencies
        deps = await graph_storage.get_dependencies(node1_id)
        assert node2_id in deps
        
        dependents = await graph_storage.get_dependents(node2_id)
        assert node1_id in dependents
    
    async def test_cycle_prevention(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test that cycles are prevented."""
        # Create nodes
        node1_id, node2_id, node3_id = uuid4(), uuid4(), uuid4()
        
        for i, node_id in enumerate([node1_id, node2_id, node3_id], 1):
            node = GraphNode(id=node_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create chain: node1 -> node2 -> node3
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        await graph_storage.add_edge(GraphEdge(from_id=node2_id, to_id=node3_id))
        
        # Should not have cycles
        assert await graph_storage.has_cycle() is False
        
        # Try to create cycle: node3 -> node1
        cycle_edge = GraphEdge(from_id=node3_id, to_id=node1_id)
        result = await graph_storage.add_edge(cycle_edge)
        assert result is False  # Should be rejected
        
        # Graph should still be acyclic
        assert await graph_storage.has_cycle() is False
    
    async def test_topological_sort(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test topological sorting with NetworkX."""
        # Create nodes
        node1_id, node2_id, node3_id = uuid4(), uuid4(), uuid4()
        
        for i, node_id in enumerate([node1_id, node2_id, node3_id], 1):
            node = GraphNode(id=node_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create dependencies: node1 -> node2 -> node3
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        await graph_storage.add_edge(GraphEdge(from_id=node2_id, to_id=node3_id))
        
        # Get topological sort
        sorted_nodes = await graph_storage.topological_sort()
        assert len(sorted_nodes) == 3
        
        # Verify topological order (dependencies come after dependents)
        node1_idx = sorted_nodes.index(node1_id)
        node2_idx = sorted_nodes.index(node2_id)
        node3_idx = sorted_nodes.index(node3_id)
        
        # In topological order: dependencies come after their dependents
        assert node1_idx < node2_idx < node3_idx
    
    async def test_remove_node_removes_edges(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test that removing node also removes associated edges."""
        # Create nodes
        node1_id, node2_id, node3_id = uuid4(), uuid4(), uuid4()
        
        for i, node_id in enumerate([node1_id, node2_id, node3_id], 1):
            node = GraphNode(id=node_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create edges involving node2
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        await graph_storage.add_edge(GraphEdge(from_id=node2_id, to_id=node3_id))
        
        # Verify edges exist
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 2
        
        # Remove node2
        result = await graph_storage.remove_node(node2_id)
        assert result is True
        
        # All edges involving node2 should be removed
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 0
        
        # Node2 should not exist
        assert await graph_storage.get_node(node2_id) is None
    
    async def test_shortest_path(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test shortest path functionality."""
        # Create nodes
        node1_id, node2_id, node3_id, node4_id = [uuid4() for _ in range(4)]
        
        for i, node_id in enumerate([node1_id, node2_id, node3_id, node4_id], 1):
            node = GraphNode(id=node_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create path: node1 -> node2 -> node3 -> node4
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        await graph_storage.add_edge(GraphEdge(from_id=node2_id, to_id=node3_id))
        await graph_storage.add_edge(GraphEdge(from_id=node3_id, to_id=node4_id))
        
        # Also create direct path: node1 -> node4
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node4_id))
        
        # Shortest path should be direct: [node1_id, node4_id]
        path = await graph_storage.get_shortest_path(node1_id, node4_id)
        assert path == [node1_id, node4_id]
        
        # Path that doesn't exist
        path = await graph_storage.get_shortest_path(node4_id, node1_id)
        assert path is None
    
    async def test_descendants_and_ancestors(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test descendants and ancestors functionality."""
        # Create nodes
        node1_id, node2_id, node3_id, node4_id = [uuid4() for _ in range(4)]
        
        for i, node_id in enumerate([node1_id, node2_id, node3_id, node4_id], 1):
            node = GraphNode(id=node_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create tree: node1 -> node2, node1 -> node3, node2 -> node4
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node3_id))
        await graph_storage.add_edge(GraphEdge(from_id=node2_id, to_id=node4_id))
        
        # Test descendants (all nodes reachable from node1)
        descendants = await graph_storage.get_descendants(node1_id)
        assert set(descendants) == {node2_id, node3_id, node4_id}
        
        # Test ancestors (all nodes that can reach node4)
        ancestors = await graph_storage.get_ancestors(node4_id)
        assert set(ancestors) == {node1_id, node2_id}
    
    async def test_reachability(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test reachability checking."""
        # Create nodes
        node1_id, node2_id, node3_id = uuid4(), uuid4(), uuid4()
        
        for i, node_id in enumerate([node1_id, node2_id, node3_id], 1):
            node = GraphNode(id=node_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create path: node1 -> node2
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        
        # Test reachability
        assert await graph_storage.is_reachable(node1_id, node2_id) is True
        assert await graph_storage.is_reachable(node2_id, node1_id) is False
        assert await graph_storage.is_reachable(node1_id, node3_id) is False
    
    async def test_graph_metrics(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test graph metrics functionality."""
        # Test empty graph
        metrics = await graph_storage.get_graph_metrics()
        assert metrics["node_count"] == 0
        assert metrics["edge_count"] == 0
        assert metrics["is_dag"] is True
        
        # Add nodes and edges
        node1_id, node2_id, node3_id = uuid4(), uuid4(), uuid4()
        
        for i, node_id in enumerate([node1_id, node2_id, node3_id], 1):
            node = GraphNode(id=node_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        await graph_storage.add_edge(GraphEdge(from_id=node2_id, to_id=node3_id))
        
        # Test populated graph metrics
        metrics = await graph_storage.get_graph_metrics()
        assert metrics["node_count"] == 3
        assert metrics["edge_count"] == 2
        assert metrics["is_dag"] is True
        assert metrics["density"] > 0.0
        assert "strongly_connected_components" in metrics
        assert "weakly_connected_components" in metrics
    
    async def test_edge_with_custom_relationship(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test edges with custom relationship types."""
        # Create nodes
        node1_id, node2_id = uuid4(), uuid4()
        node1 = GraphNode(id=node1_id, data={"name": "task1"})
        node2 = GraphNode(id=node2_id, data={"name": "task2"})
        
        await graph_storage.add_node(node1)
        await graph_storage.add_node(node2)
        
        # Create edge with custom relationship
        edge = GraphEdge(
            from_id=node1_id, 
            to_id=node2_id, 
            relationship="blocks"
        )
        result = await graph_storage.add_edge(edge)
        assert result is True
        
        # Verify edge exists with correct relationship
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 1
        assert edges[0].relationship == "blocks"
        
        # Test removing specific edge by relationship
        result = await graph_storage.remove_edge(edge)
        assert result is True
        
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 0
    
    async def test_clear_graph(
        self, graph_storage: NetworkXGraphStorage
    ) -> None:
        """Test clearing entire graph."""
        # Add some content
        node1_id, node2_id = uuid4(), uuid4()
        node1 = GraphNode(id=node1_id, data={"name": "task1"})
        node2 = GraphNode(id=node2_id, data={"name": "task2"})
        
        await graph_storage.add_node(node1)
        await graph_storage.add_node(node2)
        await graph_storage.add_edge(GraphEdge(from_id=node1_id, to_id=node2_id))
        
        # Verify content exists
        nodes = await graph_storage.get_all_nodes()
        edges = await graph_storage.get_all_edges()
        assert len(nodes) == 2
        assert len(edges) == 1
        
        # Clear graph
        await graph_storage.clear()
        
        # Verify empty
        nodes = await graph_storage.get_all_nodes()
        edges = await graph_storage.get_all_edges()
        assert len(nodes) == 0
        assert len(edges) == 0
        
        metrics = await graph_storage.get_graph_metrics()
        assert metrics["node_count"] == 0
        assert metrics["edge_count"] == 0