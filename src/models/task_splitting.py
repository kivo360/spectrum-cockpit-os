"""
Task splitting and decomposition models.

This module provides comprehensive models for intelligent task decomposition,
following the patterns from MCP Shrimp Task Manager with enhanced validation
and modern Pydantic v2 patterns.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict

from .task import Task, TaskStatus, Priority, ComplexityLevel, RelatedFile


class UpdateMode(str, Enum):
    """
    Task update modes for split operations.
    
    Based on Shrimp's four update modes for different task management scenarios.
    """
    APPEND = "append"                    # Preserve all existing tasks, add new ones
    OVERWRITE = "overwrite"              # Remove unfinished tasks, keep completed ones
    SELECTIVE = "selective"              # Smart update by name matching (recommended for refinements)
    CLEAR_ALL_TASKS = "clearAllTasks"    # Complete reset with backup (default)


class GranularityRules(BaseModel):
    """
    Rules for task granularity validation and enforcement.
    
    Ensures tasks are appropriately sized and maintain quality standards.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    # Task duration constraints (in hours)
    min_task_duration_hours: int = Field(
        default=1,
        ge=1,
        description="Minimum viable task duration in hours"
    )
    max_task_duration_hours: int = Field(
        default=16,
        le=40,
        description="Maximum task duration to maintain focus"
    )
    
    # Task quantity constraints
    max_subtasks_per_split: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of subtasks in a single split operation"
    )
    
    # Content length constraints
    max_task_raw_length: int = Field(
        default=5000,
        ge=100,
        description="Maximum character limit for task raw input"
    )
    max_task_name_length: int = Field(
        default=100,
        ge=5,
        description="Maximum task name length"
    )
    min_description_length: int = Field(
        default=10,
        ge=5,
        description="Minimum task description length"
    )
    
    # Structural constraints
    max_depth_levels: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum task hierarchy depth (Modules > Processes > Steps)"
    )
    
    def validate_task_count(self, count: int) -> bool:
        """Validate if task count is within acceptable limits."""
        return 1 <= count <= self.max_subtasks_per_split
    
    def validate_task_name_length(self, name: str) -> bool:
        """Validate task name length."""
        return 1 <= len(name.strip()) <= self.max_task_name_length
    
    def validate_description_length(self, description: str) -> bool:
        """Validate task description length."""
        return len(description.strip()) >= self.min_description_length
    
    @field_validator("max_task_duration_hours")
    @classmethod
    def validate_duration_range(cls, v: int, info) -> int:
        """Ensure max duration is greater than min duration."""
        min_duration = info.data.get("min_task_duration_hours", 1)
        if v <= min_duration:
            raise ValueError(f"Max duration ({v}) must be greater than min duration ({min_duration})")
        return v


class TaskTemplate(BaseModel):
    """
    Template for creating tasks with structured decomposition data.
    
    Represents a task template that can be converted to an actual Task instance
    with all required fields and validation.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Clear, concise task name expressing the task purpose"
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Detailed task description with implementation points and acceptance criteria"
    )
    implementation_guide: str = Field(
        ...,
        min_length=10,
        description="Specific implementation methods and steps with pseudocode"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of prerequisite task names or IDs"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Supplementary implementation suggestions or special requirements"
    )
    related_files: List[RelatedFile] = Field(
        default_factory=list,
        description="Associated files with line-level precision"
    )
    verification_criteria: Optional[str] = Field(
        default=None,
        description="Specific validation standards and verification methods"
    )
    
    # Task metadata for conversion
    priority: Priority = Field(
        default=Priority.P2,
        description="Task priority level"
    )
    complexity: Optional[ComplexityLevel] = Field(
        default=None,
        description="Estimated task complexity"
    )
    estimated_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=40,
        description="Estimated hours to complete"
    )
    category: Optional[str] = Field(
        default=None,
        description="Task category or domain"
    )
    
    def to_task(self) -> Task:
        """Convert template to actual Task instance."""
        return Task(
            name=self.name,
            description=self.description,
            implementation_guide=self.implementation_guide,
            verification_criteria=self.verification_criteria or "",
            status=TaskStatus.PENDING,
            priority=self.priority,
            complexity=self.complexity,
            estimated_hours=self.estimated_hours,
            category=self.category,
            notes=self.notes,
            dependencies=[],  # Will be resolved during splitting
            related_files=self.related_files.copy()
        )
    
    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: List[str]) -> List[str]:
        """Validate dependency list."""
        if not v:
            return v
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in v:
            if dep.strip() and dep not in seen:
                seen.add(dep)
                unique_deps.append(dep.strip())
        
        return unique_deps


class TaskSplitRequest(BaseModel):
    """
    Request model for task splitting operations.
    
    Contains all information needed to perform intelligent task decomposition
    with proper validation and granularity controls.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    update_mode: UpdateMode = Field(
        default=UpdateMode.CLEAR_ALL_TASKS,
        description="Task update strategy for the split operation"
    )
    task_templates: List[TaskTemplate] = Field(
        ...,
        min_length=1,
        description="List of task templates to create or update"
    )
    global_analysis_result: Optional[str] = Field(
        default=None,
        description="Overall project goal applicable to all tasks"
    )
    granularity_rules: GranularityRules = Field(
        default_factory=GranularityRules,
        description="Rules for task granularity validation"
    )
    
    def validate_granularity(self) -> bool:
        """Validate request against granularity rules."""
        # Check task count
        if not self.granularity_rules.validate_task_count(len(self.task_templates)):
            return False
        
        # Check individual task constraints
        for template in self.task_templates:
            if not self.granularity_rules.validate_task_name_length(template.name):
                return False
            if not self.granularity_rules.validate_description_length(template.description):
                return False
        
        return True
    
    @field_validator("task_templates")
    @classmethod
    def validate_task_templates(cls, v: List[TaskTemplate]) -> List[TaskTemplate]:
        """Validate task templates for uniqueness and quality."""
        if not v:
            raise ValueError("At least one task template is required")
        
        # Check for duplicate names
        names = [template.name.lower().strip() for template in v]
        if len(names) != len(set(names)):
            raise ValueError("Task names must be unique within a split request")
        
        return v


