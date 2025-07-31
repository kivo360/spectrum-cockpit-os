"""Command-line interface for the Advanced Task Manager using Typer."""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from typing_extensions import Annotated

from src.models.task import ComplexityLevel, Priority, Task, TaskStatus, RelatedFile, RelatedFileType
from src.services.task_service import TaskService
from src.storage.duckdb_table import DuckDBTableStorage
from src.storage.networkx_graph import NetworkXGraphStorage

# Rich console for beautiful output
console = Console()

# Typer app instance
app = typer.Typer(
    name="task-manager",
    help="Advanced Task Manager CLI - Graph and Table Storage System.",
    rich_markup_mode="rich",
    add_completion=False
)

# Global service instance
service: Optional[TaskService] = None


async def initialize_service(db_path: str = "tasks.db") -> TaskService:
    """Initialize the task service."""
    table_storage = DuckDBTableStorage(Task, database_path=db_path)
    graph_storage = NetworkXGraphStorage()
    return TaskService(table_storage, graph_storage)


def format_task_table(tasks: List[Task]) -> Table:
    """Format tasks as a rich table."""
    table = Table(title="📋 Tasks")
    
    table.add_column("ID", style="dim", width=8)
    table.add_column("Name", style="bold", min_width=20)
    table.add_column("Status", justify="center", width=12)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Complexity", justify="center", width=10)
    table.add_column("Hours", justify="right", width=6)
    table.add_column("Category", width=12)
    
    status_colors = {
        TaskStatus.PENDING: "yellow",
        TaskStatus.IN_PROGRESS: "blue",
        TaskStatus.COMPLETED: "green", 
        TaskStatus.BLOCKED: "red"
    }
    
    priority_colors = {
        Priority.P0: "red",
        Priority.P1: "orange3",
        Priority.P2: "yellow",
        Priority.P3: "blue"
    }
    
    for task in tasks:
        status_color = status_colors.get(task.status, "white")
        priority_color = priority_colors.get(task.priority, "white")
        
        table.add_row(
            str(task.id)[:8] + "...",
            task.name,
            f"[{status_color}]{task.status.value}[/{status_color}]",
            f"[{priority_color}]{task.priority.value}[/{priority_color}]",
            task.complexity.value if task.complexity else "-",
            str(task.estimated_hours) if task.estimated_hours else "-",
            task.category or "-"
        )
    
    return table


