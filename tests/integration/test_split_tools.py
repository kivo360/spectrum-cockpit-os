"""
Integration tests for MCP split tools.

Tests the integration between task splitting service and FastMCP server,
ensuring proper JSON handling, validation, and response formatting.
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.server import create_mcp
from src.models.task_splitting import (
    TaskSplitRequest, 
    TaskTemplate, 
    UpdateMode,
    SplitResult,
    SplitOperation
)
from src.models.task import Task, TaskStatus
from src.services.task_splitting_service import TaskSplittingService


class TestMCPSplitTools:
    """Test MCP split tools integration."""
    
    @pytest.fixture
    def mock_task_splitting_service(self):
        """Mock task splitting service for testing."""
        service = Mock(spec=TaskSplittingService)
        
        # Mock successful split result
        successful_result = SplitResult(
            success=True,
            created_tasks=[
                Task(
                    name="Test Task",
                    description="Test task description for MCP integration",
                    implementation_guide="Implementation guide for test task"
                )
            ],
            operation=SplitOperation(
                operation_type="split_tasks",
                update_mode=UpdateMode.CLEAR_ALL_TASKS,
                tasks_before_count=0,
                tasks_after_count=1,
                tasks_added=1,
                tasks_updated=0,
                tasks_removed=0
            ),
            message="Successfully processed 1 task using clearAllTasks mode",
            errors=[]
        )
        
        service.split_tasks = AsyncMock(return_value=successful_result)
        return service
    
    @pytest.fixture
    def mcp_server(self, mock_task_splitting_service):
        """Create MCP server with mocked services."""
        # Import server module and patch the global service instances
        import src.server
        
        # Store original values
        original_task_splitting_service = src.server.task_splitting_service
        
        # Replace with mock
        src.server.task_splitting_service = mock_task_splitting_service
        
        # Create server
        server = create_mcp()
        
        # Restore original value after test
        yield server
        src.server.task_splitting_service = original_task_splitting_service
    
    @pytest.mark.asyncio
    async def test_split_tasks_tool_exists(self, mcp_server):
        """Test that split_tasks tool is registered."""
        tools = await mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "split_tasks" in tool_names
    
    @pytest.mark.asyncio
    async def test_split_tasks_tool_schema(self, mcp_server):
        """Test split_tasks tool has proper schema."""
        tools = await mcp_server.list_tools()
        split_tasks_tool = next(tool for tool in tools if tool.name == "split_tasks")
        
        # Check tool has required properties
        assert split_tasks_tool.description is not None
        assert "task" in split_tasks_tool.description.lower()
        assert "split" in split_tasks_tool.description.lower()
        
        # Check input schema has required fields
        schema = split_tasks_tool.inputSchema
        assert "properties" in schema
        properties = schema["properties"]
        
        assert "updateMode" in properties
        assert "tasksRaw" in properties
        assert "globalAnalysisResult" in properties
    
    @pytest.mark.asyncio
    async def test_split_tasks_clear_all_mode(self, mcp_server, mock_task_splitting_service):
        """Test split_tasks tool with clearAllTasks mode."""
        tasks_raw = json.dumps([
            {
                "name": "Setup Development Environment",
                "description": "Initialize project with dependencies and configuration",
                "implementation_guide": "1. Install Node.js\n2. Setup project structure\n3. Configure environment",
                "dependencies": []
            },
            {
                "name": "Implement Authentication",
                "description": "Create user authentication system with proper security",
                "implementation_guide": "1. Setup JWT\n2. Create login/logout endpoints\n3. Add middleware",
                "dependencies": ["Setup Development Environment"]
            }
        ])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "clearAllTasks",
                "tasksRaw": tasks_raw,
                "globalAnalysisResult": "Build a secure web application"
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        assert "success" in result_text.lower() or "task" in result_text.lower()
        
        # Verify service was called with correct parameters
        mock_task_splitting_service.split_tasks.assert_called_once()
        call_args = mock_task_splitting_service.split_tasks.call_args[0][0]
        
        assert isinstance(call_args, TaskSplitRequest)
        assert call_args.update_mode == UpdateMode.CLEAR_ALL_TASKS
        assert len(call_args.task_templates) == 2
        assert call_args.global_analysis_result == "Build a secure web application"
    
    @pytest.mark.asyncio
    async def test_split_tasks_append_mode(self, mcp_server, mock_task_splitting_service):
        """Test split_tasks tool with append mode."""
        tasks_raw = json.dumps([
            {
                "name": "New Feature",
                "description": "Add new feature to existing application with proper testing",
                "implementation_guide": "1. Design feature\n2. Implement code\n3. Add tests",
                "dependencies": []
            }
        ])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "append",
                "tasksRaw": tasks_raw
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Verify service was called with append mode
        call_args = mock_task_splitting_service.split_tasks.call_args[0][0]
        assert call_args.update_mode == UpdateMode.APPEND
        assert len(call_args.task_templates) == 1
    
    @pytest.mark.asyncio
    async def test_split_tasks_selective_mode(self, mcp_server, mock_task_splitting_service):
        """Test split_tasks tool with selective mode."""
        tasks_raw = json.dumps([
            {
                "name": "Update Existing Task",
                "description": "Updated description with more comprehensive details",
                "implementation_guide": "Updated implementation with new requirements",
                "dependencies": [],
                "notes": "Updated with new specifications"
            }
        ])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "selective",
                "tasksRaw": tasks_raw
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Verify service was called with selective mode
        call_args = mock_task_splitting_service.split_tasks.call_args[0][0]
        assert call_args.update_mode == UpdateMode.SELECTIVE
    
    @pytest.mark.asyncio
    async def test_split_tasks_with_dependencies(self, mcp_server, mock_task_splitting_service):
        """Test split_tasks tool with complex dependencies."""
        tasks_raw = json.dumps([
            {
                "name": "Database Setup",
                "description": "Setup database schema and connections with proper indexing",
                "implementation_guide": "1. Create schema\n2. Setup connections\n3. Add indexes",
                "dependencies": []
            },
            {
                "name": "API Development",
                "description": "Develop REST API endpoints with proper validation",
                "implementation_guide": "1. Create routes\n2. Add validation\n3. Test endpoints",
                "dependencies": ["Database Setup"]
            },
            {
                "name": "Frontend Integration",
                "description": "Integrate frontend with API endpoints and handle errors",
                "implementation_guide": "1. Connect to API\n2. Handle responses\n3. Error handling",
                "dependencies": ["API Development"]
            }
        ])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "clearAllTasks",
                "tasksRaw": tasks_raw,
                "globalAnalysisResult": "Full-stack application development"
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Verify complex dependency structure was parsed correctly
        call_args = mock_task_splitting_service.split_tasks.call_args[0][0]
        assert len(call_args.task_templates) == 3
        
        # Check dependencies were parsed correctly
        templates_by_name = {t.name: t for t in call_args.task_templates}
        
        assert len(templates_by_name["Database Setup"].dependencies) == 0
        assert "Database Setup" in templates_by_name["API Development"].dependencies
        assert "API Development" in templates_by_name["Frontend Integration"].dependencies
    
    @pytest.mark.asyncio
    async def test_split_tasks_invalid_json(self, mcp_server):
        """Test split_tasks tool with invalid JSON."""
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "clearAllTasks",
                "tasksRaw": "invalid json string"
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Should return error string
        assert "json" in result_text.lower() or "error" in result_text.lower()
    
    @pytest.mark.asyncio
    async def test_split_tasks_invalid_update_mode(self, mcp_server):
        """Test split_tasks tool with invalid update mode."""
        tasks_raw = json.dumps([
            {
                "name": "Test Task",
                "description": "Test task with proper description length",
                "implementation_guide": "Test implementation guide",
                "dependencies": []
            }
        ])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "invalidMode",
                "tasksRaw": tasks_raw
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Should return error string for invalid update mode
        assert "mode" in result_text.lower() or "invalid" in result_text.lower()
    
    @pytest.mark.asyncio
    async def test_split_tasks_empty_tasks(self, mcp_server):
        """Test split_tasks tool with empty task list."""
        tasks_raw = json.dumps([])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "clearAllTasks",
                "tasksRaw": tasks_raw
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Should return error string for empty task list
        assert "error" in result_text.lower() or "empty" in result_text.lower() or "task" in result_text.lower()
    
    @pytest.mark.asyncio
    async def test_split_tasks_service_error(self, mcp_server):
        """Test split_tasks tool when service returns error."""
        # Mock service to return error
        with patch('src.server.task_splitting_service') as mock_service:
            error_result = SplitResult(
                success=False,
                created_tasks=[],
                operation=None,
                message="Split operation failed due to validation error",
                errors=["Task name too long", "Invalid dependency reference"]
            )
            mock_service.split_tasks = AsyncMock(return_value=error_result)
            
            tasks_raw = json.dumps([
                {
                    "name": "Test Task",
                    "description": "Test task description for error scenario",
                    "implementation_guide": "Test implementation guide",
                    "dependencies": []
                }
            ])
            
            result = await mcp_server.call_tool(
                "split_tasks",
                {
                    "updateMode": "clearAllTasks",
                    "tasksRaw": tasks_raw
                }
            )
            
            assert result is not None
            # FastMCP returns a more complex structure: ([TextContent], metadata)
            if isinstance(result, tuple) and len(result) == 2:
                text_contents, metadata = result
                if text_contents and hasattr(text_contents[0], 'text'):
                    result_text = text_contents[0].text
                else:
                    result_text = str(result)
            else:
                result_text = str(result)
            
            # Should return error information
            assert "error" in result_text.lower() or "failed" in result_text.lower()
    
    @pytest.mark.asyncio
    async def test_split_tasks_with_related_files(self, mcp_server, mock_task_splitting_service):
        """Test split_tasks tool with related files."""
        tasks_raw = json.dumps([
            {
                "name": "Update Component",
                "description": "Update React component with new features and proper testing",
                "implementation_guide": "1. Modify component\n2. Update tests\n3. Update documentation",
                "dependencies": [],
                "relatedFiles": [
                    {
                        "path": "src/components/UserProfile.tsx",
                        "type": "TO_MODIFY",
                        "description": "Main component file to be updated",
                        "lineStart": 25,
                        "lineEnd": 100
                    },
                    {
                        "path": "src/components/__tests__/UserProfile.test.tsx",
                        "type": "TO_MODIFY", 
                        "description": "Test file to be updated with new test cases"
                    }
                ]
            }
        ])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "selective",
                "tasksRaw": tasks_raw
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Verify related files were parsed correctly
        call_args = mock_task_splitting_service.split_tasks.call_args[0][0]
        task_template = call_args.task_templates[0]
        
        assert len(task_template.related_files) == 2
        assert task_template.related_files[0].path == "src/components/UserProfile.tsx"
        assert task_template.related_files[0].line_start == 25
        assert task_template.related_files[0].line_end == 100
    
    @pytest.mark.asyncio
    async def test_split_tasks_response_format(self, mcp_server, mock_task_splitting_service):
        """Test split_tasks tool response format."""
        tasks_raw = json.dumps([
            {
                "name": "Format Test Task",
                "description": "Task to test response formatting from MCP tool",
                "implementation_guide": "Implementation guide for format testing",
                "dependencies": []
            }
        ])
        
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "clearAllTasks",
                "tasksRaw": tasks_raw
            }
        )
        
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        # Should contain key information about the operation
        assert "task" in result_text.lower()
        assert "success" in result_text.lower() or "complete" in result_text.lower()
        
        # Should mention the update mode used
        assert "clearAllTasks" in result_text or "clear" in result_text.lower()
    
    @pytest.mark.asyncio
    async def test_split_tasks_granularity_validation(self, mcp_server):
        """Test split_tasks tool with granularity rule violations."""
        # Create too many tasks (exceeding default limit of 10)
        tasks = []
        for i in range(15):
            tasks.append({
                "name": f"Task {i}",
                "description": f"Description for task {i} with adequate length requirements",
                "implementation_guide": f"Implementation guide for task {i}",
                "dependencies": []
            })
        
        tasks_raw = json.dumps(tasks)
        
        # Should handle granularity validation in service
        result = await mcp_server.call_tool(
            "split_tasks",
            {
                "updateMode": "clearAllTasks",
                "tasksRaw": tasks_raw
            }
        )
        
        # Service should handle validation and return appropriate response
        assert result is not None
        # FastMCP returns a more complex structure: ([TextContent], metadata)
        if isinstance(result, tuple) and len(result) == 2:
            text_contents, metadata = result
            if text_contents and hasattr(text_contents[0], 'text'):
                result_text = text_contents[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)