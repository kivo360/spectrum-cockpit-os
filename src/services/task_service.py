"""Task management service layer coordinating graph and table storage."""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.models.task import GraphEdge, GraphNode, Task, TaskDependency, TaskStatus
from src.storage.abstractions import AbstractGraphStorage, AbstractTableStorage


class TaskService:
    """High-level service for task management using both graph and table storage."""
    
    def __init__(
        self, 
        table_storage: AbstractTableStorage[Task],
        graph_storage: AbstractGraphStorage
    ) -> None:
        """Initialize task service with storage backends.
        
        Args:
            table_storage: Table storage for task metadata
            graph_storage: Graph storage for dependency relationships
        """
        self.table_storage = table_storage
        self.graph_storage = graph_storage
    
    async def create_task(self, task: Task) -> Task:
        """Create a new task in both table and graph storage.
        
        Args:
            task: Task to create
            
        Returns:
            Created task
            
        Raises:
            ValueError: If task already exists or has invalid dependencies
        """
        # Create task in table storage first
        created_task = await self.table_storage.create(task)
        
        # Create corresponding graph node
        graph_node = GraphNode(
            id=task.id,
            data={
                "name": task.name,
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                "complexity": task.complexity.value if task.complexity and hasattr(task.complexity, 'value') else (task.complexity if task.complexity else None),
                "category": task.category
            }
        )
        
        node_created = await self.graph_storage.add_node(graph_node)
        if not node_created:
            # Rollback table creation if graph node creation fails
            await self.table_storage.delete(task.id)
            raise ValueError(f"Failed to create graph node for task {task.id}")
        
        # Add dependency edges if specified
        if task.dependencies:
            await self._add_task_dependencies(task.id, task.dependencies)
        
        return created_task
    
    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get task by ID from table storage.
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            Task if found, None otherwise
        """
        return await self.table_storage.get_by_id(task_id)
    
    async def update_task(self, task: Task) -> Task:
        """Update existing task in both storages.
        
        Args:
            task: Updated task
            
        Returns:
            Updated task
            
        Raises:
            ValueError: If task doesn't exist
        """
        # Update task in table storage
        updated_task = await self.table_storage.update(task)
        
        # Update graph node data
        graph_node = GraphNode(
            id=task.id,
            data={
                "name": task.name,
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                "complexity": task.complexity.value if task.complexity and hasattr(task.complexity, 'value') else (task.complexity if task.complexity else None),
                "category": task.category
            }
        )
        
        # Remove existing node and add updated one
        await self.graph_storage.remove_node(task.id)
        await self.graph_storage.add_node(graph_node)
        
        # Update dependencies
        if task.dependencies:
            await self._add_task_dependencies(task.id, task.dependencies)
        
        return updated_task
    
    async def delete_task(self, task_id: UUID) -> bool:
        """Delete task from both storages.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        # Delete from table storage first
        table_deleted = await self.table_storage.delete(task_id)
        
        # Delete from graph storage (this also removes edges)
        graph_deleted = await self.graph_storage.remove_node(task_id)
        
        return table_deleted and graph_deleted
    
    async def list_tasks(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """List tasks with optional filters.
        
        Args:
            filters: Query filters for table storage
            limit: Maximum number of tasks to return
            
        Returns:
            List of matching tasks
        """
        if filters:
            tasks = await self.table_storage.query(filters)
        else:
            tasks = await self.table_storage.list_all()
        
        if limit:
            tasks = tasks[:limit]
        
        return tasks
    
    async def get_task_dependencies(self, task_id: UUID) -> List[Task]:
        """Get tasks that this task depends on.
        
        Args:
            task_id: Task ID to get dependencies for
            
        Returns:
            List of dependency tasks
        """
        dependency_ids = await self.graph_storage.get_dependencies(task_id)
        
        # Fetch task details from table storage
        tasks = []
        for dep_id in dependency_ids:
            task = await self.table_storage.get_by_id(dep_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def get_task_dependents(self, task_id: UUID) -> List[Task]:
        """Get tasks that depend on this task.
        
        Args:
            task_id: Task ID to get dependents for
            
        Returns:
            List of dependent tasks
        """
        dependent_ids = await self.graph_storage.get_dependents(task_id)
        
        # Fetch task details from table storage
        tasks = []
        for dep_id in dependent_ids:
            task = await self.table_storage.get_by_id(dep_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def add_dependency(self, task_id: UUID, depends_on_id: UUID) -> bool:
        """Add dependency relationship between tasks.
        
        Args:
            task_id: Task that depends on another
            depends_on_id: Task that is depended upon
            
        Returns:
            True if dependency added, False if would create cycle
            
        Raises:
            ValueError: If either task doesn't exist
        """
        # Verify both tasks exist
        task = await self.table_storage.get_by_id(task_id)
        depends_on_task = await self.table_storage.get_by_id(depends_on_id)
        
        if not task:
            raise ValueError(f"Task {task_id} not found")
        if not depends_on_task:
            raise ValueError(f"Dependency task {depends_on_id} not found")
        
        # Add edge to graph storage
        edge = GraphEdge(from_id=task_id, to_id=depends_on_id)
        edge_added = await self.graph_storage.add_edge(edge)
        
        if edge_added:
            # Update task's dependency list in table storage
            task.dependencies.append(TaskDependency(task_id=depends_on_id))
            await self.table_storage.update(task)
        
        return edge_added
    
    async def remove_dependency(self, task_id: UUID, depends_on_id: UUID) -> bool:
        """Remove dependency relationship between tasks.
        
        Args:
            task_id: Task that depends on another
            depends_on_id: Task that is depended upon
            
        Returns:
            True if dependency removed, False if not found
        """
        # Remove edge from graph storage
        edge = GraphEdge(from_id=task_id, to_id=depends_on_id)
        edge_removed = await self.graph_storage.remove_edge(edge)
        
        if edge_removed:
            # Update task's dependency list in table storage
            task = await self.table_storage.get_by_id(task_id)
            if task:
                task.dependencies = [
                    dep for dep in task.dependencies 
                    if dep.task_id != depends_on_id
                ]
                await self.table_storage.update(task)
        
        return edge_removed
    
    async def get_execution_order(self) -> List[Task]:
        """Get tasks in topological execution order.
        
        Returns:
            List of tasks in dependency execution order
            
        Raises:
            ValueError: If circular dependencies detected
        """
        # Get topological sort from graph storage
        sorted_ids = await self.graph_storage.topological_sort()
        
        # Reverse the order for proper execution sequence
        # Since our edges go task -> dependency, we need to reverse
        # the topological sort to get dependency -> task execution order
        sorted_ids.reverse()
        
        # Fetch task details from table storage
        tasks = []
        for task_id in sorted_ids:
            task = await self.table_storage.get_by_id(task_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def detect_circular_dependencies(self) -> bool:
        """Check if task dependency graph has cycles.
        
        Returns:
            True if circular dependencies exist, False otherwise
        """
        return await self.graph_storage.has_cycle()
    
    async def get_ready_tasks(
        self, 
        status_filter: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Get tasks that are ready to be worked on (no pending dependencies).
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            List of ready tasks
        """
        # Get all tasks
        filters = {"status": status_filter.value if hasattr(status_filter, 'value') else status_filter} if status_filter else {}
        all_tasks = await self.list_tasks(filters)
        
        ready_tasks = []
        for task in all_tasks:
            # Check if all dependencies are completed
            dependencies = await self.get_task_dependencies(task.id)
            
            if not dependencies:  # No dependencies
                ready_tasks.append(task)
            else:
                # Check if all dependencies are completed
                all_deps_complete = all(
                    dep.status == TaskStatus.COMPLETED 
                    for dep in dependencies
                )
                if all_deps_complete:
                    ready_tasks.append(task)
        
        return ready_tasks
    
    async def get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics.
        
        Returns:
            Dictionary with project metrics
        """
        # Get basic task statistics from table storage
        table_stats = await self.table_storage.get_statistics()
        
        # Get graph metrics
        graph_metrics = await self.graph_storage.get_graph_metrics()
        
        # Get status breakdown
        status_counts = {}
        for status in TaskStatus:
            tasks = await self.list_tasks({"status": status.value})
            status_counts[status.value] = len(tasks)
        
        # Get ready tasks count
        ready_tasks = await self.get_ready_tasks()
        
        return {
            "total_tasks": table_stats["total_count"],
            "earliest_created": table_stats.get("earliest_created"),
            "latest_created": table_stats.get("latest_created"),
            "latest_updated": table_stats.get("latest_updated"),
            "graph_nodes": graph_metrics["node_count"],
            "graph_edges": graph_metrics["edge_count"],
            "has_cycles": await self.detect_circular_dependencies(),
            "status_breakdown": status_counts,
            "ready_tasks_count": len(ready_tasks)
        }
    
    async def bulk_create_tasks(self, tasks: List[Task]) -> List[Task]:
        """Create multiple tasks efficiently.
        
        Args:
            tasks: List of tasks to create
            
        Returns:
            List of created tasks
            
        Raises:
            ValueError: If any task creation fails
        """
        # Create all tasks in table storage first
        created_tasks = await self.table_storage.bulk_insert(tasks)
        
        # Create corresponding graph nodes
        for task in created_tasks:
            graph_node = GraphNode(
                id=task.id,
                data={
                    "name": task.name,
                    "status": task.status.value if hasattr(task.status, 'value') else task.status,
                    "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                    "complexity": task.complexity.value if task.complexity and hasattr(task.complexity, 'value') else (task.complexity if task.complexity else None),
                    "category": task.category
                }
            )
            
            node_created = await self.graph_storage.add_node(graph_node)
            if not node_created:
                raise ValueError(f"Failed to create graph node for task {task.id}")
        
        # Add dependencies for all tasks
        for task in created_tasks:
            if task.dependencies:
                await self._add_task_dependencies(task.id, task.dependencies)
        
        return created_tasks
    
    async def clear_all_data(self) -> None:
        """Clear all tasks from both storages. Use with caution!"""
        await self.table_storage.clear()
        await self.graph_storage.clear()
    
    async def _add_task_dependencies(
        self, 
        task_id: UUID, 
        dependencies: List[TaskDependency]
    ) -> None:
        """Internal method to add dependencies to graph storage.
        
        Args:
            task_id: Task ID that has dependencies
            dependencies: List of dependencies to add
        """
        for dep in dependencies:
            # Verify dependency task exists
            dep_task = await self.table_storage.get_by_id(dep.task_id)
            if not dep_task:
                raise ValueError(f"Dependency task {dep.task_id} not found")
            
            # Create edge in graph storage
            edge = GraphEdge(from_id=task_id, to_id=dep.task_id)
            edge_added = await self.graph_storage.add_edge(edge)
            
            if not edge_added:
                raise ValueError(
                    f"Failed to add dependency: {task_id} -> {dep.task_id} "
                    "(would create cycle)"
                )