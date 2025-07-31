#!/usr/bin/env python3
"""Example usage of the storage abstractions with NetworkX and DuckDB."""

import asyncio
from uuid import uuid4

from src.models.task import (
    ComplexityLevel,
    GraphEdge,
    GraphNode,
    Priority,
    RelatedFile,
    RelatedFileType,
    Task,
    TaskDependency,
    TaskStatus,
)
from src.storage.duckdb_table import DuckDBTableStorage
from src.storage.networkx_graph import NetworkXGraphStorage


async def demonstrate_graph_storage():
    """Demonstrate NetworkX graph storage capabilities."""
    print("🌐 NetworkX Graph Storage Demo")
    print("=" * 50)
    
    # Create graph storage
    graph_storage = NetworkXGraphStorage()
    
    # Create some tasks
    task1_id = uuid4()
    task2_id = uuid4()
    task3_id = uuid4()
    
    # Add nodes to graph
    node1 = GraphNode(id=task1_id, data={"name": "Setup Database"})
    node2 = GraphNode(id=task2_id, data={"name": "Create API"})
    node3 = GraphNode(id=task3_id, data={"name": "Build Frontend"})
    
    await graph_storage.add_node(node1)
    await graph_storage.add_node(node2)
    await graph_storage.add_node(node3)
    
    print(f"✅ Added {len(await graph_storage.get_all_nodes())} nodes")
    
    # Create dependencies: API depends on Database, Frontend depends on API
    edge1 = GraphEdge(from_id=task2_id, to_id=task1_id)  # API -> Database
    edge2 = GraphEdge(from_id=task3_id, to_id=task2_id)  # Frontend -> API
    
    await graph_storage.add_edge(edge1)
    await graph_storage.add_edge(edge2)
    
    print(f"✅ Added {len(await graph_storage.get_all_edges())} dependency edges")
    
    # Test cycle prevention
    cycle_edge = GraphEdge(from_id=task1_id, to_id=task3_id)  # Would create cycle
    result = await graph_storage.add_edge(cycle_edge)
    print(f"🚫 Cycle prevention works: {not result}")
    
    # Get topological sort (execution order)
    sorted_tasks = await graph_storage.topological_sort()
    print(f"📋 Execution order: {[str(t)[:8] + '...' for t in sorted_tasks]}")
    
    # Test advanced features
    path = await graph_storage.get_shortest_path(task3_id, task1_id)
    print(f"🛣️  Dependency path length: {len(path) if path else 0}")
    
    # Graph metrics
    metrics = await graph_storage.get_graph_metrics()
    print(f"📊 Graph metrics: {metrics['node_count']} nodes, {metrics['edge_count']} edges")
    
    print()


async def demonstrate_table_storage():
    """Demonstrate DuckDB table storage capabilities."""
    print("🗄️  DuckDB Table Storage Demo")
    print("=" * 50)
    
    # Create table storage
    table_storage = DuckDBTableStorage(Task, database_path=":memory:")
    
    # Create sample tasks
    tasks = [
        Task(
            name="Setup Database Schema",
            description="Create database tables and indexes for the application",
            implementation_guide="Use PostgreSQL with proper indexing strategy",
            status=TaskStatus.COMPLETED,
            priority=Priority.P0,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=8,
            category="Backend",
            related_files=[
                RelatedFile(
                    path="src/database/schema.sql",
                    type=RelatedFileType.CREATE,
                    description="Database schema definition"
                )
            ]
        ),
        Task(
            name="Build REST API",
            description="Implement RESTful API endpoints for task management",
            implementation_guide="Use FastAPI with async/await patterns",
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.P1,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=16,
            category="Backend",
            dependencies=[],  # Will add after database task is created
            related_files=[
                RelatedFile(
                    path="src/api/routes.py",
                    type=RelatedFileType.CREATE,
                    description="API route definitions"
                ),
                RelatedFile(
                    path="src/api/models.py",
                    type=RelatedFileType.TO_MODIFY,
                    description="API data models",
                    line_start=1,
                    line_end=50
                )
            ]
        ),
        Task(
            name="Create React Frontend",
            description="Build responsive frontend interface using React",
            implementation_guide="Use React 19 with TypeScript and Tailwind CSS",
            status=TaskStatus.PENDING,
            priority=Priority.P1,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=20,
            category="Frontend",
            related_files=[
                RelatedFile(
                    path="frontend/src/App.tsx",
                    type=RelatedFileType.CREATE,
                    description="Main React application component"
                )
            ]
        )
    ]
    
    # Bulk insert tasks
    created_tasks = await table_storage.bulk_insert(tasks)
    print(f"✅ Created {len(created_tasks)} tasks")
    
    # Add dependencies after creation
    api_task = created_tasks[1]
    api_task.dependencies = [TaskDependency(task_id=created_tasks[0].id)]
    await table_storage.update(api_task)
    
    frontend_task = created_tasks[2]
    frontend_task.dependencies = [TaskDependency(task_id=api_task.id)]
    await table_storage.update(frontend_task)
    print("✅ Added task dependencies")
    
    # Query by status
    pending_tasks = await table_storage.query({"status": TaskStatus.PENDING.value})
    print(f"📋 Pending tasks: {len(pending_tasks)}")
    
    in_progress_tasks = await table_storage.query({"status": TaskStatus.IN_PROGRESS.value})
    print(f"🔄 In progress tasks: {len(in_progress_tasks)}")
    
    # Query by priority
    p1_tasks = await table_storage.query({"priority": Priority.P1.value})
    print(f"🔥 High priority (P1) tasks: {len(p1_tasks)}")
    
    # Query by category
    backend_tasks = await table_storage.query({"category": "Backend"})
    print(f"⚙️  Backend tasks: {len(backend_tasks)}")
    
    # Get statistics
    stats = await table_storage.get_statistics()
    print(f"📊 Total tasks: {stats['total_count']}")
    
    # Demonstrate individual retrieval
    task = await table_storage.get_by_id(created_tasks[1].id)
    if task:
        print(f"🔍 Retrieved task: '{task.name}' with {len(task.related_files)} related files")
    
    # Close connection
    table_storage.close()
    print()


