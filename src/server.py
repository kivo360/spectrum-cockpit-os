"""FastMCP Server for Advanced Task Management."""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ValidationError

from src.models.task import (
    ComplexityLevel,
    Priority,
    Task,
    TaskStatus,
    RelatedFile,
    RelatedFileType,
    TaskDependency,
)
from src.services.task_service import TaskService
from src.services.task_splitting_service import TaskSplittingService
from src.storage.duckdb_table import DuckDBTableStorage
from src.storage.networkx_graph import NetworkXGraphStorage
from src.schemas.splitting_schemas import RawTaskSplitSchema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
task_service: Optional[TaskService] = None
task_splitting_service: Optional[TaskSplittingService] = None


class TaskCreationRequest(BaseModel):
    """Request model for creating a new task."""
    name: str
    description: str
    implementation_guide: str
    verification_criteria: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.PENDING
    priority: Optional[Priority] = Priority.P2
    complexity: Optional[ComplexityLevel] = None
    estimated_hours: Optional[int] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    dependencies: List[str] = []  # Task IDs or names
    related_files: List[Dict[str, Any]] = []


class TaskUpdateRequest(BaseModel):
    """Request model for updating an existing task."""
    task_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    implementation_guide: Optional[str] = None
    verification_criteria: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    complexity: Optional[ComplexityLevel] = None
    estimated_hours: Optional[int] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class TaskQueryRequest(BaseModel):
    """Request model for querying tasks."""
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    category: Optional[str] = None
    complexity: Optional[ComplexityLevel] = None
    limit: Optional[int] = None


async def initialize_service() -> TaskService:
    """Initialize the task service with storage backends."""
    global task_service, task_splitting_service
    
    # Get database path from environment or use default
    db_path = os.getenv("TASK_DB_PATH", "tasks.db")
    
    # Initialize storage backends
    table_storage = DuckDBTableStorage(Task, database_path=db_path)
    graph_storage = NetworkXGraphStorage()
    
    # Create services
    task_service = TaskService(table_storage, graph_storage)
    task_splitting_service = TaskSplittingService(task_service)
    
    logger.info(f"Task service initialized with database: {db_path}")
    logger.info("Task splitting service initialized")
    return task_service


def format_task_summary(task: Task) -> str:
    """Format task for display."""
    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.IN_PROGRESS: "🔄", 
        TaskStatus.COMPLETED: "✅",
        TaskStatus.BLOCKED: "🚫"
    }
    
    priority_emoji = {
        Priority.P0: "🔴",
        Priority.P1: "🟡", 
        Priority.P2: "🟢",
        Priority.P3: "🔵"
    }
    
    return (
        f"{status_emoji.get(task.status, '❓')} {priority_emoji.get(task.priority, '⚪')} "
        f"**{task.name}** ({str(task.id)[:8]}...)\n"
        f"└─ {task.description[:100]}{'...' if len(task.description) > 100 else ''}"
    )


def format_task_detailed(task: Task) -> str:
    """Format task with full details."""
    details = [
        f"# 📋 Task: {task.name}",
        f"**ID:** `{task.id}`",
        f"**Status:** {task.status.value}",
        f"**Priority:** {task.priority.value}",
        "",
        f"## Description",
        task.description,
        "",
        f"## Implementation Guide", 
        task.implementation_guide,
    ]
    
    if task.verification_criteria:
        details.extend([
            "",
            f"## Verification Criteria",
            task.verification_criteria
        ])
    
    if task.complexity:
        details.append(f"**Complexity:** {task.complexity.value}")
    
    if task.estimated_hours:
        details.append(f"**Estimated Hours:** {task.estimated_hours}")
    
    if task.category:
        details.append(f"**Category:** {task.category}")
    
    if task.dependencies:
        details.extend([
            "",
            f"## Dependencies ({len(task.dependencies)})",
            *[f"- {dep.task_id}" for dep in task.dependencies]
        ])
    
    if task.related_files:
        details.extend([
            "",
            f"## Related Files ({len(task.related_files)})",
            *[f"- **{file.type.value}**: `{file.path}` - {file.description}" 
              for file in task.related_files]
        ])
    
    if task.notes:
        details.extend([
            "",
            f"## Notes",
            task.notes
        ])
    
    details.extend([
        "",
        f"**Created:** {task.created_at.isoformat()}",
        f"**Updated:** {task.updated_at.isoformat()}"
    ])
    
    return "\n".join(details)


