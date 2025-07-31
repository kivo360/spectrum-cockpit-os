"""Integration tests for the MCP server implementation."""

import asyncio
import json
import tempfile
import os
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.server import (
    server,
    initialize_service,
    handle_call_tool,
    handle_read_resource,
    format_task_summary,
    format_task_detailed,
)
from src.models.task import ComplexityLevel, Priority, Task, TaskStatus


class TestMCPServerIntegration:
    """Test MCP server integration and tool functionality."""
    
    @pytest.fixture
    async def test_service(self):
        """Create a test service with temporary database."""
        # Store original env var
        original_db_path = os.environ.get("TASK_DB_PATH")
        
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        try:
            # Set environment variable for test
            os.environ["TASK_DB_PATH"] = db_path
            
            # Initialize service
            service = await initialize_service()
            
            # Set global service for tools
            import src.server
            src.server.task_service = service
            
            yield service
            
        finally:
            # Cleanup
            service.table_storage.close()
            if os.path.exists(db_path):
                os.unlink(db_path)
            
            # Restore original env var
            if original_db_path:
                os.environ["TASK_DB_PATH"] = original_db_path
            elif "TASK_DB_PATH" in os.environ:
                del os.environ["TASK_DB_PATH"]
    
    async def test_create_task_tool(self, test_service):
        """Test the create_task MCP tool."""
        tool_args = {
            "name": "Test Task via MCP",
            "description": "Testing task creation through MCP server tool interface",
            "implementation_guide": "1. Create task 2. Verify creation 3. Test functionality",
            "priority": "P1",
            "complexity": "MODERATE",
            "estimated_hours": 6,
            "category": "Testing",
            "notes": "Created via MCP tool test"
        }
        
        # Call the tool
        result = await handle_call_tool("create_task", tool_args)
        
        # Verify response
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Task Created Successfully" in result[0].text
        assert "Test Task via MCP" in result[0].text
        
        # Verify task was actually created in service
        tasks = await test_service.list_tasks({"category": "Testing"})
        assert len(tasks) == 1
        assert tasks[0].name == "Test Task via MCP"
        assert tasks[0].priority == Priority.P1
        assert tasks[0].complexity == ComplexityLevel.MODERATE
    
    async def test_list_tasks_tool(self, test_service):
        """Test the list_tasks MCP tool with filters."""
        # Create test tasks
        test_tasks = [
            Task(
                name="Backend Task",
                description="Backend development task",
                implementation_guide="Backend implementation steps",
                priority=Priority.P1,
                status=TaskStatus.IN_PROGRESS,
                category="Backend"
            ),
            Task(
                name="Frontend Task", 
                description="Frontend development task",
                implementation_guide="Frontend implementation steps",
                priority=Priority.P2,
                status=TaskStatus.PENDING,
                category="Frontend"
            ),
            Task(
                name="DevOps Task",
                description="DevOps and infrastructure task",
                implementation_guide="DevOps implementation steps",
                priority=Priority.P1,
                status=TaskStatus.COMPLETED,
                category="DevOps"
            )
        ]
        
        for task in test_tasks:
            await test_service.create_task(task)
        
        # Test listing all tasks
        result = await handle_call_tool("list_tasks", {})
        assert len(result) == 1
        assert "Found 3 Task(s)" in result[0].text
        
        # Test filtering by status
        result = await handle_call_tool("list_tasks", {"status": "IN_PROGRESS"})
        assert "Found 1 Task(s)" in result[0].text
        assert "Backend Task" in result[0].text
        
        # Test filtering by priority
        result = await handle_call_tool("list_tasks", {"priority": "P1"})
        assert "Found 2 Task(s)" in result[0].text
        
        # Test filtering by category
        result = await handle_call_tool("list_tasks", {"category": "Frontend"})
        assert "Found 1 Task(s)" in result[0].text
        assert "Frontend Task" in result[0].text
        
        # Test multiple filters
        result = await handle_call_tool("list_tasks", {
            "status": "PENDING",
            "priority": "P2"
        })
        assert "Found 1 Task(s)" in result[0].text
        assert "Frontend Task" in result[0].text
    
    async def test_dependency_management_tools(self, test_service):
        """Test dependency management through MCP tools."""
        # Create tasks
        database_task = Task(
            name="Database Setup",
            description="Set up database infrastructure",
            implementation_guide="Database setup steps"
        )
        api_task = Task(
            name="API Development", 
            description="Develop REST API",
            implementation_guide="API development steps"
        )
        
        db_task = await test_service.create_task(database_task)
        api_task_created = await test_service.create_task(api_task)
        
        # Add dependency via MCP tool
        result = await handle_call_tool("add_dependency", {
            "task_id": str(api_task_created.id),
            "depends_on_id": str(db_task.id)
        })
        
        assert len(result) == 1
        assert "Dependency added" in result[0].text
        
        # Get dependencies via MCP tool
        result = await handle_call_tool("get_task_dependencies", {
            "task_id": str(api_task_created.id)
        })
        
        assert "Dependencies for Task" in result[0].text
        assert "Database Setup" in result[0].text
        
        # Test execution order
        result = await handle_call_tool("get_execution_order", {})
        
        assert "Task Execution Order" in result[0].text
        assert "Database Setup" in result[0].text
        assert "API Development" in result[0].text
        
        # Database should appear before API in the text
        text = result[0].text
        db_pos = text.find("Database Setup")
        api_pos = text.find("API Development")
        assert db_pos < api_pos
    
    async def test_update_task_tool(self, test_service):
        """Test task updating through MCP tool."""
        # Create task
        task = Task(
            name="Original Task Name",
            description="Original description",
            implementation_guide="Original implementation guide",
            status=TaskStatus.PENDING,
            priority=Priority.P2
        )
        
        created_task = await test_service.create_task(task)
        
        # Update task via MCP tool
        result = await handle_call_tool("update_task", {
            "task_id": str(created_task.id),
            "name": "Updated Task Name",
            "status": "IN_PROGRESS",
            "priority": "P1",
            "notes": "Added some important notes"
        })
        
        assert len(result) == 1
        assert "Task Updated Successfully" in result[0].text
        assert "Updated Task Name" in result[0].text
        
        # Verify task was actually updated
        updated_task = await test_service.get_task(created_task.id)
        assert updated_task.name == "Updated Task Name"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.priority == Priority.P1
        assert updated_task.notes == "Added some important notes"
    
    async def test_bulk_create_tasks_tool(self, test_service):
        """Test bulk task creation through MCP tool."""
        tasks_data = [
            {
                "name": "Feature A",
                "description": "Implement feature A with comprehensive testing",
                "implementation_guide": "Steps for implementing feature A",
                "priority": "P1",
                "complexity": "MODERATE",
                "estimated_hours": 8,
                "category": "Development"
            },
            {
                "name": "Feature B",
                "description": "Implement feature B with user interface",
                "implementation_guide": "Steps for implementing feature B",
                "priority": "P2", 
                "complexity": "COMPLEX",
                "estimated_hours": 12,
                "category": "Development"
            },
            {
                "name": "Integration Testing",
                "description": "Test integration between features A and B",
                "implementation_guide": "Steps for integration testing",
                "priority": "P1",
                "complexity": "SIMPLE",
                "estimated_hours": 4,
                "category": "QA"
            }
        ]
        
        # Bulk create via MCP tool
        result = await handle_call_tool("bulk_create_tasks", {
            "tasks": tasks_data
        })
        
        assert len(result) == 1
        assert "3 Tasks Created Successfully" in result[0].text
        assert "Feature A" in result[0].text
        assert "Feature B" in result[0].text
        assert "Integration Testing" in result[0].text
        
        # Verify tasks were created
        all_tasks = await test_service.list_tasks()
        assert len(all_tasks) == 3
        
        dev_tasks = await test_service.list_tasks({"category": "Development"})
        assert len(dev_tasks) == 2
        
        qa_tasks = await test_service.list_tasks({"category": "QA"})
        assert len(qa_tasks) == 1
    
    async def test_statistics_and_analysis_tools(self, test_service):
        """Test project statistics and analysis tools."""
        # Create diverse set of tasks
        tasks = [
            Task(name="Completed Task", description="Done", implementation_guide="Done", status=TaskStatus.COMPLETED),
            Task(name="In Progress Task", description="Working", implementation_guide="Working", status=TaskStatus.IN_PROGRESS),
            Task(name="Pending Task 1", description="Waiting", implementation_guide="Waiting", status=TaskStatus.PENDING),
            Task(name="Pending Task 2", description="Waiting", implementation_guide="Waiting", status=TaskStatus.PENDING),
            Task(name="Blocked Task", description="Blocked", implementation_guide="Blocked", status=TaskStatus.BLOCKED)
        ]
        
        created_tasks = []
        for task in tasks:
            created_task = await test_service.create_task(task)
            created_tasks.append(created_task)
        
        # Add some dependencies
        await test_service.add_dependency(created_tasks[1].id, created_tasks[0].id)
        await test_service.add_dependency(created_tasks[2].id, created_tasks[1].id)
        
        # Test statistics tool
        result = await handle_call_tool("get_statistics", {})
        
        assert "Project Statistics" in result[0].text
        assert "Total Tasks: 5" in result[0].text
        assert "Graph Nodes: 5" in result[0].text
        assert "Graph Edges: 2" in result[0].text
        assert "COMPLETED: 1" in result[0].text
        assert "IN_PROGRESS: 1" in result[0].text
        assert "PENDING: 2" in result[0].text
        assert "BLOCKED: 1" in result[0].text
        
        # Test cycle detection tool
        result = await handle_call_tool("detect_cycles", {})
        assert "No circular dependencies found" in result[0].text
        
        # Test ready tasks tool
        result = await handle_call_tool("get_ready_tasks", {})
        assert "Ready Tasks" in result[0].text
        # Should show tasks with no pending dependencies
    
    async def test_resource_reading(self, test_service):
        """Test MCP resource reading functionality."""
        # Create some test data
        tasks = [
            Task(name="Setup", description="Setup task", implementation_guide="Setup", status=TaskStatus.COMPLETED),
            Task(name="Development", description="Dev task", implementation_guide="Dev", status=TaskStatus.IN_PROGRESS),
            Task(name="Testing", description="Test task", implementation_guide="Test", status=TaskStatus.PENDING)
        ]
        
        created_tasks = []
        for task in tasks:
            created_task = await test_service.create_task(task)
            created_tasks.append(created_task)
        
        # Add dependencies
        await test_service.add_dependency(created_tasks[1].id, created_tasks[0].id)
        await test_service.add_dependency(created_tasks[2].id, created_tasks[1].id)
        
        # Test statistics resource
        stats_resource = await handle_read_resource("task://statistics")
        stats_data = json.loads(stats_resource)
        
        assert stats_data["total_tasks"] == 3
        assert stats_data["graph_nodes"] == 3
        assert stats_data["graph_edges"] == 2
        assert stats_data["status_breakdown"]["COMPLETED"] == 1
        assert stats_data["status_breakdown"]["IN_PROGRESS"] == 1
        assert stats_data["status_breakdown"]["PENDING"] == 1
        
        # Test execution order resource
        order_resource = await handle_read_resource("task://execution-order")
        
        assert "Task Execution Order" in order_resource
        assert "Setup" in order_resource
        assert "Development" in order_resource
        assert "Testing" in order_resource
        
        # Test ready tasks resource
        ready_resource = await handle_read_resource("task://ready-tasks")
        
        assert "Ready Tasks" in ready_resource
        # Development should be ready since Setup is completed
        assert "Development" in ready_resource
    
    async def test_error_handling_in_tools(self, test_service):
        """Test error handling in MCP tools."""
        # Test creating task with invalid data
        result = await handle_call_tool("create_task", {
            "name": "",  # Invalid: empty name
            "description": "Valid description",
            "implementation_guide": "Valid guide"
        })
        
        assert len(result) == 1
        assert "Validation Error" in result[0].text or "Error" in result[0].text
        
        # Test getting non-existent task
        result = await handle_call_tool("get_task", {
            "task_id": "00000000-0000-0000-0000-000000000000"
        })
        
        assert "not found" in result[0].text
        
        # Test updating non-existent task
        result = await handle_call_tool("update_task", {
            "task_id": "00000000-0000-0000-0000-000000000000",
            "name": "Updated Name"
        })
        
        assert "not found" in result[0].text
        
        # Test invalid tool name
        result = await handle_call_tool("invalid_tool", {})
        
        assert "Unknown tool" in result[0].text
    
    async def test_task_formatting_functions(self, test_service):
        """Test task formatting functions used by MCP server."""
        # Create a comprehensive test task
        task = Task(
            name="Comprehensive Test Task",
            description="A task with all possible fields populated for testing formatting functions",
            implementation_guide="Detailed step-by-step implementation guide with multiple phases",
            verification_criteria="Comprehensive verification steps to ensure quality",
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.P1,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=8,
            category="Testing",
            notes="Important notes about this task and special considerations"
        )
        
        # Test summary formatting
        summary = format_task_summary(task)
        
        assert "🔄" in summary  # IN_PROGRESS emoji
        assert "🟡" in summary  # P1 priority emoji
        assert "Comprehensive Test Task" in summary
        assert task.description[:100] in summary
        
        # Test detailed formatting
        detailed = format_task_detailed(task)
        
        assert "# 📋 Task: Comprehensive Test Task" in detailed
        assert str(task.id) in detailed
        assert "IN_PROGRESS" in detailed
        assert "P1" in detailed
        assert task.description in detailed
        assert task.implementation_guide in detailed
        assert task.verification_criteria in detailed
        assert "MODERATE" in detailed
        assert "8" in detailed
        assert "Testing" in detailed
        assert task.notes in detailed
        assert task.created_at.isoformat()[:10] in detailed  # Date part
    
    async def test_complex_workflow_scenario(self, test_service):
        """Test a complex workflow scenario through MCP tools."""
        # Scenario: Create a web application project with proper dependencies
        
        # Phase 1: Create foundational tasks
        foundation_tasks = [
            {
                "name": "Database Schema Design",
                "description": "Design database schema for web application with user management and content storage",
                "implementation_guide": "1. Analyze requirements 2. Design ERD 3. Create schema 4. Add indexes",
                "priority": "P0",
                "complexity": "MODERATE",
                "estimated_hours": 6,
                "category": "Database"
            },
            {
                "name": "Authentication System",
                "description": "Implement JWT-based authentication with role-based access control",
                "implementation_guide": "1. Set up JWT 2. Create auth middleware 3. Implement RBAC 4. Add session management",
                "priority": "P0", 
                "complexity": "COMPLEX",
                "estimated_hours": 12,
                "category": "Backend"
            },
            {
                "name": "REST API Framework",
                "description": "Set up FastAPI framework with proper error handling and validation",
                "implementation_guide": "1. Install FastAPI 2. Set up routing 3. Add validation 4. Implement error handling",
                "priority": "P1",
                "complexity": "MODERATE",
                "estimated_hours": 8,
                "category": "Backend"
            }
        ]
        
        # Create foundation tasks
        result = await handle_call_tool("bulk_create_tasks", {"tasks": foundation_tasks})
        assert "3 Tasks Created Successfully" in result[0].text
        
        # Get created task IDs for dependency management
        db_tasks = await test_service.list_tasks({"category": "Database"})
        backend_tasks = await test_service.list_tasks({"category": "Backend"})
        
        db_task_id = db_tasks[0].id
        auth_task = next(t for t in backend_tasks if "Authentication" in t.name)
        api_task = next(t for t in backend_tasks if "REST API" in t.name)
        
        # Phase 2: Add dependencies
        # Auth depends on Database
        result = await handle_call_tool("add_dependency", {
            "task_id": str(auth_task.id),
            "depends_on_id": str(db_task_id)
        })
        assert "Dependency added" in result[0].text
        
        # API depends on Auth
        result = await handle_call_tool("add_dependency", {
            "task_id": str(api_task.id),
            "depends_on_id": str(auth_task.id)
        })
        assert "Dependency added" in result[0].text
        
        # Phase 3: Check execution order
        result = await handle_call_tool("get_execution_order", {})
        text = result[0].text
        
        # Verify proper ordering
        db_pos = text.find("Database Schema")
        auth_pos = text.find("Authentication System")
        api_pos = text.find("REST API Framework")
        
        assert db_pos < auth_pos < api_pos
        
        # Phase 4: Simulate work progress
        # Complete database task
        result = await handle_call_tool("update_task", {
            "task_id": str(db_task_id),
            "status": "COMPLETED",
            "notes": "Database schema implemented and tested"
        })
        assert "Task Updated Successfully" in result[0].text
        
        # Check ready tasks - Auth should now be ready
        result = await handle_call_tool("get_ready_tasks", {})
        assert "Authentication System" in result[0].text
        
        # Start working on auth
        result = await handle_call_tool("update_task", {
            "task_id": str(auth_task.id),
            "status": "IN_PROGRESS",
            "notes": "Started implementing JWT authentication"
        })
        
        # Phase 5: Check final statistics
        result = await handle_call_tool("get_statistics", {})
        
        assert "Total Tasks: 3" in result[0].text
        assert "Graph Edges: 2" in result[0].text
        assert "COMPLETED: 1" in result[0].text
        assert "IN_PROGRESS: 1" in result[0].text
        assert "PENDING: 1" in result[0].text
        
        # Verify no cycles
        result = await handle_call_tool("detect_cycles", {})
        assert "No circular dependencies found" in result[0].text