async def demonstrate_integration():
    """Demonstrate how graph and table storage work together."""
    print("🔗 Integrated Storage Demo")
    print("=" * 50)
    
    # Create both storage types
    graph_storage = NetworkXGraphStorage()
    table_storage = DuckDBTableStorage(Task, database_path=":memory:")
    
    # Create tasks in table storage first
    task1 = Task(
        name="Database Setup",
        description="Set up PostgreSQL database",
        implementation_guide="Install and configure PostgreSQL",
        complexity=ComplexityLevel.SIMPLE,
        estimated_hours=4
    )
    task2 = Task(
        name="API Development",
        description="Build REST API endpoints",
        implementation_guide="Use FastAPI framework",
        complexity=ComplexityLevel.MODERATE,
        estimated_hours=8
    )
    task3 = Task(
        name="Frontend Integration",
        description="Connect frontend to API",
        implementation_guide="Use Axios for HTTP requests",
        complexity=ComplexityLevel.MODERATE,
        estimated_hours=6
    )
    
    # Store tasks in table
    await table_storage.create(task1)
    await table_storage.create(task2)
    await table_storage.create(task3)
    
    # Create corresponding graph nodes
    node1 = GraphNode(id=task1.id, data={"name": task1.name, "complexity": task1.complexity.value})
    node2 = GraphNode(id=task2.id, data={"name": task2.name, "complexity": task2.complexity.value})
    node3 = GraphNode(id=task3.id, data={"name": task3.name, "complexity": task3.complexity.value})
    
    await graph_storage.add_node(node1)
    await graph_storage.add_node(node2)
    await graph_storage.add_node(node3)
    
    # Create dependency graph
    await graph_storage.add_edge(GraphEdge(from_id=task2.id, to_id=task1.id))  # API depends on DB
    await graph_storage.add_edge(GraphEdge(from_id=task3.id, to_id=task2.id))  # Frontend depends on API
    
    # Get execution order from graph
    execution_order = await graph_storage.topological_sort()
    print(f"📋 Execution order determined by dependency graph:")
    
    for i, task_id in enumerate(execution_order, 1):
        task = await table_storage.get_by_id(task_id)
        if task:
            dependencies = await graph_storage.get_dependencies(task_id)
            print(f"  {i}. {task.name} ({task.complexity.value}, {task.estimated_hours}h)")
            if dependencies:
                print(f"     Depends on: {len(dependencies)} task(s)")
    
    # Calculate total project duration (sum of hours on critical path)
    total_hours = sum(
        (await table_storage.get_by_id(task_id)).estimated_hours or 0
        for task_id in execution_order
    )
    print(f"⏱️  Total estimated duration: {total_hours} hours")
    
    # Cleanup
    table_storage.close()
    print()


async def main():
    """Run all demonstrations."""
    print("🚀 Advanced MCP Task Manager - Storage Demonstration")
    print("=" * 70)
    print()
    
    await demonstrate_graph_storage()
    await demonstrate_table_storage()
    await demonstrate_integration()
    
    print("✨ Storage system demonstration complete!")
    print()
    print("Key achievements:")
    print("• ✅ Pydantic v2 models with comprehensive validation")
    print("• ✅ Abstract storage interfaces with TDD approach")
    print("• ✅ NetworkX graph storage with cycle prevention")
    print("• ✅ DuckDB table storage with JSON querying")
    print("• ✅ Integrated dependency management system")
    print("• ✅ Production-ready error handling and type safety")


if __name__ == "__main__":
    asyncio.run(main())