class SplitOperation(BaseModel):
    """
    Record of a task splitting operation for tracking and auditing.
    
    Captures the details of what happened during a split operation
    for debugging, rollback, and analytics purposes.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    operation_type: str = Field(
        ...,
        description="Type of operation performed (e.g., 'split_tasks')"
    )
    update_mode: UpdateMode = Field(
        ...,
        description="Update mode used for the operation"
    )
    tasks_before_count: int = Field(
        ...,
        ge=0,
        description="Number of tasks before the operation"
    )
    tasks_after_count: int = Field(
        ...,
        ge=0,
        description="Number of tasks after the operation"
    )
    tasks_added: int = Field(
        ...,
        ge=0,
        description="Number of tasks added"
    )
    tasks_updated: int = Field(
        ...,
        ge=0,
        description="Number of tasks updated"
    )
    tasks_removed: int = Field(
        ...,
        ge=0,
        description="Number of tasks removed"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the operation was performed"
    )
    
    def get_summary(self) -> str:
        """Generate a human-readable summary of the operation."""
        return (
            f"Split operation ({self.update_mode.value}): "
            f"{self.tasks_before_count} → {self.tasks_after_count} tasks "
            f"(+{self.tasks_added}, ~{self.tasks_updated}, -{self.tasks_removed})"
        )


class SplitResult(BaseModel):
    """
    Result of a task splitting operation.
    
    Contains the outcome of the split operation including created tasks,
    operation details, and any errors that occurred.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    success: bool = Field(
        ...,
        description="Whether the split operation succeeded"
    )
    created_tasks: List[Task] = Field(
        default_factory=list,
        description="Tasks that were created or updated"
    )
    operation: Optional[SplitOperation] = Field(
        default=None,
        description="Details of the operation performed"
    )
    message: str = Field(
        ...,
        description="Human-readable result message"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors that occurred during the operation"
    )
    
    @property
    def task_count(self) -> int:
        """Number of tasks in the result."""
        return len(self.created_tasks)
    
    def get_task_names(self) -> List[str]:
        """Get list of created task names."""
        return [task.name for task in self.created_tasks]


class TaskDecomposition(BaseModel):
    """
    Complete task decomposition with original task and generated subtasks.
    
    Represents the full decomposition of a complex task into manageable subtasks
    with dependency tracking and validation.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    original_task: Task = Field(
        ...,
        description="The original task that was decomposed"
    )
    subtask_templates: List[TaskTemplate] = Field(
        ...,
        min_length=1,
        description="Templates for the generated subtasks"
    )
    decomposition_strategy: str = Field(
        default="functional_modules",
        description="Strategy used to decompose the task"
    )
    granularity_rules: GranularityRules = Field(
        default_factory=GranularityRules,
        description="Rules applied during decomposition"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the decomposition was created"
    )
    
    def validate(self) -> bool:
        """Validate the decomposition against granularity rules."""
        # Check subtask count
        if not self.granularity_rules.validate_task_count(len(self.subtask_templates)):
            return False
        
        # Check individual subtask quality
        for template in self.subtask_templates:
            if not self.granularity_rules.validate_task_name_length(template.name):
                return False
            if not self.granularity_rules.validate_description_length(template.description):
                return False
        
        return True
    
    def get_dependency_map(self) -> Dict[str, List[str]]:
        """Get mapping of task names to their dependencies."""
        return {
            template.name: template.dependencies.copy()
            for template in self.subtask_templates
        }
    
    def get_execution_order(self) -> List[str]:
        """Get recommended execution order based on dependencies."""
        # Simple topological sort of task names
        dependency_map = self.get_dependency_map()
        result = []
        remaining = set(dependency_map.keys())
        
        while remaining:
            # Find tasks with no unmet dependencies
            ready = []
            for task_name in remaining:
                deps = dependency_map[task_name]
                if all(dep in result or dep not in remaining for dep in deps):
                    ready.append(task_name)
            
            if not ready:
                # Circular dependency or unresolvable - add remaining in original order
                ready = list(remaining)
            
            # Sort alphabetically for consistent ordering
            ready.sort()
            result.extend(ready)
            remaining -= set(ready)
        
        return result