async def resolve_task_references(task_ids_or_names: List[str]) -> List[UUID]:
    """Resolve task IDs or names to UUIDs."""
    resolved_ids = []
    
    for ref in task_ids_or_names:
        try:
            # Try to parse as UUID first
            task_id = UUID(ref)
            task = await task_service.get_task(task_id)
            if task:
                resolved_ids.append(task_id)
            else:
                logger.warning(f"Task with ID {task_id} not found")
        except ValueError:
            # Not a UUID, try to find by name
            tasks = await task_service.list_tasks({"name": ref})
            if tasks:
                resolved_ids.append(tasks[0].id)
            else:
                logger.warning(f"Task with name '{ref}' not found")
    
    return resolved_ids


# Initialize the FastMCP server
def create_mcp() -> FastMCP:
    """Create and configure the FastMCP server."""
    mcp = FastMCP("Advanced Task Manager")
    
    @mcp.resource("task://statistics")
    async def get_statistics() -> str:
        """Get comprehensive project statistics."""
        stats = await task_service.get_project_statistics()
        return json.dumps(stats, indent=2, default=str)
    
    @mcp.resource("task://execution-order")
    async def get_execution_order() -> str:
        """Get tasks in dependency execution order."""
        tasks = await task_service.get_execution_order()
        if not tasks:
            return "No tasks found."
        
        content = ["# 📋 Task Execution Order", ""]
        for i, task in enumerate(tasks, 1):
            content.append(f"{i}. {format_task_summary(task)}")
        
        return "\n".join(content)
    
    @mcp.resource("task://ready-tasks")
    async def get_ready_tasks() -> str:
        """Get tasks ready to work on."""
        ready_tasks = await task_service.get_ready_tasks()
        if not ready_tasks:
            return "No ready tasks found."
        
        content = ["# ⚡ Ready Tasks", ""]
        for task in ready_tasks:
            content.append(format_task_summary(task))
            content.append("")
        
        return "\n".join(content)
    
    @mcp.tool()
    async def create_task(
        name: str,
        description: str,
        implementation_guide: str,
        verification_criteria: str = None,
        status: str = "PENDING",
        priority: str = "P2",
        complexity: str = None,
        estimated_hours: int = None,
        category: str = None,
        notes: str = None,
        dependencies: list = None,
        related_files: list = None
    ) -> str:
        """Create a new task with comprehensive metadata."""
        try:
            # Convert dependencies from strings to TaskDependency objects
            task_dependencies = []
            if dependencies:
                dep_ids = await resolve_task_references(dependencies)
                task_dependencies = [TaskDependency(task_id=dep_id) for dep_id in dep_ids]
            
            # Convert related files
            task_related_files = []
            if related_files:
                for file_data in related_files:
                    task_related_files.append(RelatedFile(**file_data))
            
            # Create task
            task = Task(
                name=name,
                description=description,
                implementation_guide=implementation_guide,
                verification_criteria=verification_criteria,
                status=TaskStatus(status),
                priority=Priority(priority),
                complexity=ComplexityLevel(complexity) if complexity else None,
                estimated_hours=estimated_hours,
                category=category,
                notes=notes,
                dependencies=task_dependencies,
                related_files=task_related_files
            )
            
            created_task = await task_service.create_task(task)
            
            return f"✅ **Task Created Successfully**\n\n{format_task_detailed(created_task)}"
        
        except Exception as e:
            return f"❌ Error creating task: {e}"
    
    @mcp.tool()
    async def get_task(task_id: str) -> str:
        """Get detailed information about a specific task."""
        try:
            try:
                task_uuid = UUID(task_id)
            except ValueError:
                # Try to find by name
                tasks = await task_service.list_tasks({"name": task_id})
                if not tasks:
                    return f"❌ Task '{task_id}' not found"
                task_uuid = tasks[0].id
            
            task = await task_service.get_task(task_uuid)
            if not task:
                return f"❌ Task with ID {task_uuid} not found"
            
            return format_task_detailed(task)
        
        except Exception as e:
            return f"❌ Error retrieving task: {e}"
    
    @mcp.tool()
    async def list_tasks(
        status: str = None,
        priority: str = None,
        category: str = None,
        complexity: str = None,
        limit: int = None
    ) -> str:
        """List tasks with optional filters."""
        try:
            # Build filters
            filters = {}
            if status:
                filters["status"] = status
            if priority:
                filters["priority"] = priority
            if category:
                filters["category"] = category
            if complexity:
                filters["complexity"] = complexity
            
            tasks = await task_service.list_tasks(filters, limit)
            
            if not tasks:
                return "No tasks found matching criteria."
            
            content = [f"# 📋 Found {len(tasks)} Task(s)", ""]
            for task in tasks:
                content.append(format_task_summary(task))
                content.append("")
            
            return "\n".join(content)
        
        except Exception as e:
            return f"❌ Error listing tasks: {e}"
    
    @mcp.tool()
    async def update_task(
        task_id: str,
        name: str = None,
        description: str = None,
        implementation_guide: str = None,
        verification_criteria: str = None,
        status: str = None,
        priority: str = None,
        complexity: str = None,
        estimated_hours: int = None,
        category: str = None,
        notes: str = None
    ) -> str:
        """Update an existing task."""
        try:
            task_uuid = UUID(task_id)
            
            # Get existing task
            existing_task = await task_service.get_task(task_uuid)
            if not existing_task:
                return f"❌ Task with ID {task_uuid} not found"
            
            # Update fields that were provided
            if name is not None:
                existing_task.name = name
            if description is not None:
                existing_task.description = description
            if implementation_guide is not None:
                existing_task.implementation_guide = implementation_guide
            if verification_criteria is not None:
                existing_task.verification_criteria = verification_criteria
            if status is not None:
                existing_task.status = TaskStatus(status)
            if priority is not None:
                existing_task.priority = Priority(priority)
            if complexity is not None:
                existing_task.complexity = ComplexityLevel(complexity)
            if estimated_hours is not None:
                existing_task.estimated_hours = estimated_hours
            if category is not None:
                existing_task.category = category
            if notes is not None:
                existing_task.notes = notes
            
            # Update timestamp
            existing_task.update_timestamp()
            
            updated_task = await task_service.update_task(existing_task)
            
            return f"✅ **Task Updated Successfully**\n\n{format_task_detailed(updated_task)}"
        
        except Exception as e:
            return f"❌ Error updating task: {e}"
    
    @mcp.tool()
    async def delete_task(task_id: str) -> str:
        """Delete a task from both graph and table storage."""
        try:
            task_uuid = UUID(task_id)
            deleted = await task_service.delete_task(task_uuid)
            
            if deleted:
                return f"✅ Task {task_uuid} deleted successfully"
            else:
                return f"❌ Task {task_uuid} not found"
        
        except Exception as e:
            return f"❌ Error deleting task: {e}"
    
    @mcp.tool()
    async def add_dependency(task_id: str, depends_on_id: str) -> str:
        """Add dependency relationship between tasks."""
        try:
            task_uuid = UUID(task_id)
            depends_on_uuid = UUID(depends_on_id)
            
            added = await task_service.add_dependency(task_uuid, depends_on_uuid)
            
            if added:
                return f"✅ Dependency added: {task_id} → {depends_on_id}"
            else:
                return "❌ Failed to add dependency (would create cycle)"
        
        except Exception as e:
            return f"❌ Error adding dependency: {e}"
    
    @mcp.tool()
    async def get_execution_order() -> str:
        """Get all tasks in dependency execution order."""
        try:
            tasks = await task_service.get_execution_order()
            
            if not tasks:
                return "No tasks found."
            
            content = ["# 📋 Task Execution Order", ""]
            for i, task in enumerate(tasks, 1):
                content.append(f"{i}. {format_task_summary(task)}")
            
            return "\n".join(content)
        
        except Exception as e:
            return f"❌ Error getting execution order: {e}"
    
    @mcp.tool()
    async def get_ready_tasks(status_filter: str = None) -> str:
        """Get tasks ready to work on (no pending dependencies)."""
        try:
            status = TaskStatus(status_filter) if status_filter else None
            ready_tasks = await task_service.get_ready_tasks(status)
            
            if not ready_tasks:
                return "No ready tasks found."
            
            content = ["# ⚡ Ready Tasks", ""]
            for task in ready_tasks:
                content.append(format_task_summary(task))
                content.append("")
            
            return "\n".join(content)
        
        except Exception as e:
            return f"❌ Error getting ready tasks: {e}"
    
    @mcp.tool()
    async def get_statistics() -> str:
        """Get comprehensive project statistics."""
        try:
            stats = await task_service.get_project_statistics()
            
            content = [
                "# 📊 Project Statistics",
                "",
                f"**Total Tasks:** {stats['total_tasks']}",
                f"**Graph Nodes:** {stats['graph_nodes']}",
                f"**Graph Edges:** {stats['graph_edges']}",
                f"**Has Cycles:** {'⚠️ Yes' if stats['has_cycles'] else '✅ No'}",
                f"**Ready Tasks:** {stats['ready_tasks_count']}",
                "",
                "## Status Breakdown",
                ""
            ]
            
            for status, count in stats["status_breakdown"].items():
                content.append(f"- **{status}:** {count}")
            
            if stats.get("earliest_created"):
                content.extend([
                    "",
                    f"**Earliest Created:** {stats['earliest_created']}",
                    f"**Latest Created:** {stats['latest_created']}",
                    f"**Latest Updated:** {stats['latest_updated']}"
                ])
            
            return "\n".join(content)
        
        except Exception as e:
            return f"❌ Error getting statistics: {e}"
    
    @mcp.tool()
    async def detect_cycles() -> str:
        """Check for circular dependencies in task graph."""
        try:
            has_cycles = await task_service.detect_circular_dependencies()
            
            if has_cycles:
                return "⚠️ Circular dependencies detected in task graph!"
            else:
                return "✅ No circular dependencies found."
        
        except Exception as e:
            return f"❌ Error detecting cycles: {e}"
    
    @mcp.tool()
    async def bulk_create_tasks(tasks: list) -> str:
        """Create multiple tasks efficiently."""
        try:
            # Create Task objects
            task_objects = []
            for task_data in tasks:
                task = Task(
                    name=task_data["name"],
                    description=task_data["description"], 
                    implementation_guide=task_data["implementation_guide"],
                    priority=Priority(task_data.get("priority", "P2")),
                    complexity=ComplexityLevel(task_data["complexity"]) if task_data.get("complexity") else None,
                    estimated_hours=task_data.get("estimated_hours"),
                    category=task_data.get("category")
                )
                task_objects.append(task)
            
            created_tasks = await task_service.bulk_create_tasks(task_objects)
            
            content = [f"✅ **{len(created_tasks)} Tasks Created Successfully**", ""]
            for task in created_tasks:
                content.append(format_task_summary(task))
                content.append("")
            
            return "\n".join(content)
        
        except Exception as e:
            return f"❌ Error bulk creating tasks: {e}"
    
    @mcp.tool()
    async def split_tasks(
        updateMode: str = "clearAllTasks",
        tasksRaw = None,  # Can be str or list - FastMCP auto-parses JSON
        globalAnalysisResult: str = None
    ) -> str:
        """
        Split complex tasks into manageable subtasks with intelligent decomposition.
        
        Supports four update modes:
        - clearAllTasks: Remove all existing tasks and create new ones (default)
        - append: Add new tasks to existing ones
        - selective: Update matching tasks by name, create new ones
        - overwrite: Remove unfinished tasks, keep completed ones, add new ones
        
        Args:
            updateMode: Task update strategy
            tasksRaw: JSON string containing array of task templates
            globalAnalysisResult: Overall project goal applicable to all tasks
        """
        try:
            # Validate input parameters
            if not tasksRaw:
                return "❌ Error: tasksRaw parameter is required"
            
            # Handle both string (JSON) and already parsed list inputs from FastMCP
            if isinstance(tasksRaw, str):
                # JSON string - need to parse
                try:
                    tasks_data = json.loads(tasksRaw)
                except json.JSONDecodeError as e:
                    return f"❌ Invalid JSON in tasksRaw: {e}"
                
                # Validate string input using schema
                raw_request_data = {
                    "updateMode": updateMode,
                    "tasksRaw": tasksRaw, 
                    "globalAnalysisResult": globalAnalysisResult
                }
                
                try:
                    RawTaskSplitSchema.model_validate(raw_request_data)
                except ValidationError as e:
                    return f"❌ Validation Error: {e}"
                    
            elif isinstance(tasksRaw, list):
                # Already parsed by FastMCP
                tasks_data = tasksRaw
                
                # For pre-parsed data, skip schema validation since it requires string
                if not tasks_data:
                    return "❌ Error: tasksRaw cannot be empty"
                    
            else:
                return f"❌ Error: tasksRaw must be a JSON string or list, got {type(tasksRaw)}"
            
            # Convert to internal models
            from src.models.task_splitting import TaskSplitRequest, TaskTemplate, UpdateMode
            from src.models.task import RelatedFile, RelatedFileType
            
            # Convert updateMode string to enum
            try:
                update_mode = UpdateMode(updateMode)
            except ValueError:
                return f"❌ Invalid updateMode: {updateMode}. Must be one of: append, overwrite, selective, clearAllTasks"
            
            # Convert task data to TaskTemplate objects
            task_templates = []
            for task_data in tasks_data:
                try:
                    # Handle related files if present
                    related_files = []
                    if "relatedFiles" in task_data:
                        for file_data in task_data["relatedFiles"]:
                            related_file = RelatedFile(
                                path=file_data["path"],
                                type=RelatedFileType(file_data["type"]),
                                description=file_data["description"],
                                line_start=file_data.get("lineStart"),
                                line_end=file_data.get("lineEnd")
                            )
                            related_files.append(related_file)
                    
                    template = TaskTemplate(
                        name=task_data["name"],
                        description=task_data["description"],
                        implementation_guide=task_data["implementation_guide"],
                        dependencies=task_data.get("dependencies", []),
                        notes=task_data.get("notes"),
                        related_files=related_files,
                        verification_criteria=task_data.get("verificationCriteria")
                    )
                    task_templates.append(template)
                    
                except (KeyError, ValueError) as e:
                    return f"❌ Invalid task data: {e}"
            
            # Create split request
            split_request = TaskSplitRequest(
                update_mode=update_mode,
                task_templates=task_templates,
                global_analysis_result=globalAnalysisResult
            )
            
            # Execute the split operation
            result = await task_splitting_service.split_tasks(split_request)
            
            # Format response
            if result.success:
                content = [f"✅ **Task Split Operation Successful**", ""]
                content.append(f"**Mode**: {result.operation.update_mode.value}")
                content.append(f"**Tasks Before**: {result.operation.tasks_before_count}")
                content.append(f"**Tasks After**: {result.operation.tasks_after_count}")
                content.append(f"**Tasks Added**: {result.operation.tasks_added}")
                content.append(f"**Tasks Updated**: {result.operation.tasks_updated}")
                content.append(f"**Tasks Removed**: {result.operation.tasks_removed}")
                content.append("")
                content.append(f"**Message**: {result.message}")
                
                if result.created_tasks:
                    content.append("")
                    content.append("**Created/Updated Tasks:**")
                    for task in result.created_tasks:
                        content.append(format_task_summary(task))
                        content.append("")
                
                return "\n".join(content)
            else:
                content = [f"❌ **Task Split Operation Failed**", ""]
                content.append(f"**Message**: {result.message}")
                if result.errors:
                    content.append("")
                    content.append("**Errors:**")
                    for error in result.errors:
                        content.append(f"- {error}")
                
                return "\n".join(content)
        
        except Exception as e:
            logger.error(f"Error in split_tasks tool: {e}")
            return f"❌ Unexpected error during task splitting: {e}"
    
    return mcp


async def main():
    """Main entry point for the FastMCP server."""
    global task_service
    
    # Initialize the task service
    task_service = await initialize_service()
    
    # Create and run the FastMCP server
    mcp = create_mcp()
    
    # Run the server based on environment
    transport = os.getenv("TRANSPORT", "stdio")
    if transport == "sse":
        await mcp.run_sse_async()
    else:
        await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())