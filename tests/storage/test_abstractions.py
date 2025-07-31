"""Comprehensive tests for abstract storage interfaces."""

import pytest
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.models.task import GraphEdge, GraphNode, Task
from src.storage.abstractions import AbstractGraphStorage, AbstractTableStorage


class MockGraphStorage(AbstractGraphStorage):
    """Mock implementation of graph storage for testing."""
    
    def __init__(self) -> None:
        self.nodes: Dict[UUID, GraphNode] = {}
        self.edges: List[GraphEdge] = []
    
    async def add_node(self, node: GraphNode) -> bool:
        """Add node to mock graph storage."""
        if node.id in self.nodes:
            return False
        self.nodes[node.id] = node
        return True
    
    async def add_edge(self, edge: GraphEdge) -> bool:
        """Add edge to mock graph storage."""
        # Check if would create cycle (simple implementation)
        if await self._would_create_cycle(edge):
            return False
        self.edges.append(edge)
        return True
    
    async def get_node(self, node_id: UUID) -> Optional[GraphNode]:
        """Get node from mock graph storage."""
        return self.nodes.get(node_id)
    
    async def remove_node(self, node_id: UUID) -> bool:
        """Remove node and associated edges."""
        if node_id not in self.nodes:
            return False
        
        # Remove the node
        del self.nodes[node_id]
        
        # Remove all edges involving this node
        self.edges = [
            edge for edge in self.edges
            if edge.from_id != node_id and edge.to_id != node_id
        ]
        return True
    
    async def remove_edge(self, edge: GraphEdge) -> bool:
        """Remove specific edge."""
        for i, existing_edge in enumerate(self.edges):
            if (existing_edge.from_id == edge.from_id and 
                existing_edge.to_id == edge.to_id and
                existing_edge.relationship == edge.relationship):
                del self.edges[i]
                return True
        return False
    
    async def get_dependencies(self, node_id: UUID) -> List[UUID]:
        """Get nodes this node depends on."""
        dependencies = []
        for edge in self.edges:
            if edge.from_id == node_id:
                dependencies.append(edge.to_id)
        return dependencies
    
    async def get_dependents(self, node_id: UUID) -> List[UUID]:
        """Get nodes that depend on this node."""
        dependents = []
        for edge in self.edges:
            if edge.to_id == node_id:
                dependents.append(edge.from_id)
        return dependents
    
    async def has_cycle(self) -> bool:
        """Check if graph has cycles."""
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        async def has_cycle_util(node_id: UUID) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            dependencies = await self.get_dependencies(node_id)
            for dep_id in dependencies:
                if dep_id not in visited:
                    if await has_cycle_util(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if await has_cycle_util(node_id):
                    return True
        
        return False
    
    async def topological_sort(self) -> List[UUID]:
        """Return topologically sorted nodes."""
        if await self.has_cycle():
            raise ValueError("Graph contains cycles")
        
        # Use Kahn's algorithm for topological sorting
        # Count in-degrees (number of dependencies for each node)
        in_degrees = {node_id: 0 for node_id in self.nodes}
        
        for edge in self.edges:
            in_degrees[edge.from_id] += 1  # from_id depends on to_id
        
        # Start with nodes that have no dependencies
        queue = [node_id for node_id, degree in in_degrees.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # Get nodes that depend on this node
            dependents = await self.get_dependents(node_id)
            for dependent_id in dependents:
                in_degrees[dependent_id] -= 1
                if in_degrees[dependent_id] == 0:
                    queue.append(dependent_id)
        
        return result
    
    async def get_all_nodes(self) -> List[GraphNode]:
        """Get all nodes."""
        return list(self.nodes.values())
    
    async def get_all_edges(self) -> List[GraphEdge]:
        """Get all edges."""
        return self.edges.copy()
    
    async def clear(self) -> None:
        """Clear all nodes and edges."""
        self.nodes.clear()
        self.edges.clear()
    
    async def _would_create_cycle(self, new_edge: GraphEdge) -> bool:
        """Check if adding edge would create cycle."""
        # Temporarily add edge and check for cycles
        self.edges.append(new_edge)
        has_cycle = await self.has_cycle()
        self.edges.pop()  # Remove the temporary edge
        return has_cycle


class MockTableStorage(AbstractTableStorage[Task]):
    """Mock implementation of table storage for testing."""
    
    def __init__(self) -> None:
        super().__init__(Task)
        self.items: Dict[UUID, Task] = {}
    
    async def create(self, item: Task) -> Task:
        """Create item in mock table storage."""
        if item.id in self.items:
            raise ValueError(f"Item with ID {item.id} already exists")
        self.items[item.id] = item
        return item
    
    async def get_by_id(self, item_id: UUID) -> Optional[Task]:
        """Get item by ID."""
        return self.items.get(item_id)
    
    async def list_all(self) -> List[Task]:
        """List all items."""
        return list(self.items.values())
    
    async def update(self, item: Task) -> Task:
        """Update existing item."""
        if item.id not in self.items:
            raise ValueError(f"Item with ID {item.id} doesn't exist")
        self.items[item.id] = item
        return item
    
    async def delete(self, item_id: UUID) -> bool:
        """Delete item by ID."""
        if item_id not in self.items:
            return False
        del self.items[item_id]
        return True
    
    async def query(self, filters: Dict[str, Any]) -> List[Task]:
        """Query items with filters."""
        results = []
        for item in self.items.values():
            match = True
            for field, value in filters.items():
                if not hasattr(item, field) or getattr(item, field) != value:
                    match = False
                    break
            if match:
                results.append(item)
        return results
    
    async def count(self) -> int:
        """Get count of items."""
        return len(self.items)
    
    async def exists(self, item_id: UUID) -> bool:
        """Check if item exists."""
        return item_id in self.items
    
    async def clear(self) -> None:
        """Clear all items."""
        self.items.clear()


class TestAbstractGraphStorage:
    """Test abstract graph storage interface compliance."""
    
    @pytest.fixture
    def graph_storage(self) -> MockGraphStorage:
        """Create mock graph storage for testing."""
        return MockGraphStorage()
    
    async def test_node_creation_and_retrieval(
        self, graph_storage: MockGraphStorage
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
    
    async def test_node_removal(self, graph_storage: MockGraphStorage) -> None:
        """Test node removal."""
        node_id = uuid4()
        node = GraphNode(id=node_id, data={"name": "test_task"})
        
        # Add node
        await graph_storage.add_node(node)
        assert await graph_storage.get_node(node_id) is not None
        
        # Remove node
        result = await graph_storage.remove_node(node_id)
        assert result is True
        assert await graph_storage.get_node(node_id) is None
        
        # Try to remove non-existent node
        result = await graph_storage.remove_node(node_id)
        assert result is False
    
    async def test_edge_creation_and_removal(
        self, graph_storage: MockGraphStorage
    ) -> None:
        """Test edge operations."""
        # Create nodes
        node1_id, node2_id = uuid4(), uuid4()
        node1 = GraphNode(id=node1_id, data={"name": "task1"})
        node2 = GraphNode(id=node2_id, data={"name": "task2"})
        
        await graph_storage.add_node(node1)
        await graph_storage.add_node(node2)
        
        # Create edge: node1 depends on node2
        edge = GraphEdge(from_id=node1_id, to_id=node2_id)
        result = await graph_storage.add_edge(edge)
        assert result is True
        
        # Verify edge exists
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 1
        assert edges[0] == edge
        
        # Remove edge
        result = await graph_storage.remove_edge(edge)
        assert result is True
        
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 0
    
    async def test_dependency_queries(
        self, graph_storage: MockGraphStorage
    ) -> None:
        """Test dependency relationship queries."""
        # Create nodes
        task1_id, task2_id, task3_id = uuid4(), uuid4(), uuid4()
        
        for i, task_id in enumerate([task1_id, task2_id, task3_id], 1):
            node = GraphNode(id=task_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create dependencies: task3 -> task2 -> task1
        edge1 = GraphEdge(from_id=task2_id, to_id=task1_id)
        edge2 = GraphEdge(from_id=task3_id, to_id=task2_id)
        
        await graph_storage.add_edge(edge1)
        await graph_storage.add_edge(edge2)
        
        # Test dependency queries
        task2_deps = await graph_storage.get_dependencies(task2_id)
        assert task1_id in task2_deps
        assert len(task2_deps) == 1
        
        task3_deps = await graph_storage.get_dependencies(task3_id)
        assert task2_id in task3_deps
        assert len(task3_deps) == 1
        
        # Test dependent queries
        task1_dependents = await graph_storage.get_dependents(task1_id)
        assert task2_id in task1_dependents
        assert len(task1_dependents) == 1
        
        task2_dependents = await graph_storage.get_dependents(task2_id)
        assert task3_id in task2_dependents
        assert len(task2_dependents) == 1
    
    async def test_cycle_detection(
        self, graph_storage: MockGraphStorage
    ) -> None:
        """Test cycle detection."""
        # Create nodes
        task1_id, task2_id, task3_id = uuid4(), uuid4(), uuid4()
        
        for i, task_id in enumerate([task1_id, task2_id, task3_id], 1):
            node = GraphNode(id=task_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create acyclic dependencies: task3 -> task2 -> task1
        await graph_storage.add_edge(GraphEdge(from_id=task2_id, to_id=task1_id))
        await graph_storage.add_edge(GraphEdge(from_id=task3_id, to_id=task2_id))
        
        # Should not have cycles
        assert await graph_storage.has_cycle() is False
        
        # Try to create cycle: task1 -> task3 (would create cycle)
        cycle_edge = GraphEdge(from_id=task1_id, to_id=task3_id)
        result = await graph_storage.add_edge(cycle_edge)
        assert result is False  # Should be rejected
        
        # Graph should still be acyclic
        assert await graph_storage.has_cycle() is False
    
    async def test_topological_sort(
        self, graph_storage: MockGraphStorage
    ) -> None:
        """Test topological sorting."""
        # Create nodes
        task1_id, task2_id, task3_id = uuid4(), uuid4(), uuid4()
        
        for i, task_id in enumerate([task1_id, task2_id, task3_id], 1):
            node = GraphNode(id=task_id, data={"name": f"task{i}"})
            await graph_storage.add_node(node)
        
        # Create dependencies: task2 depends on task1, task3 depends on task2
        # In graph: task3 -> task2 -> task1 (from_id depends on to_id)
        await graph_storage.add_edge(GraphEdge(from_id=task2_id, to_id=task1_id))
        await graph_storage.add_edge(GraphEdge(from_id=task3_id, to_id=task2_id))
        
        # Get topological sort
        sorted_nodes = await graph_storage.topological_sort()
        
        # In topological order: dependencies come before dependents
        # task1 should come before task2, task2 before task3
        task1_idx = sorted_nodes.index(task1_id)
        task2_idx = sorted_nodes.index(task2_id)  
        task3_idx = sorted_nodes.index(task3_id)
        
        # Dependencies must come before their dependents in topological order
        assert task1_idx < task2_idx < task3_idx
    
    async def test_node_removal_removes_edges(
        self, graph_storage: MockGraphStorage
    ) -> None:
        """Test that removing node also removes associated edges."""
        # Create nodes
        task1_id, task2_id = uuid4(), uuid4()
        node1 = GraphNode(id=task1_id, data={"name": "task1"})
        node2 = GraphNode(id=task2_id, data={"name": "task2"})
        
        await graph_storage.add_node(node1)
        await graph_storage.add_node(node2)
        
        # Create edge
        edge = GraphEdge(from_id=task2_id, to_id=task1_id)
        await graph_storage.add_edge(edge)
        
        # Verify edge exists
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 1
        
        # Remove node1
        await graph_storage.remove_node(task1_id)
        
        # Edge should be removed too
        edges = await graph_storage.get_all_edges()
        assert len(edges) == 0
    
    async def test_clear_graph(self, graph_storage: MockGraphStorage) -> None:
        """Test clearing entire graph."""
        # Add some nodes and edges
        task1_id, task2_id = uuid4(), uuid4()
        node1 = GraphNode(id=task1_id, data={"name": "task1"})
        node2 = GraphNode(id=task2_id, data={"name": "task2"})
        
        await graph_storage.add_node(node1)
        await graph_storage.add_node(node2)
        await graph_storage.add_edge(GraphEdge(from_id=task2_id, to_id=task1_id))
        
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


class TestAbstractTableStorage:
    """Test abstract table storage interface compliance."""
    
    @pytest.fixture
    def table_storage(self) -> MockTableStorage:
        """Create mock table storage for testing."""
        return MockTableStorage()
    
    async def test_item_creation_and_retrieval(
        self, table_storage: MockTableStorage
    ) -> None:
        """Test basic item operations."""
        task = Task(
            name="Test Task",
            description="A test task for storage testing",
            implementation_guide="Test implementation guide"
        )
        
        # Test creation
        created_task = await table_storage.create(task)
        assert created_task == task
        
        # Test retrieval
        retrieved_task = await table_storage.get_by_id(task.id)
        assert retrieved_task == task
        
        # Test duplicate creation fails
        with pytest.raises(ValueError, match="already exists"):
            await table_storage.create(task)
    
    async def test_item_update(self, table_storage: MockTableStorage) -> None:
        """Test item updates."""
        task = Task(
            name="Test Task",
            description="A test task for storage testing",
            implementation_guide="Test implementation guide"
        )
        
        # Create task
        await table_storage.create(task)
        
        # Update task
        task.name = "Updated Task"
        updated_task = await table_storage.update(task)
        assert updated_task.name == "Updated Task"
        
        # Verify update persisted
        retrieved_task = await table_storage.get_by_id(task.id)
        assert retrieved_task.name == "Updated Task"
        
        # Try to update non-existent task
        new_task = Task(
            name="New Task",
            description="A new task",
            implementation_guide="New implementation"
        )
        
        with pytest.raises(ValueError, match="doesn't exist"):
            await table_storage.update(new_task)
    
    async def test_item_deletion(self, table_storage: MockTableStorage) -> None:
        """Test item deletion."""
        task = Task(
            name="Test Task",
            description="A test task for storage testing",
            implementation_guide="Test implementation guide"
        )
        
        # Create task
        await table_storage.create(task)
        assert await table_storage.exists(task.id) is True
        
        # Delete task
        result = await table_storage.delete(task.id)
        assert result is True
        assert await table_storage.exists(task.id) is False
        
        # Try to delete non-existent task
        result = await table_storage.delete(task.id)
        assert result is False
    
    async def test_list_all_items(self, table_storage: MockTableStorage) -> None:
        """Test listing all items."""
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = Task(
                name=f"Task {i}",
                description=f"Description for task {i}",
                implementation_guide=f"Implementation guide {i}"
            )
            tasks.append(task)
            await table_storage.create(task)
        
        # List all items
        all_items = await table_storage.list_all()
        assert len(all_items) == 3
        
        # Verify all tasks are present
        all_ids = {item.id for item in all_items}
        expected_ids = {task.id for task in tasks}
        assert all_ids == expected_ids
    
    async def test_query_items(self, table_storage: MockTableStorage) -> None:
        """Test querying items with filters."""
        # Create tasks with different statuses
        from src.models.task import TaskStatus, Priority
        
        task1 = Task(
            name="Task 1",
            description="First task",
            implementation_guide="Implementation 1",
            status=TaskStatus.PENDING,
            priority=Priority.P1
        )
        task2 = Task(
            name="Task 2", 
            description="Second task",
            implementation_guide="Implementation 2",
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.P1
        )
        task3 = Task(
            name="Task 3",
            description="Third task", 
            implementation_guide="Implementation 3",
            status=TaskStatus.PENDING,
            priority=Priority.P2
        )
        
        await table_storage.create(task1)
        await table_storage.create(task2)
        await table_storage.create(task3)
        
        # Query by status
        pending_tasks = await table_storage.query({"status": TaskStatus.PENDING})
        assert len(pending_tasks) == 2
        
        # Query by priority
        p1_tasks = await table_storage.query({"priority": Priority.P1})
        assert len(p1_tasks) == 2
        
        # Query by multiple filters
        pending_p1_tasks = await table_storage.query({
            "status": TaskStatus.PENDING,
            "priority": Priority.P1
        })
        assert len(pending_p1_tasks) == 1
        assert pending_p1_tasks[0].id == task1.id
    
    async def test_count_items(self, table_storage: MockTableStorage) -> None:
        """Test counting items."""
        # Initially empty
        assert await table_storage.count() == 0
        
        # Add some tasks
        for i in range(5):
            task = Task(
                name=f"Task {i}",
                description=f"Description {i}",
                implementation_guide=f"Implementation {i}"
            )
            await table_storage.create(task)
        
        # Check count
        assert await table_storage.count() == 5
        
        # Delete one task
        tasks = await table_storage.list_all()
        await table_storage.delete(tasks[0].id)
        
        assert await table_storage.count() == 4
    
    async def test_clear_storage(self, table_storage: MockTableStorage) -> None:
        """Test clearing all items."""
        # Add some tasks
        for i in range(3):
            task = Task(
                name=f"Task {i}",
                description=f"Description {i}",
                implementation_guide=f"Implementation {i}"
            )
            await table_storage.create(task)
        
        # Verify items exist
        assert await table_storage.count() == 3
        
        # Clear storage
        await table_storage.clear()
        
        # Verify empty
        assert await table_storage.count() == 0
        all_items = await table_storage.list_all()
        assert len(all_items) == 0
    
    async def test_model_class_property(
        self, table_storage: MockTableStorage
    ) -> None:
        """Test that storage maintains model class reference."""
        assert table_storage.model_class == Task