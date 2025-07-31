#!/usr/bin/env python3
"""Complete system demonstration of the Advanced Task Manager.

This script demonstrates all the features of the task management system:
- Creating tasks with comprehensive metadata
- Building dependency graphs
- Querying and filtering tasks
- Managing project workflows
- Analyzing project statistics
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.columns import Columns

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
from src.storage.duckdb_table import DuckDBTableStorage
from src.storage.networkx_graph import NetworkXGraphStorage

console = Console()


async def create_demo_project(service: TaskService) -> dict:
    """Create a comprehensive demo project with realistic tasks."""
    console.print(Panel.fit("🏗️ Creating Demo Project: Web Application", style="bold blue"))
    
    # Phase 1: Infrastructure and Setup
    infrastructure_tasks = [
        Task(
            name="Project Setup and Configuration",
            description="Initialize project structure, set up development environment, and configure CI/CD pipeline",
            implementation_guide=(
                "1. Create Git repository with proper .gitignore and README\n"
                "2. Set up Python virtual environment with requirements.txt\n"
                "3. Configure pre-commit hooks for code quality\n"
                "4. Set up GitHub Actions for automated testing and deployment\n"
                "5. Create development and production environment configurations"
            ),
            verification_criteria=(
                "- Repository has proper structure and documentation\n"
                "- CI/CD pipeline runs successfully\n"
                "- Development environment can be set up from scratch\n"
                "- All code quality checks pass"
            ),
            priority=Priority.P0,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=6,
            category="DevOps",
            notes="Foundation task - must be completed first",
            related_files=[
                RelatedFile(
                    path="README.md",
                    type=RelatedFileType.CREATE,
                    description="Project documentation and setup instructions"
                ),
                RelatedFile(
                    path=".github/workflows/ci.yml",
                    type=RelatedFileType.CREATE,
                    description="GitHub Actions CI/CD configuration"
                ),
                RelatedFile(
                    path="requirements.txt",
                    type=RelatedFileType.CREATE,
                    description="Python dependencies specification"
                )
            ]
        ),
        
        Task(
            name="Database Schema Design and Setup",
            description="Design and implement PostgreSQL database schema with proper indexing and constraints",
            implementation_guide=(
                "1. Analyze application requirements and design ERD\n"
                "2. Create database schema with tables, relationships, and constraints\n"
                "3. Add appropriate indexes for query optimization\n"
                "4. Set up database migrations system\n"
                "5. Create sample data for development and testing"
            ),
            verification_criteria=(
                "- Database schema supports all application features\n"
                "- All foreign key relationships are properly defined\n"
                "- Indexes are optimized for expected query patterns\n"
                "- Migration system works correctly\n"
                "- Sample data covers all major use cases"
            ),
            priority=Priority.P0,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=12,
            category="Database",
            related_files=[
                RelatedFile(
                    path="database/schema.sql",
                    type=RelatedFileType.CREATE,
                    description="Database schema definition"
                ),
                RelatedFile(
                    path="database/migrations/",
                    type=RelatedFileType.CREATE,
                    description="Database migration scripts directory"
                ),
                RelatedFile(
                    path="database/sample_data.sql",
                    type=RelatedFileType.CREATE,
                    description="Sample data for development"
                )
            ]
        ),
    ]
    
    # Phase 2: Backend Development
    backend_tasks = [
        Task(
            name="Authentication and Authorization System",
            description="Implement JWT-based authentication with role-based access control and session management",
            implementation_guide=(
                "1. Set up JWT token generation and validation\n"
                "2. Create user registration and login endpoints\n"
                "3. Implement role-based access control (RBAC)\n"
                "4. Add password reset and email verification\n"
                "5. Create session management and logout functionality\n"
                "6. Add rate limiting and security middleware"
            ),
            verification_criteria=(
                "- Users can register, login, and logout successfully\n"
                "- JWT tokens are generated and validated correctly\n"
                "- Role-based permissions work as expected\n"
                "- Password reset flow works end-to-end\n"
                "- Security measures prevent common attacks\n"
                "- API endpoints are properly protected"
            ),
            priority=Priority.P1,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=16,
            category="Backend",
            related_files=[
                RelatedFile(
                    path="src/auth/models.py",
                    type=RelatedFileType.CREATE,
                    description="Authentication data models"
                ),
                RelatedFile(
                    path="src/auth/handlers.py",
                    type=RelatedFileType.CREATE,
                    description="Authentication request handlers"
                ),
                RelatedFile(
                    path="src/middleware/auth.py",
                    type=RelatedFileType.CREATE,
                    description="Authentication middleware"
                ),
                RelatedFile(
                    path="tests/test_auth.py",
                    type=RelatedFileType.CREATE,
                    description="Authentication system tests"
                )
            ]
        ),
        
        Task(
            name="RESTful API Framework and Core Endpoints",
            description="Build FastAPI-based REST API with proper error handling, validation, and documentation",
            implementation_guide=(
                "1. Set up FastAPI application with proper configuration\n"
                "2. Create base API structure with versioning\n"
                "3. Implement request/response models with Pydantic\n"
                "4. Add comprehensive error handling and logging\n"
                "5. Create CRUD endpoints for core resources\n"
                "6. Generate interactive API documentation\n"
                "7. Add request validation and sanitization"
            ),
            verification_criteria=(
                "- API follows RESTful conventions and best practices\n"
                "- All endpoints have proper request/response validation\n"
                "- Error handling provides meaningful messages\n"
                "- API documentation is complete and accurate\n"
                "- Logging captures all important events\n"
                "- API versioning strategy is implemented"
            ),
            priority=Priority.P1,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=14,
            category="Backend",
            related_files=[
                RelatedFile(
                    path="src/api/main.py",
                    type=RelatedFileType.CREATE,
                    description="FastAPI application setup"
                ),
                RelatedFile(
                    path="src/api/routes/",
                    type=RelatedFileType.CREATE,
                    description="API route definitions directory"
                ),
                RelatedFile(
                    path="src/api/models.py",
                    type=RelatedFileType.CREATE,
                    description="API request/response models"
                ),
                RelatedFile(
                    path="src/api/exceptions.py",
                    type=RelatedFileType.CREATE,
                    description="Custom exception handlers"
                )
            ]
        ),
    ]
    
    # Phase 3: Frontend Development
    frontend_tasks = [
        Task(
            name="React Application Setup and Architecture",
            description="Set up modern React application with TypeScript, routing, and state management",
            implementation_guide=(
                "1. Create React app with TypeScript and modern tooling\n"
                "2. Set up React Router for client-side routing\n"
                "3. Configure state management with Redux Toolkit\n"
                "4. Set up component library and design system\n"
                "5. Configure build pipeline and optimization\n"
                "6. Add development tools and debugging setup"
            ),
            verification_criteria=(
                "- React application builds and runs without errors\n"
                "- TypeScript configuration is properly set up\n"
                "- Routing works correctly for all planned pages\n"
                "- State management handles complex application state\n"
                "- Component library provides consistent UI elements\n"
                "- Build pipeline produces optimized production bundle"
            ),
            priority=Priority.P1,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=8,
            category="Frontend",
            related_files=[
                RelatedFile(
                    path="frontend/src/App.tsx",
                    type=RelatedFileType.CREATE,
                    description="Main React application component"
                ),
                RelatedFile(
                    path="frontend/src/store/",
                    type=RelatedFileType.CREATE,
                    description="Redux store configuration"
                ),
                RelatedFile(
                    path="frontend/src/components/",
                    type=RelatedFileType.CREATE,
                    description="Reusable UI components"
                ),
                RelatedFile(
                    path="frontend/src/pages/",
                    type=RelatedFileType.CREATE,
                    description="Application page components"
                )
            ]
        ),
        
        Task(
            name="User Interface Components and Styling",
            description="Create responsive UI components with modern styling and accessibility features",
            implementation_guide=(
                "1. Design and implement core UI components\n"
                "2. Set up responsive design with CSS Grid and Flexbox\n"
                "3. Add dark/light theme support\n"
                "4. Implement accessibility features (ARIA, keyboard navigation)\n"
                "5. Create loading states and error boundaries\n"
                "6. Add animations and micro-interactions\n"
                "7. Optimize for mobile and tablet devices"
            ),
            verification_criteria=(
                "- All components are responsive across device sizes\n"
                "- Accessibility standards are met (WCAG 2.1 AA)\n"
                "- Theme switching works seamlessly\n"
                "- Loading and error states provide good UX\n"
                "- Animations enhance user experience\n"
                "- Components are properly tested and documented"
            ),
            priority=Priority.P2,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=6,
            category="Frontend",
            related_files=[
                RelatedFile(
                    path="frontend/src/styles/",
                    type=RelatedFileType.CREATE,
                    description="CSS/SCSS styling files"
                ),
                RelatedFile(
                    path="frontend/src/components/ui/",
                    type=RelatedFileType.CREATE,
                    description="UI component library"
                ),
                RelatedFile(
                    path="frontend/src/themes/",
                    type=RelatedFileType.CREATE,
                    description="Theme configuration files"
                )
            ]
        ),
    ]
    
    # Phase 4: Testing and Quality Assurance
    testing_tasks = [
        Task(
            name="Backend Testing Suite",
            description="Implement comprehensive testing for backend API with unit, integration, and e2e tests",
            implementation_guide=(
                "1. Set up pytest testing framework with fixtures\n"
                "2. Create unit tests for all business logic\n"
                "3. Add integration tests for API endpoints\n"
                "4. Implement database testing with test containers\n"
                "5. Add authentication and authorization tests\n"
                "6. Create performance and load tests\n"
                "7. Set up test coverage reporting"
            ),
            verification_criteria=(
                "- Test coverage is above 90% for critical code paths\n"
                "- All API endpoints have comprehensive tests\n"
                "- Database operations are tested with real database\n"
                "- Authentication flows are thoroughly tested\n"
                "- Performance tests validate response times\n"
                "- Tests run reliably in CI/CD pipeline"
            ),
            priority=Priority.P1,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=8,
            category="Testing",
            related_files=[
                RelatedFile(
                    path="tests/unit/",
                    type=RelatedFileType.CREATE,
                    description="Unit test directory"
                ),
                RelatedFile(
                    path="tests/integration/",
                    type=RelatedFileType.CREATE,
                    description="Integration test directory"
                ),
                RelatedFile(
                    path="tests/conftest.py",
                    type=RelatedFileType.CREATE,
                    description="Pytest configuration and fixtures"
                )
            ]
        ),
        
        Task(
            name="Frontend Testing and Quality Assurance",
            description="Implement frontend testing with Jest, React Testing Library, and Cypress",
            implementation_guide=(
                "1. Set up Jest and React Testing Library\n"
                "2. Create unit tests for React components\n"
                "3. Add integration tests for user workflows\n"
                "4. Set up Cypress for end-to-end testing\n"
                "5. Add visual regression testing\n"
                "6. Create accessibility testing automation\n"
                "7. Set up test coverage and quality gates"
            ),
            verification_criteria=(
                "- All components have unit tests with good coverage\n"
                "- User workflows are tested end-to-end\n"
                "- Visual regression tests catch UI changes\n"
                "- Accessibility tests validate WCAG compliance\n"
                "- Tests run reliably in CI/CD pipeline\n"
                "- Quality gates prevent regression deployments"
            ),
            priority=Priority.P2,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=8,
            category="Testing",
            related_files=[
                RelatedFile(
                    path="frontend/src/__tests__/",
                    type=RelatedFileType.CREATE,
                    description="Frontend unit tests"
                ),
                RelatedFile(
                    path="cypress/integration/",
                    type=RelatedFileType.CREATE,
                    description="End-to-end test specs"
                ),
                RelatedFile(
                    path="cypress/fixtures/",
                    type=RelatedFileType.CREATE,
                    description="Test data fixtures"
                )
            ]
        ),
    ]
    
    # Phase 5: Deployment and Operations
    deployment_tasks = [
        Task(
            name="Production Deployment Configuration",
            description="Set up production deployment with Docker, monitoring, and security configurations",
            implementation_guide=(
                "1. Create Docker containers for all services\n"
                "2. Set up Docker Compose for local development\n"
                "3. Configure production deployment (AWS/GCP/Azure)\n"
                "4. Set up environment-specific configurations\n"
                "5. Add health checks and monitoring\n"
                "6. Configure SSL/TLS and security headers\n"
                "7. Set up backup and disaster recovery"
            ),
            verification_criteria=(
                "- Application deploys successfully to production\n"
                "- All services are properly containerized\n"
                "- Environment configurations are secure\n"
                "- Health checks and monitoring are working\n"
                "- SSL/TLS is properly configured\n"
                "- Backup and recovery procedures are tested"
            ),
            priority=Priority.P2,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=14,
            category="DevOps",
            related_files=[
                RelatedFile(
                    path="Dockerfile",
                    type=RelatedFileType.CREATE,
                    description="Docker container configuration"
                ),
                RelatedFile(
                    path="docker-compose.yml",
                    type=RelatedFileType.CREATE,
                    description="Docker Compose setup"
                ),
                RelatedFile(
                    path="deploy/",
                    type=RelatedFileType.CREATE,
                    description="Deployment scripts and configurations"
                )
            ]
        ),
    ]
    
    # Combine all tasks
    all_tasks = infrastructure_tasks + backend_tasks + frontend_tasks + testing_tasks + deployment_tasks
    
    # Create tasks in the service
    created_tasks = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task_progress = progress.add_task("Creating project tasks...", total=len(all_tasks))
        
        for task in all_tasks:
            created_task = await service.create_task(task)
            created_tasks.append(created_task)
            progress.advance(task_progress)
    
    # Create dependency relationships
    dependencies = [
        # Backend depends on infrastructure
        (created_tasks[2], created_tasks[0]),  # Auth depends on Project Setup
        (created_tasks[2], created_tasks[1]),  # Auth depends on Database
        (created_tasks[3], created_tasks[2]),  # API depends on Auth
        
        # Frontend depends on backend
        (created_tasks[4], created_tasks[3]),  # React Setup depends on API
        (created_tasks[5], created_tasks[4]),  # UI Components depend on React Setup
        
        # Testing depends on implementation
        (created_tasks[6], created_tasks[3]),  # Backend Testing depends on API
        (created_tasks[7], created_tasks[5]),  # Frontend Testing depends on UI
        
        # Deployment depends on everything
        (created_tasks[8], created_tasks[6]),  # Deployment depends on Backend Testing
        (created_tasks[8], created_tasks[7]),  # Deployment depends on Frontend Testing
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        dep_progress = progress.add_task("Creating dependencies...", total=len(dependencies))
        
        for dependent_task, dependency_task in dependencies:
            await service.add_dependency(dependent_task.id, dependency_task.id)
            progress.advance(dep_progress)
    
    # Return project summary
    return {
        "total_tasks": len(created_tasks),
        "phases": {
            "Infrastructure": len(infrastructure_tasks),
            "Backend": len(backend_tasks),
            "Frontend": len(frontend_tasks),
            "Testing": len(testing_tasks),
            "Deployment": len(deployment_tasks),
        },
        "dependencies": len(dependencies),
        "tasks": created_tasks
    }


async def demonstrate_system_features(service: TaskService, project_info: dict):
    """Demonstrate all system features with the created project."""
    console.print(Panel.fit("🔍 System Features Demonstration", style="bold green"))
    
    # 1. Show execution order
    console.print("\n[bold cyan]1. Task Execution Order (Topological Sort)[/bold cyan]")
    execution_order = await service.get_execution_order()
    
    order_table = Table(title="📋 Execution Order")
    order_table.add_column("Order", justify="right", width=6)
    order_table.add_column("Task", min_width=30)
    order_table.add_column("Category", width=12)
    order_table.add_column("Priority", justify="center", width=8)
    order_table.add_column("Hours", justify="right", width=6)
    
    for i, task in enumerate(execution_order, 1):
        priority_val = task.priority.value if hasattr(task.priority, 'value') else task.priority
        priority_color = {"P0": "red", "P1": "orange3", "P2": "yellow", "P3": "blue"}.get(priority_val, "white")
        order_table.add_row(
            str(i),
            task.name,
            task.category or "-",
            f"[{priority_color}]{priority_val}[/{priority_color}]",
            str(task.estimated_hours) if task.estimated_hours else "-"
        )
    
    console.print(order_table)
    
    # 2. Show ready tasks
    console.print("\n[bold cyan]2. Ready Tasks (No Pending Dependencies)[/bold cyan]")
    ready_tasks = await service.get_ready_tasks()
    
    if ready_tasks:
        for task in ready_tasks:
            console.print(f"✅ [green]{task.name}[/green] - {task.category}")
    else:
        console.print("[yellow]No ready tasks (all have dependencies)[/yellow]")
    
    # 3. Simulate work progress
    console.print("\n[bold cyan]3. Simulating Work Progress[/bold cyan]")
    
    # Complete the first few tasks
    tasks_to_complete = execution_order[:3]
    
    for task in tasks_to_complete:
        task.status = TaskStatus.COMPLETED
        await service.update_task(task)
        console.print(f"✅ Completed: [green]{task.name}[/green]")
    
    # Start working on the next task
    if len(execution_order) > 3:
        next_task = execution_order[3]
        next_task.status = TaskStatus.IN_PROGRESS
        await service.update_task(next_task)
        console.print(f"🔄 Started: [blue]{next_task.name}[/blue]")
    
    # 4. Show updated ready tasks
    console.print("\n[bold cyan]4. Updated Ready Tasks After Progress[/bold cyan]")
    updated_ready = await service.get_ready_tasks()
    
    for task in updated_ready:
        console.print(f"⚡ [yellow]{task.name}[/yellow] - Ready to start")
    
    # 5. Filter and query demonstrations
    console.print("\n[bold cyan]5. Advanced Filtering and Queries[/bold cyan]")
    
    # Filter by status
    pending_tasks = await service.list_tasks({"status": TaskStatus.PENDING.value})
    completed_tasks = await service.list_tasks({"status": TaskStatus.COMPLETED.value})
    in_progress_tasks = await service.list_tasks({"status": TaskStatus.IN_PROGRESS.value})
    
    status_table = Table(title="📊 Status Breakdown")
    status_table.add_column("Status", width=15)
    status_table.add_column("Count", justify="right", width=8)
    status_table.add_column("Tasks", min_width=40)
    
    status_table.add_row(
        "[green]COMPLETED[/green]",
        str(len(completed_tasks)),
        ", ".join([t.name[:30] + "..." if len(t.name) > 30 else t.name for t in completed_tasks[:3]])
    )
    status_table.add_row(
        "[blue]IN_PROGRESS[/blue]",
        str(len(in_progress_tasks)),
        ", ".join([t.name[:30] + "..." if len(t.name) > 30 else t.name for t in in_progress_tasks[:3]])
    )
    status_table.add_row(
        "[yellow]PENDING[/yellow]",
        str(len(pending_tasks)),
        ", ".join([t.name[:30] + "..." if len(t.name) > 30 else t.name for t in pending_tasks[:3]])
    )
    
    console.print(status_table)
    
    # Filter by category
    categories = ["DevOps", "Backend", "Frontend", "Testing"]
    category_panels = []
    
    for category in categories:
        category_tasks = await service.list_tasks({"category": category})
        
        content = []
        for task in category_tasks[:3]:  # Show first 3 tasks
            status_val = task.status.value if hasattr(task.status, 'value') else task.status
            status_emoji = {"PENDING": "⏳", "IN_PROGRESS": "🔄", "COMPLETED": "✅"}.get(status_val, "❓")
            content.append(f"{status_emoji} {task.name}")
        
        if len(category_tasks) > 3:
            content.append(f"... and {len(category_tasks) - 3} more")
        
        panel = Panel(
            "\n".join(content) if content else "No tasks",
            title=f"{category} ({len(category_tasks)})",
            title_align="left",
            height=6
        )
        category_panels.append(panel)
    
    console.print(Columns(category_panels, equal=True))
    
    # 6. Comprehensive statistics
    console.print("\n[bold cyan]6. Project Statistics[/bold cyan]")
    stats = await service.get_project_statistics()
    
    stats_content = [
        f"[bold]Total Tasks:[/bold] {stats['total_tasks']}",
        f"[bold]Graph Nodes:[/bold] {stats['graph_nodes']}",
        f"[bold]Graph Edges:[/bold] {stats['graph_edges']}",
        f"[bold]Has Cycles:[/bold] {'⚠️ Yes' if stats['has_cycles'] else '✅ No'}",
        f"[bold]Ready Tasks:[/bold] {stats['ready_tasks_count']}",
        "",
        "[bold]Status Distribution:[/bold]"
    ]
    
    for status, count in stats["status_breakdown"].items():
        color = {"COMPLETED": "green", "IN_PROGRESS": "blue", "PENDING": "yellow", "BLOCKED": "red"}.get(status, "white")
        stats_content.append(f"  [{color}]{status}[/{color}]: {count}")
    
    console.print(Panel(
        "\n".join(stats_content),
        title="📊 Project Analytics",
        title_align="left",
        border_style="cyan"
    ))


async def main():
    """Main demonstration function."""
    console.print(Panel.fit("🚀 Advanced Task Manager - Complete System Demo", style="bold magenta"))
    console.print("[dim]Demonstrating graph + table storage with comprehensive task management[/dim]\n")
    
    # Initialize service with temporary database
    db_path = "demo_tasks.db"
    table_storage = DuckDBTableStorage(Task, database_path=db_path)
    graph_storage = NetworkXGraphStorage()
    service = TaskService(table_storage, graph_storage)
    
    try:
        # Create demo project
        project_info = await create_demo_project(service)
        
        console.print(f"\n[green]✅ Demo project created successfully![/green]")
        console.print(f"📊 Created {project_info['total_tasks']} tasks across {len(project_info['phases'])} phases")
        console.print(f"🔗 Added {project_info['dependencies']} dependency relationships\n")
        
        # Demonstrate system features
        await demonstrate_system_features(service, project_info)
        
        # Export project data
        console.print("\n[bold cyan]7. Data Export Example[/bold cyan]")
        
        all_tasks = await service.list_tasks()
        export_data = {
            "project": "Web Application Demo",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_tasks": len(all_tasks),
            "tasks": [
                {
                    "id": str(task.id),
                    "name": task.name,
                    "description": task.description,
                    "status": task.status.value if hasattr(task.status, 'value') else task.status,
                    "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                    "complexity": task.complexity.value if task.complexity and hasattr(task.complexity, 'value') else (task.complexity if task.complexity else None),
                    "estimated_hours": task.estimated_hours,
                    "category": task.category,
                    "created_at": task.created_at.isoformat(),
                }
                for task in all_tasks
            ]
        }
        
        export_path = Path("demo_project_export.json")
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        
        console.print(f"📁 Project data exported to: [cyan]{export_path.absolute()}[/cyan]")
        
        # Final summary
        console.print(Panel(
            "[bold green]🎉 System demonstration completed successfully![/bold green]\n\n"
            "[bold]Key Features Demonstrated:[/bold]\n"
            "• ✅ Comprehensive task creation with metadata\n"
            "• ✅ Dependency graph management and cycle prevention\n"
            "• ✅ Topological sorting for execution order\n"
            "• ✅ Advanced filtering and querying\n"
            "• ✅ Real-time project statistics and analytics\n"
            "• ✅ Status tracking and workflow management\n"
            "• ✅ Data persistence and export capabilities\n"
            "• ✅ Integration between graph and table storage\n\n"
            f"[dim]Database file: {Path(db_path).absolute()}\n"
            f"Export file: {export_path.absolute()}[/dim]",
            title="Demo Complete",
            title_align="left",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
    
    finally:
        # Cleanup
        table_storage.close()


if __name__ == "__main__":
    asyncio.run(main())