"""
Task splitting service implementation.

Provides intelligent task decomposition, dependency resolution, and advanced
task management workflows following MCP Shrimp Task Manager patterns.
"""

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict, deque

from ..models.task_splitting import (
    TaskSplitRequest,
    TaskTemplate,
    UpdateMode,
    SplitResult,
    SplitOperation,
    TaskDecomposition,
    GranularityRules
)
from ..models.task import Task, TaskStatus, TaskDependency, Priority, ComplexityLevel
from ..services.task_service import TaskService


class SplitStrategy(str, Enum):
    """Task splitting strategies for different decomposition approaches."""
    FUNCTIONAL_MODULES = "functional_modules"     # Split by functional areas
    SEQUENTIAL_STEPS = "sequential_steps"         # Split by chronological steps
    PARALLEL_FEATURES = "parallel_features"       # Split by independent features
    COMPLEXITY_BASED = "complexity_based"         # Split by complexity levels


class DependencyResolver:
    """
    Utility class for resolving task dependencies and managing dependency graphs.
    
    Handles conversion from string references (names/IDs) to structured
    TaskDependency objects with proper validation and cycle detection.
    """
    
    def resolve_task_dependencies(
        self, 
        templates: List[TaskTemplate], 
        existing_tasks: List[Task]
    ) -> List[Task]:
        """
        Resolve task dependencies for templates against existing tasks.
        
        Args:
            templates: List of task templates with dependency strings
            existing_tasks: List of existing tasks to resolve against
            
        Returns:
            List of Task objects with resolved TaskDependency objects
        """
        # Create lookup maps for existing tasks
        name_to_task = {task.name: task for task in existing_tasks}
        id_to_task = {str(task.id): task for task in existing_tasks}
        
        resolved_tasks = []
        
        for template in templates:
            # Convert template to task
            task = template.to_task()
            
            # Resolve dependencies
            resolved_dependencies = []
            for dep_ref in template.dependencies:
                dep_ref = dep_ref.strip()
                
                # Try to resolve by UUID first
                if dep_ref in id_to_task:
                    resolved_dependencies.append(
                        TaskDependency(task_id=uuid.UUID(dep_ref))
                    )
                # Then try by name
                elif dep_ref in name_to_task:
                    resolved_dependencies.append(
                        TaskDependency(task_id=name_to_task[dep_ref].id)
                    )
                # Skip unresolvable dependencies (with warning in real implementation)
            
            task.dependencies = resolved_dependencies
            resolved_tasks.append(task)
        
        return resolved_tasks
    
    def detect_circular_dependencies(self, templates: List[TaskTemplate]) -> bool:
        """
        Detect circular dependencies in task templates.
        
        Args:
            templates: List of task templates to check
            
        Returns:
            True if circular dependencies are detected, False otherwise
        """
        # Build dependency graph
        graph = defaultdict(list)
        for template in templates:
            for dep in template.dependencies:
                graph[dep].append(template.name)
        
        # Use DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check all nodes
        for template in templates:
            if template.name not in visited:
                if has_cycle(template.name):
                    return True
        
        return False
    
    def topological_sort(self, templates: List[TaskTemplate]) -> List[str]:
        """
        Return task names in topologically sorted order (dependencies first).
        
        Args:
            templates: List of task templates to sort
            
        Returns:
            List of task names in dependency-resolved execution order
        """
        # Build adjacency list and in-degree count
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        all_tasks = {template.name for template in templates}
        
        # Initialize in-degree for all tasks
        for template in templates:
            in_degree[template.name] = 0
        
        # Build graph and calculate in-degrees
        for template in templates:
            for dep in template.dependencies:
                if dep in all_tasks:  # Only consider dependencies within our task set
                    graph[dep].append(template.name)
                    in_degree[template.name] += 1
        
        # Kahn's algorithm for topological sorting
        queue = deque([task for task in all_tasks if in_degree[task] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If we couldn't sort all tasks, there might be a cycle
        if len(result) != len(all_tasks):
            # Return alphabetical order as fallback
            return sorted(all_tasks)
        
        return result


class TaskSplittingService:
    """
    Service for intelligent task splitting and decomposition.
    
    Provides advanced task management capabilities including:
    - Intelligent task decomposition with multiple strategies
    - Dependency resolution and cycle detection  
    - Update mode handling (append/overwrite/selective/clear)
    - Granularity validation and quality enforcement
    - Task execution order optimization
    """
    
    def __init__(self, task_service: TaskService):
        """
        Initialize the task splitting service.
        
        Args:
            task_service: Service for task CRUD operations
        """
        self.task_service = task_service
        self.dependency_resolver = DependencyResolver()
        self.default_granularity_rules = GranularityRules()
    
    async def split_tasks(self, request: TaskSplitRequest) -> SplitResult:
        """
        Split tasks according to the provided request and update mode.
        
        Args:
            request: Task split request with templates and configuration
            
        Returns:
            Result of the split operation with created tasks and operation details
        """
        try:
            # Validate the request
            is_valid, validation_errors = await self.validate_split_request(request)
            if not is_valid:
                return SplitResult(
                    success=False,
                    created_tasks=[],
                    operation=None,
                    message="Validation failed",
                    errors=validation_errors
                )
            
            # Get current tasks for baseline
            existing_tasks = await self.task_service.get_all_tasks()
            tasks_before_count = len(existing_tasks)
            
            # Handle different update modes
            created_tasks = []
            tasks_updated = 0
            tasks_removed = 0
            
            if request.update_mode == UpdateMode.CLEAR_ALL_TASKS:
                # Clear all existing tasks and create new ones
                await self.task_service.clear_all_tasks()
                created_tasks = await self._create_tasks_from_templates(
                    request.task_templates, []
                )
                tasks_removed = tasks_before_count
                
            elif request.update_mode == UpdateMode.APPEND:
                # Add new tasks to existing ones
                created_tasks = await self._create_tasks_from_templates(
                    request.task_templates, existing_tasks
                )
                
            elif request.update_mode == UpdateMode.SELECTIVE:
                # Update matching tasks, create new ones
                created_tasks, tasks_updated = await self._selective_update_tasks(
                    request.task_templates, existing_tasks
                )
                
            elif request.update_mode == UpdateMode.OVERWRITE:
                # Remove unfinished tasks, keep completed ones, add new tasks
                completed_tasks = [
                    task for task in existing_tasks 
                    if task.status == TaskStatus.COMPLETED
                ]
                
                # Remove non-completed tasks
                for task in existing_tasks:
                    if task.status != TaskStatus.COMPLETED:
                        await self.task_service.delete_task(task.id)
                        tasks_removed += 1
                
                # Create new tasks
                created_tasks = await self._create_tasks_from_templates(
                    request.task_templates, completed_tasks
                )
            
            # Create operation record
            tasks_after_count = len(await self.task_service.get_all_tasks())
            operation = SplitOperation(
                operation_type="split_tasks",
                update_mode=request.update_mode,
                tasks_before_count=tasks_before_count,
                tasks_after_count=tasks_after_count,
                tasks_added=len(created_tasks),
                tasks_updated=tasks_updated,
                tasks_removed=tasks_removed
            )
            
            return SplitResult(
                success=True,
                created_tasks=created_tasks,
                operation=operation,
                message=f"Successfully processed {len(created_tasks)} tasks using {request.update_mode.value} mode",
                errors=[]
            )
            
        except Exception as e:
            return SplitResult(
                success=False,
                created_tasks=[],
                operation=None,
                message=f"Split operation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _create_tasks_from_templates(
        self, 
        templates: List[TaskTemplate],
        existing_tasks: List[Task]
    ) -> List[Task]:
        """Create tasks from templates with dependency resolution."""
        resolved_tasks = self.dependency_resolver.resolve_task_dependencies(
            templates, existing_tasks
        )
        
        created_tasks = []
        for task in resolved_tasks:
            created_task = await self.task_service.create_task(task)
            created_tasks.append(created_task)
        
        return created_tasks
    
    async def _selective_update_tasks(
        self,
        templates: List[TaskTemplate],
        existing_tasks: List[Task]
    ) -> Tuple[List[Task], int]:
        """
        Selectively update or create tasks based on name matching.
        
        Returns:
            Tuple of (created_tasks, updated_count)
        """
        existing_by_name = {task.name: task for task in existing_tasks}
        created_tasks = []
        updated_count = 0
        
        for template in templates:
            if template.name in existing_by_name:
                # Update existing task
                existing_task = existing_by_name[template.name]
                
                # Update fields from template
                existing_task.description = template.description
                existing_task.implementation_guide = template.implementation_guide
                existing_task.verification_criteria = template.verification_criteria or ""
                existing_task.notes = template.notes
                existing_task.priority = template.priority
                existing_task.complexity = template.complexity
                existing_task.estimated_hours = template.estimated_hours
                existing_task.category = template.category
                existing_task.related_files = template.related_files.copy()
                
                # Resolve and update dependencies
                resolved_deps = self.dependency_resolver.resolve_task_dependencies(
                    [template], existing_tasks
                )
                if resolved_deps:
                    existing_task.dependencies = resolved_deps[0].dependencies
                
                updated_task = await self.task_service.update_task(existing_task)
                created_tasks.append(updated_task)
                updated_count += 1
            else:
                # Create new task
                resolved_tasks = self.dependency_resolver.resolve_task_dependencies(
                    [template], existing_tasks
                )
                if resolved_tasks:
                    new_task = await self.task_service.create_task(resolved_tasks[0])
                    created_tasks.append(new_task)
        
        return created_tasks, updated_count
    
    async def validate_split_request(self, request: TaskSplitRequest) -> Tuple[bool, List[str]]:
        """
        Validate a split request against granularity rules and business logic.
        
        Args:
            request: The split request to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check granularity rules
        if not request.validate_granularity():
            errors.append("Request violates granularity rules - too many tasks or invalid task constraints")
        
        # Check for circular dependencies
        if self.dependency_resolver.detect_circular_dependencies(request.task_templates):
            errors.append("Circular dependencies detected in task templates")
        
        # Validate individual templates
        for i, template in enumerate(request.task_templates):
            if not request.granularity_rules.validate_task_name_length(template.name):
                errors.append(f"Task {i+1}: Name '{template.name}' exceeds maximum length")
            
            if not request.granularity_rules.validate_description_length(template.description):
                errors.append(f"Task {i+1}: Description too short (minimum {request.granularity_rules.min_description_length} characters)")
        
        return len(errors) == 0, errors
    
    async def decompose_task(
        self,
        original_task: Task,
        strategy: SplitStrategy = SplitStrategy.FUNCTIONAL_MODULES,
        max_subtasks: int = 8,
        granularity_rules: Optional[GranularityRules] = None
    ) -> TaskDecomposition:
        """
        Decompose a complex task into manageable subtasks.
        
        Args:
            original_task: The task to decompose
            strategy: Decomposition strategy to use
            max_subtasks: Maximum number of subtasks to create
            granularity_rules: Rules for task granularity validation
            
        Returns:
            TaskDecomposition with generated subtask templates
        """
        if granularity_rules is None:
            granularity_rules = self.default_granularity_rules
        
        # Generate subtask templates based on strategy
        subtask_templates = []
        
        if strategy == SplitStrategy.FUNCTIONAL_MODULES:
            subtask_templates = self._decompose_by_functional_modules(
                original_task, max_subtasks
            )
        elif strategy == SplitStrategy.SEQUENTIAL_STEPS:
            subtask_templates = self._decompose_by_sequential_steps(
                original_task, max_subtasks
            )
        elif strategy == SplitStrategy.PARALLEL_FEATURES:
            subtask_templates = self._decompose_by_parallel_features(
                original_task, max_subtasks
            )
        elif strategy == SplitStrategy.COMPLEXITY_BASED:
            subtask_templates = self._decompose_by_complexity(
                original_task, max_subtasks
            )
        
        return TaskDecomposition(
            original_task=original_task,
            subtask_templates=subtask_templates,
            decomposition_strategy=strategy.value,
            granularity_rules=granularity_rules
        )
    
    def _decompose_by_functional_modules(
        self, 
        original_task: Task, 
        max_subtasks: int
    ) -> List[TaskTemplate]:
        """Decompose task by functional modules/areas."""
        # This is a simplified implementation - in reality, this would use
        # NLP or AI to analyze the task and create intelligent subtasks
        
        base_name = original_task.name
        subtasks = []
        
        # Common functional modules for software projects
        modules = [
            ("Setup & Configuration", "Initialize project structure and dependencies"),
            ("Core Implementation", "Implement the main functionality and business logic"),
            ("User Interface", "Create user interface components and interactions"),
            ("Testing & Validation", "Implement comprehensive testing and validation"),
            ("Documentation", "Create user and technical documentation")
        ]
        
        for i, (module_name, module_desc) in enumerate(modules[:max_subtasks]):
            subtask = TaskTemplate(
                name=f"{base_name}: {module_name}",
                description=f"{module_desc} for {original_task.description}",
                implementation_guide=f"Implement {module_name.lower()} following best practices",
                dependencies=[subtasks[i-1].name] if i > 0 else [],
                priority=original_task.priority,
                complexity=ComplexityLevel.MODERATE if original_task.complexity == ComplexityLevel.COMPLEX else ComplexityLevel.SIMPLE,
                category=original_task.category
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def _decompose_by_sequential_steps(
        self, 
        original_task: Task, 
        max_subtasks: int
    ) -> List[TaskTemplate]:
        """Decompose task by chronological steps."""
        base_name = original_task.name
        subtasks = []
        
        # Generic sequential steps
        steps = [
            ("Planning & Analysis", "Analyze requirements and create detailed plan"),
            ("Foundation Setup", "Setup basic infrastructure and foundation"),
            ("Core Development", "Implement core functionality step by step"),
            ("Integration", "Integrate all components and test interactions"),
            ("Finalization", "Final testing, cleanup, and deployment preparation")
        ]
        
        for i, (step_name, step_desc) in enumerate(steps[:max_subtasks]):
            subtask = TaskTemplate(
                name=f"{base_name}: {step_name}",
                description=f"{step_desc} for {original_task.description}",
                implementation_guide=f"Complete {step_name.lower()} with attention to detail",
                dependencies=[subtasks[i-1].name] if i > 0 else [],
                priority=original_task.priority,
                complexity=ComplexityLevel.MODERATE,
                category=original_task.category
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def _decompose_by_parallel_features(
        self, 
        original_task: Task, 
        max_subtasks: int
    ) -> List[TaskTemplate]:
        """Decompose task by independent parallel features."""
        base_name = original_task.name
        subtasks = []
        
        # Generic parallel features
        features = [
            ("Feature A", "Implement first independent feature"),
            ("Feature B", "Implement second independent feature"),
            ("Feature C", "Implement third independent feature"),
            ("Integration Layer", "Create integration layer connecting all features")
        ]
        
        for i, (feature_name, feature_desc) in enumerate(features[:max_subtasks]):
            # Only the integration layer depends on other features
            deps = []
            if "Integration" in feature_name and i > 0:
                deps = [f"{base_name}: Feature A", f"{base_name}: Feature B"]
            
            subtask = TaskTemplate(
                name=f"{base_name}: {feature_name}",
                description=f"{feature_desc} for {original_task.description}",
                implementation_guide=f"Implement {feature_name.lower()} as independent module",
                dependencies=deps,
                priority=original_task.priority,
                complexity=ComplexityLevel.MODERATE,
                category=original_task.category
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def _decompose_by_complexity(
        self, 
        original_task: Task, 
        max_subtasks: int
    ) -> List[TaskTemplate]:
        """Decompose task by complexity levels."""
        base_name = original_task.name
        subtasks = []
        
        # Complexity-based breakdown
        complexity_levels = [
            ("Simple Components", ComplexityLevel.SIMPLE, "Implement straightforward components"),
            ("Moderate Logic", ComplexityLevel.MODERATE, "Implement moderately complex logic"),
            ("Complex Integration", ComplexityLevel.COMPLEX, "Handle complex integration requirements")
        ]
        
        for i, (level_name, complexity, level_desc) in enumerate(complexity_levels[:max_subtasks]):
            subtask = TaskTemplate(
                name=f"{base_name}: {level_name}",
                description=f"{level_desc} for {original_task.description}",
                implementation_guide=f"Focus on {level_name.lower()} with appropriate complexity handling",
                dependencies=[subtasks[i-1].name] if i > 0 else [],
                priority=original_task.priority,
                complexity=complexity,
                category=original_task.category
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def get_execution_order(self, templates: List[TaskTemplate]) -> List[str]:
        """
        Get recommended execution order for task templates based on dependencies.
        
        Args:
            templates: List of task templates to order
            
        Returns:
            List of task names in recommended execution order
        """
        return self.dependency_resolver.topological_sort(templates)
    
    async def get_split_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current task splitting state.
        
        Returns:
            Dictionary containing various statistics about tasks
        """
        all_tasks = await self.task_service.get_all_tasks()
        
        # Basic counts
        total_tasks = len(all_tasks)
        
        # Status distribution
        status_counts = defaultdict(int)
        for task in all_tasks:
            status_counts[task.status.value] += 1
        
        # Dependency analysis
        dependency_counts = [len(task.dependencies) for task in all_tasks]
        avg_dependencies = sum(dependency_counts) / len(dependency_counts) if dependency_counts else 0
        
        # Complexity analysis
        complexity_counts = defaultdict(int)
        for task in all_tasks:
            if task.complexity:
                complexity_counts[task.complexity.value] += 1
        
        # Find most complex tasks (by dependency count)
        most_complex_tasks = sorted(
            all_tasks,
            key=lambda t: len(t.dependencies),
            reverse=True
        )[:5]
        
        return {
            "total_tasks": total_tasks,
            "task_status_distribution": dict(status_counts),
            "average_dependencies_per_task": round(avg_dependencies, 2),
            "complexity_distribution": dict(complexity_counts),
            "most_complex_tasks": [
                {
                    "name": task.name,
                    "dependency_count": len(task.dependencies),
                    "complexity": task.complexity.value if task.complexity else None
                }
                for task in most_complex_tasks
            ]
        }