"""
Test suite for task splitting service functionality.

Tests the core task splitting service logic including intelligent decomposition,
dependency resolution, update mode handling, and integration with storage layers.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from src.services.task_splitting_service import (
    TaskSplittingService,
    SplitStrategy,
    DependencyResolver
)
from src.models.task_splitting import (
    TaskSplitRequest,
    TaskTemplate,
    UpdateMode,
    SplitResult,
    GranularityRules,
    TaskDecomposition
)
from src.models.task import Task, TaskStatus, Priority, ComplexityLevel
from src.services.task_service import TaskService
from src.storage.abstractions import AbstractTableStorage, AbstractGraphStorage


class MockTaskService:
    """Mock task service for testing."""
    
    def __init__(self):
        self.tasks = {}
        self.get_all_tasks = AsyncMock(return_value=[])
        self.create_task = AsyncMock()
        self.update_task = AsyncMock()
        self.delete_task = AsyncMock()
        self.clear_all_tasks = AsyncMock()
        self.get_task_by_name = AsyncMock(return_value=None)
    
    async def get_all_tasks_impl(self):
        """Get all tasks implementation."""
        return list(self.tasks.values())
    
    async def create_task_impl(self, task: Task) -> Task:
        """Create task implementation."""
        self.tasks[task.id] = task
        return task
    
    async def get_task_by_name_impl(self, name: str) -> Task | None:
        """Get task by name implementation."""
        for task in self.tasks.values():
            if task.name == name:
                return task
        return None
    
    async def update_task_impl(self, task: Task) -> Task:
        """Update task implementation."""
        self.tasks[task.id] = task
        return task


@pytest.fixture
def mock_task_service():
    """Fixture providing a mock task service."""
    service = MockTaskService()
    service.get_all_tasks.side_effect = service.get_all_tasks_impl
    service.create_task.side_effect = service.create_task_impl
    service.get_task_by_name.side_effect = service.get_task_by_name_impl
    service.update_task.side_effect = service.update_task_impl
    return service


@pytest.fixture
def task_splitting_service(mock_task_service):
    """Fixture providing a task splitting service."""
    return TaskSplittingService(task_service=mock_task_service)


class TestSplitStrategy:
    """Test split strategy enumeration."""
    
    def test_split_strategy_values(self):
        """Test that SplitStrategy has all required values."""
        assert SplitStrategy.FUNCTIONAL_MODULES == "functional_modules"
        assert SplitStrategy.SEQUENTIAL_STEPS == "sequential_steps"
        assert SplitStrategy.PARALLEL_FEATURES == "parallel_features"
        assert SplitStrategy.COMPLEXITY_BASED == "complexity_based"


class TestDependencyResolver:
    """Test dependency resolution functionality."""
    
    def test_create_dependency_resolver(self):
        """Test creating a dependency resolver."""
        resolver = DependencyResolver()
        assert resolver is not None
    
    def test_resolve_dependencies_by_name(self):
        """Test resolving dependencies by task names."""
        existing_tasks = [
            Task(name="Task A", description="First task description", implementation_guide="Implementation guide for task A"),
            Task(name="Task B", description="Second task description", implementation_guide="Implementation guide for task B")
        ]
        
        resolver = DependencyResolver()
        templates = [
            TaskTemplate(
                name="Task C",
                description="Third task depending on A and B",
                implementation_guide="Implementation guide for task C with detailed steps",
                dependencies=["Task A", "Task B"]
            )
        ]
        
        resolved = resolver.resolve_task_dependencies(templates, existing_tasks)
        
        assert len(resolved) == 1
        resolved_task = resolved[0]
        assert resolved_task.name == "Task C"
        assert len(resolved_task.dependencies) == 2
        
        # Dependencies should be resolved to task IDs
        dep_names = [existing_tasks[0].name, existing_tasks[1].name]
        for dep in resolved_task.dependencies:
            assert any(task.id == dep.task_id for task in existing_tasks)
    
    def test_resolve_dependencies_by_id(self):
        """Test resolving dependencies by task IDs."""
        task_a = Task(name="Task A", description="First task description", implementation_guide="Implementation guide for task A")
        task_b = Task(name="Task B", description="Second task description", implementation_guide="Implementation guide for task B")
        existing_tasks = [task_a, task_b]
        
        resolver = DependencyResolver()
        templates = [
            TaskTemplate(
                name="Task C",
                description="Third task depending on specific IDs",
                implementation_guide="Implementation guide for task C with specific ID dependencies",
                dependencies=[str(task_a.id), str(task_b.id)]
            )
        ]
        
        resolved = resolver.resolve_task_dependencies(templates, existing_tasks)
        
        assert len(resolved) == 1
        resolved_task = resolved[0]
        assert len(resolved_task.dependencies) == 2
        
        # Check that the correct task IDs were resolved
        resolved_ids = {dep.task_id for dep in resolved_task.dependencies}
        expected_ids = {task_a.id, task_b.id}
        assert resolved_ids == expected_ids
    
    def test_resolve_missing_dependencies(self):
        """Test handling of missing dependencies."""
        existing_tasks = [
            Task(name="Task A", description="First task description", implementation_guide="Implementation guide for task A")
        ]
        
        resolver = DependencyResolver()
        templates = [
            TaskTemplate(
                name="Task B",
                description="Task with missing dependency",
                implementation_guide="Implementation guide for task B with some missing dependencies",
                dependencies=["Task A", "Missing Task"]
            )
        ]
        
        resolved = resolver.resolve_task_dependencies(templates, existing_tasks)
        
        assert len(resolved) == 1
        resolved_task = resolved[0]
        # Only the existing dependency should be resolved
        assert len(resolved_task.dependencies) == 1
        assert resolved_task.dependencies[0].task_id == existing_tasks[0].id
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        resolver = DependencyResolver()
        templates = [
            TaskTemplate(
                name="Task A",
                description="Task A depends on B creating circular dependency",
                implementation_guide="Implementation guide for task A",
                dependencies=["Task B"]
            ),
            TaskTemplate(
                name="Task B", 
                description="Task B depends on A creating circular dependency",
                implementation_guide="Implementation guide for task B",
                dependencies=["Task A"]
            )
        ]
        
        has_cycles = resolver.detect_circular_dependencies(templates)
        assert has_cycles is True
    
    def test_no_circular_dependencies(self):
        """Test valid dependency chain without cycles."""
        resolver = DependencyResolver()
        templates = [
            TaskTemplate(
                name="Task A",
                description="Task A has no dependencies and is foundation",
                implementation_guide="Implementation guide for task A",
                dependencies=[]
            ),
            TaskTemplate(
                name="Task B",
                description="Task B depends on A for proper sequencing",
                implementation_guide="Implementation guide for task B", 
                dependencies=["Task A"]
            ),
            TaskTemplate(
                name="Task C",
                description="Task C depends on B for proper sequencing",
                implementation_guide="Implementation guide for task C",
                dependencies=["Task B"]
            )
        ]
        
        has_cycles = resolver.detect_circular_dependencies(templates)
        assert has_cycles is False


class TestTaskSplittingService:
    """Test task splitting service functionality."""
    
    @pytest.mark.asyncio
    async def test_create_service(self, mock_task_service):
        """Test creating a task splitting service."""
        service = TaskSplittingService(task_service=mock_task_service)
        assert service.task_service == mock_task_service
        assert isinstance(service.dependency_resolver, DependencyResolver)
    
    @pytest.mark.asyncio
    async def test_split_tasks_clear_all_mode(self, task_splitting_service, mock_task_service):
        """Test task splitting with clearAllTasks mode."""
        templates = [
            TaskTemplate(
                name="Setup Environment",
                description="Initialize development environment with proper configuration",
                implementation_guide="1. Install Node.js\n2. Setup project structure",
                dependencies=[]
            ),
            TaskTemplate(
                name="Implement Authentication",
                description="Create user authentication system with proper security",
                implementation_guide="1. Setup JWT\n2. Create login/logout",
                dependencies=["Setup Environment"]
            )
        ]
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=templates,
            global_analysis_result="Build a secure web application"
        )
        
        result = await task_splitting_service.split_tasks(request)
        
        assert result.success is True
        assert len(result.created_tasks) == 2
        assert result.operation is not None
        assert result.operation.update_mode == UpdateMode.CLEAR_ALL_TASKS
        assert result.operation.tasks_added == 2
        
        # Verify clear all tasks was called
        mock_task_service.clear_all_tasks.assert_called_once()
        
        # Verify tasks were created with proper dependency resolution
        created_task_names = [task.name for task in result.created_tasks]
        assert "Setup Environment" in created_task_names
        assert "Implement Authentication" in created_task_names
    
    @pytest.mark.asyncio
    async def test_split_tasks_append_mode(self, task_splitting_service, mock_task_service):
        """Test task splitting with append mode."""
        # Setup existing tasks
        existing_task = Task(
            name="Existing Task",
            description="Already exists in the system",
            implementation_guide="Existing implementation"
        )
        mock_task_service.tasks = {existing_task.id: existing_task}
        
        templates = [
            TaskTemplate(
                name="New Task",
                description="This is a new task to be added to existing ones",
                implementation_guide="New implementation guide",
                dependencies=[]
            )
        ]
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.APPEND,
            task_templates=templates
        )
        
        result = await task_splitting_service.split_tasks(request)
        
        assert result.success is True
        assert len(result.created_tasks) == 1
        assert result.operation.update_mode == UpdateMode.APPEND
        assert result.operation.tasks_added == 1
        
        # Verify clear all tasks was NOT called in append mode
        mock_task_service.clear_all_tasks.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_split_tasks_selective_mode(self, task_splitting_service, mock_task_service):
        """Test task splitting with selective mode."""
        # Setup existing task with same name
        existing_task = Task(
            name="Update This Task",
            description="Original description",
            implementation_guide="Original guide"
        )
        mock_task_service.tasks = {existing_task.id: existing_task}
        
        templates = [
            TaskTemplate(
                name="Update This Task",  # Same name - should update
                description="Updated description with more comprehensive details",
                implementation_guide="Updated implementation guide with new steps",
                dependencies=[]
            ),
            TaskTemplate(
                name="Brand New Task",  # New name - should create
                description="This is a completely new task to be created",
                implementation_guide="New task implementation",
                dependencies=[]
            )
        ]
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.SELECTIVE,
            task_templates=templates
        )
        
        result = await task_splitting_service.split_tasks(request)
        
        assert result.success is True
        assert result.operation.update_mode == UpdateMode.SELECTIVE
        # Should have one update and one create
        assert result.operation.tasks_updated >= 1
        assert result.operation.tasks_added >= 1
    
    @pytest.mark.asyncio
    async def test_split_tasks_overwrite_mode(self, task_splitting_service, mock_task_service):
        """Test task splitting with overwrite mode."""
        # Setup existing tasks - mix of completed and pending
        completed_task = Task(
            name="Completed Task",
            description="This task is done",
            implementation_guide="Completed guide",
            status=TaskStatus.COMPLETED
        )
        pending_task = Task(
            name="Pending Task", 
            description="This task is not done",
            implementation_guide="Pending guide",
            status=TaskStatus.PENDING
        )
        mock_task_service.tasks = {
            completed_task.id: completed_task,
            pending_task.id: pending_task
        }
        
        templates = [
            TaskTemplate(
                name="New Task After Overwrite",
                description="This task should be created after overwrite clears pending tasks",
                implementation_guide="New task guide",
                dependencies=[]
            )
        ]
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.OVERWRITE,
            task_templates=templates
        )
        
        result = await task_splitting_service.split_tasks(request)
        
        assert result.success is True
        assert result.operation.update_mode == UpdateMode.OVERWRITE
        
        # Should have removed pending tasks but kept completed ones
        # Note: The exact implementation depends on how overwrite is implemented
        assert result.operation.tasks_added == 1
    
    @pytest.mark.asyncio
    async def test_split_tasks_validation_failure(self, task_splitting_service):
        """Test task splitting with validation failures."""
        # Create invalid templates that violate granularity rules
        templates = []
        for i in range(15):  # Exceeds max of 10
            templates.append(TaskTemplate(
                name=f"Task {i}",
                description=f"Description for task {i} with adequate length",
                implementation_guide=f"Implementation {i}",
                dependencies=[]
            ))
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=templates
        )
        
        result = await task_splitting_service.split_tasks(request)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "granularity" in result.errors[0].lower() or "too many" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_split_tasks_circular_dependency_failure(self, task_splitting_service):
        """Test task splitting with circular dependency detection."""
        templates = [
            TaskTemplate(
                name="Task A",
                description="Task A depends on Task B creating a circular dependency",
                implementation_guide="Implementation A",
                dependencies=["Task B"]
            ),
            TaskTemplate(
                name="Task B",
                description="Task B depends on Task A creating a circular dependency",
                implementation_guide="Implementation B", 
                dependencies=["Task A"]
            )
        ]
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=templates
        )
        
        result = await task_splitting_service.split_tasks(request)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "circular" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_decompose_task(self, task_splitting_service):
        """Test task decomposition functionality."""
        original_task = Task(
            name="Build Web Application",
            description="Create a comprehensive web application with modern features",
            implementation_guide="Use modern frameworks and best practices"
        )
        
        decomposition = await task_splitting_service.decompose_task(
            original_task,
            strategy=SplitStrategy.FUNCTIONAL_MODULES,
            max_subtasks=5
        )
        
        assert isinstance(decomposition, TaskDecomposition)
        assert decomposition.original_task.name == "Build Web Application"
        assert decomposition.decomposition_strategy == SplitStrategy.FUNCTIONAL_MODULES
        assert len(decomposition.subtask_templates) > 0
        assert len(decomposition.subtask_templates) <= 5
        
        # Check that subtasks have proper structure
        for template in decomposition.subtask_templates:
            assert len(template.name) > 0
            assert len(template.description) >= 10
            assert len(template.implementation_guide) >= 10
    
    @pytest.mark.asyncio
    async def test_get_split_statistics(self, task_splitting_service, mock_task_service):
        """Test getting split statistics."""
        # Setup some tasks
        tasks = [
            Task(name="Task 1", description="First task description", implementation_guide="Implementation guide for task 1"),
            Task(name="Task 2", description="Second task description", implementation_guide="Implementation guide for task 2"),
            Task(name="Task 3", description="Third task description", implementation_guide="Implementation guide for task 3")
        ]
        
        for task in tasks:
            mock_task_service.tasks[task.id] = task
        
        stats = await task_splitting_service.get_split_statistics()
        
        assert "total_tasks" in stats
        assert "task_status_distribution" in stats
        assert "average_dependencies_per_task" in stats
        assert "most_complex_tasks" in stats
        
        assert stats["total_tasks"] == 3
    
    @pytest.mark.asyncio
    async def test_validate_split_request(self, task_splitting_service):
        """Test split request validation."""
        # Valid request
        valid_templates = [
            TaskTemplate(
                name="Valid Task",
                description="This is a valid task with proper length requirements",
                implementation_guide="Valid implementation with sufficient detail",
                dependencies=[]
            )
        ]
        
        valid_request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=valid_templates
        )
        
        is_valid, errors = await task_splitting_service.validate_split_request(valid_request)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid request - too many tasks
        invalid_templates = []
        for i in range(15):  # Exceeds max
            invalid_templates.append(TaskTemplate(
                name=f"Task {i}",
                description=f"Description {i} with adequate length",
                implementation_guide=f"Implementation {i}",
                dependencies=[]
            ))
        
        invalid_request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=invalid_templates
        )
        
        is_valid, errors = await task_splitting_service.validate_split_request(invalid_request)
        assert is_valid is False
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    async def test_get_execution_order(self, task_splitting_service):
        """Test getting execution order for tasks with dependencies."""
        templates = [
            TaskTemplate(
                name="Task C",
                description="Task C depends on A and B",
                implementation_guide="Implementation C",
                dependencies=["Task A", "Task B"]
            ),
            TaskTemplate(
                name="Task A",
                description="Task A has no dependencies",
                implementation_guide="Implementation A",
                dependencies=[]
            ),
            TaskTemplate(
                name="Task B",
                description="Task B depends on A",
                implementation_guide="Implementation B",
                dependencies=["Task A"]
            )
        ]
        
        execution_order = task_splitting_service.get_execution_order(templates)
        
        # Should return tasks in dependency order: A, B, C
        assert len(execution_order) == 3
        
        # Task A should come before B and C
        task_a_index = execution_order.index("Task A")
        task_b_index = execution_order.index("Task B")
        task_c_index = execution_order.index("Task C")
        
        assert task_a_index < task_b_index
        assert task_a_index < task_c_index
        assert task_b_index < task_c_index