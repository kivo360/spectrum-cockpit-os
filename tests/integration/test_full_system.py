"""Comprehensive integration tests for the full task management system."""

import pytest
import tempfile
import os
from pathlib import Path
from uuid import UUID

from src.models.task import ComplexityLevel, Priority, Task, TaskStatus, RelatedFile, RelatedFileType
from src.services.task_service import TaskService
from src.storage.duckdb_table import DuckDBTableStorage
from src.storage.networkx_graph import NetworkXGraphStorage


class TestFullSystemIntegration:
    """Test complete system integration with real storage backends."""
    
    @pytest.fixture
    async def integrated_service(self):
        """Create a fully integrated task service with real backends."""
        # Create temporary database file path
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)  # Close file descriptor
        os.unlink(db_path)  # Remove the file so DuckDB can create it fresh
        
        table_storage = None
        try:
            # Initialize real storage backends
            table_storage = DuckDBTableStorage(Task, database_path=db_path)
            graph_storage = NetworkXGraphStorage()
            
            # Create integrated service
            service = TaskService(table_storage, graph_storage)
            
            yield service
            
        finally:
            # Cleanup
            if table_storage is not None:
                table_storage.close()
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_end_to_end_task_lifecycle(self, integrated_service: TaskService):
        """Test complete task lifecycle from creation to completion."""
        # Phase 1: Create initial tasks
        database_task = Task(
            name="Setup Database",
            description="Configure PostgreSQL database with proper schemas and indexes",
            implementation_guide="1. Install PostgreSQL 2. Create database 3. Run migrations 4. Set up indexes",
            priority=Priority.P0,
            complexity=ComplexityLevel.SIMPLE,
            estimated_hours=4,
            category="Infrastructure"
        )
        
        api_task = Task(
            name="Build REST API",
            description="Implement RESTful API endpoints for task management with authentication",
            implementation_guide="1. Set up FastAPI 2. Implement auth middleware 3. Create CRUD endpoints 4. Add validation",
            priority=Priority.P1,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=8,
            category="Backend",
            related_files=[
                RelatedFile(
                    path="src/api/routes.py",
                    type=RelatedFileType.CREATE,
                    description="Main API route definitions"
                ),
                RelatedFile(
                    path="src/api/auth.py",
                    type=RelatedFileType.CREATE,
                    description="Authentication middleware"
                )
            ]
        )
        
        frontend_task = Task(
            name="Create React Frontend",
            description="Build responsive React frontend with TypeScript and modern UI components",
            implementation_guide="1. Set up React + TypeScript 2. Create component library 3. Implement routing 4. Connect to API",
            priority=Priority.P1,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=12,
            category="Frontend"
        )
        
        # Create tasks in service
        created_db = await integrated_service.create_task(database_task)
        created_api = await integrated_service.create_task(api_task)
        created_frontend = await integrated_service.create_task(frontend_task)
        
        # Verify tasks were created in both storages
        assert created_db.id == database_task.id
        assert created_api.id == api_task.id
        assert created_frontend.id == frontend_task.id
        
        # Phase 2: Add dependencies
        api_depends_on_db = await integrated_service.add_dependency(
            created_api.id, created_db.id
        )
        frontend_depends_on_api = await integrated_service.add_dependency(
            created_frontend.id, created_api.id
        )
        
        assert api_depends_on_db is True
        assert frontend_depends_on_api is True
        
        # Phase 3: Verify dependency relationships
        api_deps = await integrated_service.get_task_dependencies(created_api.id)
        frontend_deps = await integrated_service.get_task_dependencies(created_frontend.id)
        
        assert len(api_deps) == 1
        assert api_deps[0].id == created_db.id
        assert len(frontend_deps) == 1
        assert frontend_deps[0].id == created_api.id
        
        # Phase 4: Check execution order
        execution_order = await integrated_service.get_execution_order()
        assert len(execution_order) == 3
        
        # Database should come first, frontend last
        db_index = next(i for i, task in enumerate(execution_order) if task.id == created_db.id)
        api_index = next(i for i, task in enumerate(execution_order) if task.id == created_api.id)
        frontend_index = next(i for i, task in enumerate(execution_order) if task.id == created_frontend.id)
        
        assert db_index < api_index < frontend_index
        
        # Phase 5: Check ready tasks (should only be database initially)
        ready_tasks = await integrated_service.get_ready_tasks()
        assert len(ready_tasks) == 1
        assert ready_tasks[0].id == created_db.id
        
        # Phase 6: Complete database task
        created_db.status = TaskStatus.COMPLETED
        updated_db = await integrated_service.update_task(created_db)
        assert updated_db.status == TaskStatus.COMPLETED
        
        # Phase 7: Check ready tasks again (should now include API)
        ready_tasks = await integrated_service.get_ready_tasks()
        ready_ids = {task.id for task in ready_tasks}
        assert created_api.id in ready_ids
        assert created_frontend.id not in ready_ids  # Still blocked by API
        
        # Phase 8: Complete API task
        created_api.status = TaskStatus.COMPLETED
        await integrated_service.update_task(created_api)
        
        # Phase 9: Check ready tasks final time (should now include frontend)
        ready_tasks = await integrated_service.get_ready_tasks()
        ready_ids = {task.id for task in ready_tasks}
        assert created_frontend.id in ready_ids
        
        # Phase 10: Get project statistics
        stats = await integrated_service.get_project_statistics()
        assert stats["total_tasks"] == 3
        assert stats["graph_nodes"] == 3
        assert stats["graph_edges"] == 2
        assert stats["has_cycles"] is False
        assert stats["status_breakdown"]["COMPLETED"] == 2
        assert stats["status_breakdown"]["PENDING"] == 1
    
    async def test_bulk_operations_integration(self, integrated_service: TaskService):
        """Test bulk operations work correctly across both storage systems."""
        # Create multiple related tasks
        tasks = [
            Task(
                name=f"Feature Task {i}",
                description=f"Implement feature component {i} with comprehensive testing",
                implementation_guide=f"1. Design component {i} 2. Implement logic 3. Add tests 4. Document API",
                priority=Priority.P2,
                complexity=ComplexityLevel.MODERATE,
                estimated_hours=6,
                category="Development"
            )
            for i in range(1, 6)
        ]
        
        # Bulk create
        created_tasks = await integrated_service.bulk_create_tasks(tasks)
        assert len(created_tasks) == 5
        
        # Verify all created in table storage
        all_tasks = await integrated_service.list_tasks()
        assert len(all_tasks) == 5
        
        # Verify all created in graph storage
        execution_order = await integrated_service.get_execution_order()
        assert len(execution_order) == 5
        
        # Verify statistics
        stats = await integrated_service.get_project_statistics()
        assert stats["total_tasks"] == 5
        assert stats["graph_nodes"] == 5
        assert stats["graph_edges"] == 0  # No dependencies added yet
    
    async def test_complex_dependency_scenarios(self, integrated_service: TaskService):
        """Test complex dependency scenarios and cycle detection."""
        # Create a diamond dependency pattern:
        # A depends on B and C
        # B and C both depend on D
        
        task_d = Task(name="Base Task D", description="Foundation task", implementation_guide="Base implementation")
        task_c = Task(name="Task C", description="Depends on D", implementation_guide="C implementation")
        task_b = Task(name="Task B", description="Depends on D", implementation_guide="B implementation") 
        task_a = Task(name="Task A", description="Depends on B and C", implementation_guide="A implementation")
        
        # Create tasks
        created_d = await integrated_service.create_task(task_d)
        created_c = await integrated_service.create_task(task_c)
        created_b = await integrated_service.create_task(task_b)
        created_a = await integrated_service.create_task(task_a)
        
        # Add dependencies to create diamond pattern
        await integrated_service.add_dependency(created_c.id, created_d.id)
        await integrated_service.add_dependency(created_b.id, created_d.id)
        await integrated_service.add_dependency(created_a.id, created_b.id)
        await integrated_service.add_dependency(created_a.id, created_c.id)
        
        # Verify no cycles detected
        has_cycles = await integrated_service.detect_circular_dependencies()
        assert has_cycles is False
        
        # Verify execution order respects all dependencies
        execution_order = await integrated_service.get_execution_order()
        task_positions = {task.id: i for i, task in enumerate(execution_order)}
        
        # D should come before B and C
        assert task_positions[created_d.id] < task_positions[created_b.id]
        assert task_positions[created_d.id] < task_positions[created_c.id]
        
        # B and C should come before A
        assert task_positions[created_b.id] < task_positions[created_a.id]
        assert task_positions[created_c.id] < task_positions[created_a.id]
        
        # Try to create a cycle (A -> D) - should fail
        cycle_added = await integrated_service.add_dependency(created_d.id, created_a.id)
        assert cycle_added is False
        
        # Verify still no cycles
        has_cycles = await integrated_service.detect_circular_dependencies()
        assert has_cycles is False
    
    async def test_task_filtering_and_queries(self, integrated_service: TaskService):
        """Test advanced querying and filtering across storage systems."""
        # Create diverse set of tasks
        tasks = [
            Task(
                name="Critical Bug Fix",
                description="Fix critical security vulnerability in authentication",
                implementation_guide="1. Identify issue 2. Patch code 3. Test fix 4. Deploy",
                priority=Priority.P0,
                complexity=ComplexityLevel.SIMPLE,
                estimated_hours=3,
                category="Security",
                status=TaskStatus.IN_PROGRESS
            ),
            Task(
                name="User Dashboard",
                description="Create comprehensive user dashboard with analytics",
                implementation_guide="1. Design wireframes 2. Implement components 3. Add charts 4. Optimize performance",
                priority=Priority.P1,
                complexity=ComplexityLevel.COMPLEX,
                estimated_hours=15,
                category="Frontend",
                status=TaskStatus.PENDING
            ),
            Task(
                name="API Documentation",
                description="Complete API documentation with examples and tutorials",
                implementation_guide="1. Document endpoints 2. Add examples 3. Create tutorials 4. Review content",
                priority=Priority.P2,
                complexity=ComplexityLevel.MODERATE,
                estimated_hours=8,
                category="Documentation",
                status=TaskStatus.COMPLETED
            ),
            Task(
                name="Performance Optimization",
                description="Optimize database queries and application performance",
                implementation_guide="1. Profile application 2. Identify bottlenecks 3. Optimize queries 4. Monitor improvements",
                priority=Priority.P1,
                complexity=ComplexityLevel.COMPLEX,
                estimated_hours=12,
                category="Backend",
                status=TaskStatus.PENDING
            )
        ]
        
        # Create all tasks
        for task in tasks:
            await integrated_service.create_task(task)
        
        # Test filtering by status
        pending_tasks = await integrated_service.list_tasks({"status": TaskStatus.PENDING.value})
        assert len(pending_tasks) == 2
        
        in_progress_tasks = await integrated_service.list_tasks({"status": TaskStatus.IN_PROGRESS.value})
        assert len(in_progress_tasks) == 1
        
        completed_tasks = await integrated_service.list_tasks({"status": TaskStatus.COMPLETED.value})
        assert len(completed_tasks) == 1
        
        # Test filtering by priority
        p0_tasks = await integrated_service.list_tasks({"priority": Priority.P0.value})
        assert len(p0_tasks) == 1
        assert p0_tasks[0].name == "Critical Bug Fix"
        
        p1_tasks = await integrated_service.list_tasks({"priority": Priority.P1.value})
        assert len(p1_tasks) == 2
        
        # Test filtering by category
        frontend_tasks = await integrated_service.list_tasks({"category": "Frontend"})
        assert len(frontend_tasks) == 1
        assert frontend_tasks[0].name == "User Dashboard"
        
        backend_tasks = await integrated_service.list_tasks({"category": "Backend"})
        assert len(backend_tasks) == 1
        
        # Test filtering by complexity
        complex_tasks = await integrated_service.list_tasks({"complexity": ComplexityLevel.COMPLEX.value})
        assert len(complex_tasks) == 2
        
        # Test multiple filters
        pending_p1_tasks = await integrated_service.list_tasks({
            "status": TaskStatus.PENDING.value,
            "priority": Priority.P1.value
        })
        assert len(pending_p1_tasks) == 2
    
    async def test_data_persistence_and_recovery(self, integrated_service: TaskService):
        """Test that data persists correctly in DuckDB storage."""
        # Create a task with complex data
        complex_task = Task(
            name="Integration Test Task",
            description="Complex task for testing data persistence with comprehensive metadata",
            implementation_guide="Detailed multi-step implementation with various requirements and constraints",
            verification_criteria="Comprehensive verification steps to ensure quality and completeness",
            priority=Priority.P1,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=7,
            category="Testing",
            notes="Important notes about special requirements and considerations for this task",
            related_files=[
                RelatedFile(
                    path="tests/integration/test_persistence.py",
                    type=RelatedFileType.CREATE,
                    description="Integration test file for persistence testing",
                    line_start=1,
                    line_end=100
                ),
                RelatedFile(
                    path="src/models/persistence.py",
                    type=RelatedFileType.TO_MODIFY,
                    description="Persistence model to be modified",
                    line_start=50,
                    line_end=75
                )
            ]
        )
        
        # Create task
        created_task = await integrated_service.create_task(complex_task)
        original_id = created_task.id
        
        # Update task
        created_task.status = TaskStatus.IN_PROGRESS
        created_task.notes = "Updated notes with progress information"
        updated_task = await integrated_service.update_task(created_task)
        
        # Retrieve task and verify all data persisted correctly
        retrieved_task = await integrated_service.get_task(original_id)
        
        assert retrieved_task is not None
        assert retrieved_task.id == original_id
        assert retrieved_task.name == "Integration Test Task"
        assert retrieved_task.description == complex_task.description
        assert retrieved_task.implementation_guide == complex_task.implementation_guide
        assert retrieved_task.verification_criteria == complex_task.verification_criteria
        assert retrieved_task.status == TaskStatus.IN_PROGRESS
        assert retrieved_task.priority == Priority.P1
        assert retrieved_task.complexity == ComplexityLevel.MODERATE
        assert retrieved_task.estimated_hours == 7
        assert retrieved_task.category == "Testing"
        assert retrieved_task.notes == "Updated notes with progress information"
        
        # Verify related files persisted correctly
        assert len(retrieved_task.related_files) == 2
        
        test_file = next(f for f in retrieved_task.related_files if "test_persistence.py" in f.path)
        assert test_file.type == RelatedFileType.CREATE
        assert test_file.line_start == 1
        assert test_file.line_end == 100
        
        model_file = next(f for f in retrieved_task.related_files if "persistence.py" in f.path)
        assert model_file.type == RelatedFileType.TO_MODIFY
        assert model_file.line_start == 50
        assert model_file.line_end == 75
        
        # Verify timestamps
        assert retrieved_task.created_at == created_task.created_at
        assert retrieved_task.updated_at > created_task.created_at
    
    async def test_service_error_handling(self, integrated_service: TaskService):
        """Test error handling and rollback scenarios."""
        # Test creating task with invalid dependency
        task_with_invalid_dep = Task(
            name="Invalid Dependency Task",
            description="Task with non-existent dependency",
            implementation_guide="Should fail during creation"
        )
        
        # This should work (task creation without dependencies)
        created_task = await integrated_service.create_task(task_with_invalid_dep)
        assert created_task.id == task_with_invalid_dep.id
        
        # Test adding invalid dependency
        invalid_uuid = UUID('00000000-0000-0000-0000-000000000000')
        
        with pytest.raises(ValueError, match="not found"):
            await integrated_service.add_dependency(created_task.id, invalid_uuid)
        
        # Test updating non-existent task
        non_existent_task = Task(
            id=invalid_uuid,
            name="Non-existent",
            description="This task doesn't exist",
            implementation_guide="Should fail"
        )
        
        with pytest.raises(ValueError, match="doesn't exist"):
            await integrated_service.update_task(non_existent_task)
        
        # Test deleting non-existent task
        deleted = await integrated_service.delete_task(invalid_uuid)
        assert deleted is False
    
    async def test_comprehensive_statistics(self, integrated_service: TaskService):
        """Test comprehensive statistics generation."""
        # Create a representative project structure
        tasks = [
            Task(name="Setup", description="Project setup", implementation_guide="Setup steps", 
                 status=TaskStatus.COMPLETED, priority=Priority.P0, complexity=ComplexityLevel.SIMPLE, category="Infrastructure"),
            Task(name="Backend API", description="REST API", implementation_guide="API steps", 
                 status=TaskStatus.IN_PROGRESS, priority=Priority.P1, complexity=ComplexityLevel.MODERATE, category="Backend"),
            Task(name="Frontend UI", description="User interface", implementation_guide="UI steps", 
                 status=TaskStatus.PENDING, priority=Priority.P1, complexity=ComplexityLevel.COMPLEX, category="Frontend"),
            Task(name="Testing", description="Test suite", implementation_guide="Test steps", 
                 status=TaskStatus.BLOCKED, priority=Priority.P2, complexity=ComplexityLevel.MODERATE, category="QA"),
            Task(name="Documentation", description="User docs", implementation_guide="Doc steps", 
                 status=TaskStatus.PENDING, priority=Priority.P3, complexity=ComplexityLevel.SIMPLE, category="Documentation")
        ]
        
        # Create tasks and dependencies
        created_tasks = []
        for task in tasks:
            created_task = await integrated_service.create_task(task)
            created_tasks.append(created_task)
        
        # Add some dependencies
        await integrated_service.add_dependency(created_tasks[1].id, created_tasks[0].id)  # API depends on Setup
        await integrated_service.add_dependency(created_tasks[2].id, created_tasks[1].id)  # UI depends on API
        await integrated_service.add_dependency(created_tasks[3].id, created_tasks[2].id)  # Testing depends on UI
        
        # Get comprehensive statistics
        stats = await integrated_service.get_project_statistics()
        
        # Verify basic counts
        assert stats["total_tasks"] == 5
        assert stats["graph_nodes"] == 5
        assert stats["graph_edges"] == 3
        assert stats["has_cycles"] is False
        
        # Verify status breakdown
        expected_status = {
            "COMPLETED": 1,
            "IN_PROGRESS": 1, 
            "PENDING": 2,
            "BLOCKED": 1
        }
        
        for status, expected_count in expected_status.items():
            assert stats["status_breakdown"][status] == expected_count
        
        # Verify ready tasks (only Setup is complete, so Backend should be ready)
        assert stats["ready_tasks_count"] == 1  # Only Backend is ready (Setup completed)
        
        # Verify timestamps exist
        assert stats["earliest_created"] is not None
        assert stats["latest_created"] is not None
        assert stats["latest_updated"] is not None