def format_task_details(task: Task) -> Panel:
    """Format task details as a rich panel."""
    content = []
    
    # Basic info
    content.append(f"[bold]ID:[/bold] {task.id}")
    content.append(f"[bold]Status:[/bold] {task.status.value}")
    content.append(f"[bold]Priority:[/bold] {task.priority.value}")
    
    if task.complexity:
        content.append(f"[bold]Complexity:[/bold] {task.complexity.value}")
    if task.estimated_hours:
        content.append(f"[bold]Estimated Hours:[/bold] {task.estimated_hours}")
    if task.category:
        content.append(f"[bold]Category:[/bold] {task.category}")
    
    content.append("")
    content.append(f"[bold]Description:[/bold]")
    content.append(task.description)
    
    content.append("")
    content.append(f"[bold]Implementation Guide:[/bold]")
    content.append(task.implementation_guide)
    
    if task.verification_criteria:
        content.append("")
        content.append(f"[bold]Verification Criteria:[/bold]")
        content.append(task.verification_criteria)
    
    if task.dependencies:
        content.append("")
        content.append(f"[bold]Dependencies ({len(task.dependencies)}):[/bold]")
        for dep in task.dependencies:
            content.append(f"  • {dep.task_id}")
    
    if task.related_files:
        content.append("")
        content.append(f"[bold]Related Files ({len(task.related_files)}):[/bold]")
        for file in task.related_files:
            line_info = ""
            if file.line_start and file.line_end:
                line_info = f" (lines {file.line_start}-{file.line_end})"
            content.append(f"  • [{file.type.value}] {file.path}{line_info}")
            content.append(f"    {file.description}")
    
    if task.notes:
        content.append("")
        content.append(f"[bold]Notes:[/bold]")
        content.append(task.notes)
    
    content.append("")
    content.append(f"[dim]Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}")
    content.append(f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M')}[/dim]")
    
    return Panel(
        "\n".join(content),
        title=f"📋 {task.name}",
        title_align="left",
        border_style="blue"
    )


async def ensure_service_initialized(db_path: str = "tasks.db"):
    """Ensure the global service is initialized."""
    global service
    if service is None:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Initializing task service...", total=None)
                service = await initialize_service(db_path)
                progress.update(task, description="✅ Task service ready!")
            
            console.print(f"[green]Connected to database:[/green] {db_path}")
            
        except Exception as e:
            console.print(f"[red]Failed to initialize service:[/red] {e}")
            raise typer.Exit(1)


@app.command()
def create(
    name: Annotated[str, typer.Option("--name", "-n", prompt=True, help="Task name")],
    description: Annotated[str, typer.Option("--description", "-d", prompt=True, help="Task description")],
    implementation_guide: Annotated[str, typer.Option("--implementation-guide", "-i", prompt=True, help="Implementation guide")],
    priority: Annotated[Priority, typer.Option("--priority", "-p", help="Task priority")] = Priority.P2,
    complexity: Annotated[Optional[ComplexityLevel], typer.Option("--complexity", "-c", help="Task complexity")] = None,
    estimated_hours: Annotated[Optional[int], typer.Option("--hours", "-h", help="Estimated hours")] = None,
    category: Annotated[Optional[str], typer.Option("--category", help="Task category")] = None,
    notes: Annotated[Optional[str], typer.Option("--notes", help="Additional notes")] = None,
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Create a new task."""
    async def _create():
        await ensure_service_initialized(db_path)
        
        try:
            task_data = {
                'name': name,
                'description': description,
                'implementation_guide': implementation_guide,
                'priority': priority,
            }
            
            if complexity:
                task_data['complexity'] = complexity
            if estimated_hours:
                task_data['estimated_hours'] = estimated_hours
            if category:
                task_data['category'] = category
            if notes:
                task_data['notes'] = notes
            
            task = Task(**task_data)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Creating task...", total=None)
                created_task = await service.create_task(task)
                progress.update(task_progress, description="✅ Task created!")
            
            console.print(format_task_details(created_task))
            
        except Exception as e:
            console.print(f"[red]Error creating task:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_create())


@app.command()
def list(
    status: Annotated[Optional[TaskStatus], typer.Option("--status", "-s", help="Filter by status")] = None,
    priority: Annotated[Optional[Priority], typer.Option("--priority", "-p", help="Filter by priority")] = None,
    category: Annotated[Optional[str], typer.Option("--category", "-c", help="Filter by category")] = None,
    complexity: Annotated[Optional[ComplexityLevel], typer.Option("--complexity", help="Filter by complexity")] = None,
    limit: Annotated[Optional[int], typer.Option("--limit", "-l", help="Limit number of results")] = None,
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """List tasks with optional filters."""
    async def _list():
        await ensure_service_initialized(db_path)
        
        try:
            filters = {}
            if status:
                filters['status'] = status.value
            if priority:
                filters['priority'] = priority.value
            if category:
                filters['category'] = category
            if complexity:
                filters['complexity'] = complexity.value
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Loading tasks...", total=None)
                tasks = await service.list_tasks(filters, limit)
                progress.update(task_progress, description="✅ Tasks loaded!")
            
            if not tasks:
                console.print("[yellow]No tasks found matching criteria.[/yellow]")
                return
            
            console.print(format_task_table(tasks))
            console.print(f"\n[dim]Found {len(tasks)} task(s)[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error listing tasks:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_list())


@app.command()
def show(
    task_id: Annotated[str, typer.Argument(help="Task ID or name")],
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Show detailed information about a task."""
    async def _show():
        await ensure_service_initialized(db_path)
        
        try:
            # Try to parse as UUID or search by name
            try:
                task_uuid = UUID(task_id)
                task = await service.get_task(task_uuid)
            except ValueError:
                # Search by name
                tasks = await service.list_tasks({'name': task_id})
                task = tasks[0] if tasks else None
            
            if not task:
                console.print(f"[red]Task '{task_id}' not found.[/red]")
                raise typer.Exit(1)
            
            console.print(format_task_details(task))
            
        except Exception as e:
            console.print(f"[red]Error showing task:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_show())


@app.command()
def update(
    task_id: Annotated[str, typer.Argument(help="Task ID or name")],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="New task name")] = None,
    status: Annotated[Optional[TaskStatus], typer.Option("--status", "-s", help="New status")] = None,
    priority: Annotated[Optional[Priority], typer.Option("--priority", "-p", help="New priority")] = None,
    complexity: Annotated[Optional[ComplexityLevel], typer.Option("--complexity", "-c", help="New complexity")] = None,
    estimated_hours: Annotated[Optional[int], typer.Option("--hours", "-h", help="New estimated hours")] = None,
    category: Annotated[Optional[str], typer.Option("--category", help="New category")] = None,
    notes: Annotated[Optional[str], typer.Option("--notes", help="New notes")] = None,
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Update an existing task."""
    async def _update():
        await ensure_service_initialized(db_path)
        
        try:
            # Get existing task
            try:
                task_uuid = UUID(task_id)
                task = await service.get_task(task_uuid)
            except ValueError:
                tasks = await service.list_tasks({'name': task_id})
                task = tasks[0] if tasks else None
            
            if not task:
                console.print(f"[red]Task '{task_id}' not found.[/red]")
                raise typer.Exit(1)
            
            # Update fields
            if name:
                task.name = name
            if status:
                task.status = status
            if priority:
                task.priority = priority
            if complexity:
                task.complexity = complexity
            if estimated_hours is not None:
                task.estimated_hours = estimated_hours
            if category:
                task.category = category
            if notes:
                task.notes = notes
            
            # Update timestamp
            task.update_timestamp()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Updating task...", total=None)
                updated_task = await service.update_task(task)
                progress.update(task_progress, description="✅ Task updated!")
            
            console.print(format_task_details(updated_task))
            
        except Exception as e:
            console.print(f"[red]Error updating task:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_update())


@app.command()
def add_dependency(
    task_id: Annotated[str, typer.Argument(help="Task ID")],
    depends_on_id: Annotated[str, typer.Argument(help="Dependency task ID")],
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Add a dependency relationship between tasks."""
    async def _add_dependency():
        await ensure_service_initialized(db_path)
        
        try:
            task_uuid = UUID(task_id)
            depends_on_uuid = UUID(depends_on_id)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Adding dependency...", total=None)
                added = await service.add_dependency(task_uuid, depends_on_uuid)
                progress.update(task_progress, description="✅ Dependency processed!")
            
            if added:
                console.print(f"[green]✅ Dependency added:[/green] {task_id} → {depends_on_id}")
            else:
                console.print(f"[red]❌ Failed to add dependency (would create cycle)[/red]")
            
        except ValueError as e:
            console.print(f"[red]Invalid UUID format:[/red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error adding dependency:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_add_dependency())


@app.command()
def execution_order(
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Show tasks in dependency execution order."""
    async def _execution_order():
        await ensure_service_initialized(db_path)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Computing execution order...", total=None)
                tasks = await service.get_execution_order()
                progress.update(task_progress, description="✅ Order computed!")
            
            if not tasks:
                console.print("[yellow]No tasks found.[/yellow]")
                return
            
            console.print(Panel.fit("📋 Task Execution Order", style="bold blue"))
            
            for i, task in enumerate(tasks, 1):
                status_emoji = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.IN_PROGRESS: "🔄",
                    TaskStatus.COMPLETED: "✅", 
                    TaskStatus.BLOCKED: "🚫"
                }.get(task.status, "❓")
                
                console.print(f"{i:2d}. {status_emoji} [bold]{task.name}[/bold] ({task.priority.value})")
                console.print(f"    [dim]{task.description[:80]}{'...' if len(task.description) > 80 else ''}[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error getting execution order:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_execution_order())


@app.command()
def ready(
    status: Annotated[Optional[TaskStatus], typer.Option("--status", "-s", help="Filter by status")] = None,
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Show tasks ready to be worked on (no pending dependencies)."""
    async def _ready():
        await ensure_service_initialized(db_path)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Finding ready tasks...", total=None)
                ready_tasks = await service.get_ready_tasks(status)
                progress.update(task_progress, description="✅ Ready tasks found!")
            
            if not ready_tasks:
                console.print("[yellow]No ready tasks found.[/yellow]")
                return
            
            console.print(Panel.fit("⚡ Ready Tasks", style="bold green"))
            console.print(format_task_table(ready_tasks))
            
        except Exception as e:
            console.print(f"[red]Error finding ready tasks:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_ready())


@app.command()
def stats(
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Show comprehensive project statistics."""
    async def _stats():
        await ensure_service_initialized(db_path)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Computing statistics...", total=None)
                statistics = await service.get_project_statistics()
                progress.update(task_progress, description="✅ Statistics computed!")
            
            # Create statistics display
            stats_content = []
            
            stats_content.append(f"[bold]Total Tasks:[/bold] {statistics['total_tasks']}")
            stats_content.append(f"[bold]Graph Nodes:[/bold] {statistics['graph_nodes']}")
            stats_content.append(f"[bold]Graph Edges:[/bold] {statistics['graph_edges']}")
            stats_content.append(f"[bold]Has Cycles:[/bold] {'⚠️ Yes' if statistics['has_cycles'] else '✅ No'}")
            stats_content.append(f"[bold]Ready Tasks:[/bold] {statistics['ready_tasks_count']}")
            
            stats_content.append("")
            stats_content.append("[bold]Status Breakdown:[/bold]")
            
            for status, count in statistics['status_breakdown'].items():
                color = {
                    'COMPLETED': 'green',
                    'IN_PROGRESS': 'blue', 
                    'PENDING': 'yellow',
                    'BLOCKED': 'red'
                }.get(status, 'white')
                
                stats_content.append(f"  [{color}]{status}[/{color}]: {count}")
            
            if statistics.get('earliest_created'):
                stats_content.append("")
                stats_content.append(f"[dim]Earliest Created: {statistics['earliest_created']}")
                stats_content.append(f"Latest Created: {statistics['latest_created']}")
                stats_content.append(f"Latest Updated: {statistics['latest_updated']}[/dim]")
            
            console.print(Panel(
                "\n".join(stats_content),
                title="📊 Project Statistics",
                title_align="left",
                border_style="cyan"
            ))
            
        except Exception as e:
            console.print(f"[red]Error getting statistics:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_stats())


@app.command()
def detect_cycles(
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Check for circular dependencies in the task graph."""
    async def _detect_cycles():
        await ensure_service_initialized(db_path)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Detecting cycles...", total=None)
                has_cycles = await service.detect_circular_dependencies()
                progress.update(task_progress, description="✅ Cycle detection complete!")
            
            if has_cycles:
                console.print(Panel(
                    "⚠️ Circular dependencies detected in task graph!\n\nThis means some tasks depend on each other in a way that creates an impossible execution order.",
                    title="Circular Dependencies Found",
                    title_align="left",
                    border_style="red"
                ))
            else:
                console.print(Panel(
                    "✅ No circular dependencies found.\n\nTask graph is valid and can be executed in proper dependency order.",
                    title="Graph Validation Successful",
                    title_align="left",
                    border_style="green"
                ))
            
        except Exception as e:
            console.print(f"[red]Error detecting cycles:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_detect_cycles())


@app.command()
def import_tasks(
    file_path: Annotated[Path, typer.Argument(help="JSON file to import from", exists=True)],
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Import tasks from a JSON file."""
    async def _import_tasks():
        await ensure_service_initialized(db_path)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            tasks = []
            for task_data in data.get('tasks', []):
                # Convert string enums to enum instances
                if 'priority' in task_data:
                    task_data['priority'] = Priority(task_data['priority'])
                if 'status' in task_data:
                    task_data['status'] = TaskStatus(task_data['status'])
                if 'complexity' in task_data:
                    task_data['complexity'] = ComplexityLevel(task_data['complexity'])
                
                # Convert related files
                if 'related_files' in task_data:
                    related_files = []
                    for file_data in task_data['related_files']:
                        if 'type' in file_data:
                            file_data['type'] = RelatedFileType(file_data['type'])
                        related_files.append(RelatedFile(**file_data))
                    task_data['related_files'] = related_files
                
                tasks.append(Task(**task_data))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task(f"Importing {len(tasks)} tasks...", total=None)
                created_tasks = await service.bulk_create_tasks(tasks)
                progress.update(task_progress, description="✅ Tasks imported!")
            
            console.print(f"[green]✅ Successfully imported {len(created_tasks)} tasks from {file_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error importing tasks:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_import_tasks())


@app.command()
def export_tasks(
    file_path: Annotated[Path, typer.Argument(help="JSON file to export to")],
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Export all tasks to a JSON file."""
    async def _export_tasks():
        await ensure_service_initialized(db_path)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Exporting tasks...", total=None)
                tasks = await service.list_tasks()
                progress.update(task_progress, description="✅ Tasks loaded!")
            
            # Convert tasks to JSON-serializable format
            tasks_data = []
            for task in tasks:
                task_dict = task.model_dump()
                # Convert UUID to string
                task_dict['id'] = str(task_dict['id'])
                # Convert dependency UUIDs to strings
                for dep in task_dict.get('dependencies', []):
                    dep['task_id'] = str(dep['task_id'])
                tasks_data.append(task_dict)
            
            export_data = {
                'tasks': tasks_data,
                'exported_at': tasks[0].created_at.isoformat() if tasks else None,
                'total_count': len(tasks)
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            console.print(f"[green]✅ Successfully exported {len(tasks)} tasks to {file_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error exporting tasks:[/red] {e}")
            raise typer.Exit(1)
    
    asyncio.run(_export_tasks())


@app.command()
def interactive(
    db_path: Annotated[str, typer.Option("--db-path", help="Database file path")] = "tasks.db"
):
    """Start interactive task management session."""
    async def _interactive():
        await ensure_service_initialized(db_path)
        
        console.print(Panel.fit("🚀 Interactive Task Manager", style="bold magenta"))
        console.print("[dim]Type 'help' for available commands, 'quit' to exit[/dim]\n")
        
        while True:
            try:
                command = Prompt.ask("[bold cyan]task-manager[/bold cyan]", default="help")
                
                if command.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye! 👋[/yellow]")
                    break
                
                elif command.lower() == 'help':
                    help_text = """
[bold]Available Commands:[/bold]

• [cyan]stats[/cyan]         - Show project statistics
• [cyan]list[/cyan]          - List all tasks
• [cyan]ready[/cyan]         - Show ready tasks
• [cyan]order[/cyan]         - Show execution order
• [cyan]cycles[/cyan]        - Check for circular dependencies
• [cyan]create[/cyan]        - Create a new task (guided)
• [cyan]quit[/cyan]          - Exit interactive mode

[dim]Tip: Use the CLI commands for more advanced operations[/dim]
                    """
                    console.print(Panel(help_text.strip(), title="Help", border_style="blue"))
                
                elif command.lower() == 'stats':
                    await _stats()
                
                elif command.lower() == 'list':
                    tasks = await service.list_tasks()
                    if tasks:
                        console.print(format_task_table(tasks))
                        console.print(f"\n[dim]Found {len(tasks)} task(s)[/dim]")
                    else:
                        console.print("[yellow]No tasks found.[/yellow]")
                
                elif command.lower() == 'ready':
                    ready_tasks = await service.get_ready_tasks()
                    if ready_tasks:
                        console.print(Panel.fit("⚡ Ready Tasks", style="bold green"))
                        console.print(format_task_table(ready_tasks))
                    else:
                        console.print("[yellow]No ready tasks found.[/yellow]")
                
                elif command.lower() == 'order':
                    tasks = await service.get_execution_order()
                    if tasks:
                        console.print(Panel.fit("📋 Task Execution Order", style="bold blue"))
                        for i, task in enumerate(tasks, 1):
                            status_emoji = {
                                TaskStatus.PENDING: "⏳",
                                TaskStatus.IN_PROGRESS: "🔄",
                                TaskStatus.COMPLETED: "✅", 
                                TaskStatus.BLOCKED: "🚫"
                            }.get(task.status, "❓")
                            console.print(f"{i:2d}. {status_emoji} [bold]{task.name}[/bold] ({task.priority.value})")
                            console.print(f"    [dim]{task.description[:80]}{'...' if len(task.description) > 80 else ''}[/dim]")
                    else:
                        console.print("[yellow]No tasks found.[/yellow]")
                
                elif command.lower() == 'cycles':
                    has_cycles = await service.detect_circular_dependencies()
                    if has_cycles:
                        console.print(Panel(
                            "⚠️ Circular dependencies detected in task graph!",
                            title="Circular Dependencies Found",
                            title_align="left",
                            border_style="red"
                        ))
                    else:
                        console.print(Panel(
                            "✅ No circular dependencies found.",
                            title="Graph Validation Successful",
                            title_align="left",
                            border_style="green"
                        ))
                
                elif command.lower() == 'create':
                    console.print("[yellow]Guided task creation:[/yellow]\n")
                    
                    name = Prompt.ask("Task name")
                    description = Prompt.ask("Description")
                    impl_guide = Prompt.ask("Implementation guide")
                    priority = Priority(Prompt.ask("Priority", choices=['P0', 'P1', 'P2', 'P3'], default='P2'))
                    
                    # Optional fields
                    complexity = None
                    if Confirm.ask("Add complexity level?", default=False):
                        complexity = ComplexityLevel(Prompt.ask("Complexity", choices=['SIMPLE', 'MODERATE', 'COMPLEX', 'EPIC']))
                    
                    hours = None
                    if Confirm.ask("Add estimated hours?", default=False):
                        hours = int(Prompt.ask("Estimated hours", default="0"))
                        hours = hours if hours > 0 else None
                    
                    category = None
                    if Confirm.ask("Add category?", default=False):
                        category = Prompt.ask("Category")
                    
                    # Create the task
                    try:
                        task_data = {
                            'name': name,
                            'description': description,
                            'implementation_guide': impl_guide,
                            'priority': priority
                        }
                        
                        if complexity:
                            task_data['complexity'] = complexity
                        if hours:
                            task_data['estimated_hours'] = hours
                        if category:
                            task_data['category'] = category
                        
                        task = Task(**task_data)
                        created_task = await service.create_task(task)
                        
                        console.print(f"\n[green]✅ Task created successfully![/green]")
                        console.print(format_task_details(created_task))
                        
                    except Exception as e:
                        console.print(f"[red]Error creating task: {e}[/red]")
                
                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    console.print("[dim]Type 'help' for available commands[/dim]")
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit gracefully[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(_interactive())


if __name__ == '__main__':
    app()