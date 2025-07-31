"""Tests for DuckDB table storage implementation."""

import json
import pytest
from pathlib import Path
from uuid import uuid4

from src.models.task import Priority, Task, TaskStatus
from src.storage.duckdb_table import DuckDBTableStorage


class TestDuckDBTableStorage:
    """Test DuckDB table storage implementation."""
    
    @pytest.fixture
    def table_storage(self) -> DuckDBTableStorage:
        """Create DuckDB table storage for testing."""
        # Use in-memory database for tests
        return DuckDBTableStorage(Task, database_path=":memory:")
    
    async def test_basic_crud_operations(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test basic CRUD operations."""
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
        assert retrieved_task is not None
        assert retrieved_task.id == task.id
        assert retrieved_task.name == task.name
        
        # Test update
        task.name = "Updated Task"
        updated_task = await table_storage.update(task)
        assert updated_task.name == "Updated Task"
        
        # Verify update persisted
        retrieved_task = await table_storage.get_by_id(task.id)
        assert retrieved_task.name == "Updated Task"
        
        # Test deletion
        result = await table_storage.delete(task.id)
        assert result is True
        
        # Verify deletion
        retrieved_task = await table_storage.get_by_id(task.id)
        assert retrieved_task is None
    
    async def test_duplicate_creation_fails(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test that creating duplicate items fails."""
        task = Task(
            name="Test Task",
            description="A test task for storage testing",
            implementation_guide="Test implementation guide"
        )
        
        # Create task
        await table_storage.create(task)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await table_storage.create(task)
    
    async def test_update_nonexistent_fails(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test that updating non-existent item fails."""
        task = Task(
            name="Non-existent Task",
            description="This task doesn't exist",
            implementation_guide="Test implementation"
        )
        
        with pytest.raises(ValueError, match="doesn't exist"):
            await table_storage.update(task)
    
    async def test_list_all_items(
        self, table_storage: DuckDBTableStorage
    ) -> None:
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
    
    async def test_query_by_status(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test querying by task status."""
        # Create tasks with different statuses
        pending_task = Task(
            name="Pending Task",
            description="A pending task",
            implementation_guide="Implementation for pending task",
            status=TaskStatus.PENDING
        )
        in_progress_task = Task(
            name="In Progress Task",
            description="An in-progress task",
            implementation_guide="Implementation for in-progress task",
            status=TaskStatus.IN_PROGRESS
        )
        completed_task = Task(
            name="Completed Task",
            description="A completed task",
            implementation_guide="Implementation for completed task",
            status=TaskStatus.COMPLETED
        )
        
        await table_storage.create(pending_task)
        await table_storage.create(in_progress_task)
        await table_storage.create(completed_task)
        
        # Query by status
        pending_tasks = await table_storage.query({"status": TaskStatus.PENDING})
        assert len(pending_tasks) == 1
        assert pending_tasks[0].id == pending_task.id
        
        in_progress_tasks = await table_storage.query({"status": TaskStatus.IN_PROGRESS})
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0].id == in_progress_task.id
    
    async def test_query_by_priority(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test querying by task priority."""
        # Create tasks with different priorities
        p0_task = Task(
            name="P0 Task",
            description="Critical priority task",
            implementation_guide="Critical implementation",
            priority=Priority.P0
        )
        p1_task = Task(
            name="P1 Task", 
            description="High priority task",
            implementation_guide="High priority implementation",
            priority=Priority.P1
        )
        p2_task = Task(
            name="P2 Task",
            description="Medium priority task",
            implementation_guide="Medium priority implementation",
            priority=Priority.P2
        )
        
        await table_storage.create(p0_task)
        await table_storage.create(p1_task)
        await table_storage.create(p2_task)
        
        # Query by priority
        p0_tasks = await table_storage.query({"priority": Priority.P0})
        assert len(p0_tasks) == 1
        assert p0_tasks[0].id == p0_task.id
        
        p1_tasks = await table_storage.query({"priority": Priority.P1})
        assert len(p1_tasks) == 1
        assert p1_tasks[0].id == p1_task.id
    
    async def test_query_multiple_filters(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test querying with multiple filters."""
        # Create tasks with different combinations
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
        
        # Query with multiple filters
        pending_p1_tasks = await table_storage.query({
            "status": TaskStatus.PENDING,
            "priority": Priority.P1
        })
        assert len(pending_p1_tasks) == 1
        assert pending_p1_tasks[0].id == task1.id
    
    async def test_count_operations(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test counting operations."""
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
    
    async def test_exists_operation(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test exists operation."""
        task = Task(
            name="Test Task",
            description="A test task for existence checking",
            implementation_guide="Test implementation"
        )
        
        # Initially doesn't exist
        assert await table_storage.exists(task.id) is False
        
        # Create task
        await table_storage.create(task)
        assert await table_storage.exists(task.id) is True
        
        # Delete task
        await table_storage.delete(task.id)
        assert await table_storage.exists(task.id) is False
    
    async def test_clear_storage(
        self, table_storage: DuckDBTableStorage
    ) -> None:
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
    
    async def test_bulk_insert(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test bulk insert functionality."""
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = Task(
                name=f"Bulk Task {i}",
                description=f"Bulk description {i}",
                implementation_guide=f"Bulk implementation {i}"
            )
            tasks.append(task)
        
        # Bulk insert
        result = await table_storage.bulk_insert(tasks)
        assert len(result) == 5
        
        # Verify all tasks were inserted
        assert await table_storage.count() == 5
        
        all_tasks = await table_storage.list_all()
        all_ids = {task.id for task in all_tasks}
        expected_ids = {task.id for task in tasks}
        assert all_ids == expected_ids
    
    async def test_bulk_insert_with_duplicate_fails(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test that bulk insert fails if any item already exists."""
        # Create a task
        existing_task = Task(
            name="Existing Task",
            description="Already exists",
            implementation_guide="Existing implementation"
        )
        await table_storage.create(existing_task)
        
        # Try to bulk insert including the existing task
        new_task = Task(
            name="New Task",
            description="Brand new task",
            implementation_guide="New implementation"
        )
        
        with pytest.raises(ValueError, match="already exists"):
            await table_storage.bulk_insert([existing_task, new_task])
    
    async def test_get_statistics(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test getting table statistics."""
        # Initially empty
        stats = await table_storage.get_statistics()
        assert stats["total_count"] == 0
        assert stats["earliest_created"] is None
        
        # Add some tasks
        for i in range(3):
            task = Task(
                name=f"Stats Task {i}",
                description=f"Stats description {i}",
                implementation_guide=f"Stats implementation {i}"
            )
            await table_storage.create(task)
        
        # Check statistics
        stats = await table_storage.get_statistics()
        assert stats["total_count"] == 3
        assert stats["earliest_created"] is not None
        assert stats["latest_created"] is not None
        assert stats["latest_updated"] is not None
    
    async def test_query_empty_filters(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test querying with empty filters returns all items."""
        # Create some tasks
        for i in range(3):
            task = Task(
                name=f"Empty Filter Task {i}",
                description=f"Description {i}",
                implementation_guide=f"Implementation {i}"
            )
            await table_storage.create(task)
        
        # Query with empty filters
        all_tasks = await table_storage.query({})
        assert len(all_tasks) == 3
    
    async def test_custom_table_name(self) -> None:
        """Test creating storage with custom table name."""
        custom_storage = DuckDBTableStorage(
            Task, 
            database_path=":memory:",
            table_name="custom_tasks"
        )
        
        # Should work normally
        task = Task(
            name="Custom Table Task",
            description="Task in custom table",
            implementation_guide="Custom implementation"
        )
        
        await custom_storage.create(task)
        retrieved = await custom_storage.get_by_id(task.id)
        assert retrieved is not None
        assert retrieved.name == "Custom Table Task"
        
        custom_storage.close()
    
    async def test_connection_cleanup(
        self, table_storage: DuckDBTableStorage
    ) -> None:
        """Test that connections are properly cleaned up."""
        # Create and use storage
        task = Task(
            name="Cleanup Task",
            description="Task for cleanup testing",
            implementation_guide="Cleanup implementation"
        )
        
        await table_storage.create(task)
        assert await table_storage.exists(task.id) is True
        
        # Manually close connection
        table_storage.close()
        
        # Further operations should handle closed connection gracefully
        # (In a real implementation, you might want to reconnect automatically)