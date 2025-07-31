"""
Pydantic schemas for task splitting validation.

Provides JSON schema validation for task splitting operations,
compatible with MCP tool requirements and modern Pydantic v2 patterns.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..models.task import Priority, ComplexityLevel, TaskStatus, RelatedFileType


class UpdateModeSchema(str, Enum):
    """Schema for update mode validation."""
    APPEND = "append"
    OVERWRITE = "overwrite"
    SELECTIVE = "selective"
    CLEAR_ALL_TASKS = "clearAllTasks"


class RelatedFileSchema(BaseModel):
    """Schema for related file validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )
    
    path: str = Field(
        ...,
        min_length=1,
        description="File path (relative or absolute)"
    )
    type: RelatedFileType = Field(
        ...,
        description="File relationship type"
    )
    description: str = Field(
        ...,
        min_length=1,
        description="File purpose and content description"
    )
    line_start: Optional[int] = Field(
        default=None,
        ge=1,
        description="Code block start line (optional)"
    )
    line_end: Optional[int] = Field(
        default=None,
        ge=1,
        description="Code block end line (optional)"
    )
    
    @field_validator("line_end")
    @classmethod
    def validate_line_range(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure line_end is greater than line_start if both are provided."""
        if v is not None and info.data.get("line_start") is not None:
            if v <= info.data["line_start"]:
                raise ValueError("line_end must be greater than line_start")
        return v


class TaskTemplateSchema(BaseModel):
    """Schema for task template validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Clear, concise task name"
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Detailed task description with implementation points"
    )
    implementation_guide: str = Field(
        ...,
        min_length=10,
        description="Specific implementation methods and steps"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of prerequisite task names or IDs"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Supplementary implementation suggestions"
    )
    related_files: List[RelatedFileSchema] = Field(
        default_factory=list,
        description="Associated files with line-level precision"
    )
    verification_criteria: Optional[str] = Field(
        default=None,
        description="Specific validation standards and verification methods"
    )
    priority: Optional[Priority] = Field(
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
    
    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: List[str]) -> List[str]:
        """Remove duplicates and empty strings from dependencies."""
        if not v:
            return v
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in v:
            clean_dep = dep.strip()
            if clean_dep and clean_dep not in seen:
                seen.add(clean_dep)
                unique_deps.append(clean_dep)
        
        return unique_deps


class GranularityRulesSchema(BaseModel):
    """Schema for granularity rules validation."""
    model_config = ConfigDict(
        extra="forbid"
    )
    
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
    max_subtasks_per_split: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of subtasks in a single split"
    )
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
    max_depth_levels: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum task hierarchy depth"
    )


class TaskSplitRequestSchema(BaseModel):
    """Schema for task split request validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )
    
    update_mode: UpdateModeSchema = Field(
        default=UpdateModeSchema.CLEAR_ALL_TASKS,
        description="Task update strategy for the split operation"
    )
    task_templates: List[TaskTemplateSchema] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of task templates to create or update"
    )
    global_analysis_result: Optional[str] = Field(
        default=None,
        description="Overall project goal applicable to all tasks"
    )
    granularity_rules: Optional[GranularityRulesSchema] = Field(
        default=None,
        description="Custom granularity rules (uses defaults if not provided)"
    )
    
    @field_validator("task_templates")
    @classmethod
    def validate_unique_task_names(cls, v: List[TaskTemplateSchema]) -> List[TaskTemplateSchema]:
        """Ensure task names are unique within the request."""
        names = [template.name.lower().strip() for template in v]
        if len(names) != len(set(names)):
            raise ValueError("Task names must be unique within a split request")
        return v


class SplitOperationSchema(BaseModel):
    """Schema for split operation tracking."""
    model_config = ConfigDict(
        extra="forbid"
    )
    
    operation_type: str = Field(
        ...,
        description="Type of operation performed"
    )
    update_mode: UpdateModeSchema = Field(
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
        ...,
        description="When the operation was performed"
    )


class TaskSchema(BaseModel):
    """Simplified task schema for split results."""
    model_config = ConfigDict(
        extra="forbid"
    )
    
    id: str = Field(..., description="Task unique identifier")
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    implementation_guide: str = Field(..., description="Implementation guide")
    verification_criteria: str = Field(..., description="Verification criteria")
    status: TaskStatus = Field(..., description="Task status")
    priority: Priority = Field(..., description="Task priority")
    complexity: Optional[ComplexityLevel] = Field(default=None, description="Task complexity")
    estimated_hours: Optional[int] = Field(default=None, description="Estimated hours")
    category: Optional[str] = Field(default=None, description="Task category")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    related_files: List[RelatedFileSchema] = Field(default_factory=list, description="Related files")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SplitResultSchema(BaseModel):
    """Schema for split result validation."""
    model_config = ConfigDict(
        extra="forbid"
    )
    
    success: bool = Field(
        ...,
        description="Whether the split operation succeeded"
    )
    created_tasks: List[TaskSchema] = Field(
        default_factory=list,
        description="Tasks that were created or updated"
    )
    operation: Optional[SplitOperationSchema] = Field(
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


class TaskDecompositionSchema(BaseModel):
    """Schema for task decomposition validation."""
    model_config = ConfigDict(
        extra="forbid"
    )
    
    original_task: TaskSchema = Field(
        ...,
        description="The original task that was decomposed"
    )
    subtask_templates: List[TaskTemplateSchema] = Field(
        ...,
        min_length=1,
        description="Templates for the generated subtasks"
    )
    decomposition_strategy: str = Field(
        default="functional_modules",
        description="Strategy used to decompose the task"
    )
    granularity_rules: GranularityRulesSchema = Field(
        ...,
        description="Rules applied during decomposition"
    )
    created_at: datetime = Field(
        ...,
        description="When the decomposition was created"
    )


# Raw JSON schemas for MCP tool integration
class RawTaskSplitSchema(BaseModel):
    """Raw schema for MCP tool JSON input (matching Shrimp format)."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )
    
    updateMode: str = Field(
        default="clearAllTasks",
        description="Task update mode"
    )
    tasksRaw: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="JSON string containing task templates"
    )
    globalAnalysisResult: Optional[str] = Field(
        default=None,
        description="Global project analysis result"
    )
    
    @field_validator("updateMode")
    @classmethod
    def validate_update_mode(cls, v: str) -> str:
        """Validate update mode is one of the allowed values."""
        allowed_modes = {"append", "overwrite", "selective", "clearAllTasks"}
        if v not in allowed_modes:
            raise ValueError(f"updateMode must be one of: {', '.join(allowed_modes)}")
        return v
    
    @field_validator("tasksRaw")
    @classmethod
    def validate_tasks_raw_json(cls, v: str) -> str:
        """Validate that tasksRaw is valid JSON."""
        import json
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("tasksRaw must be a JSON array")
            if len(parsed) == 0:
                raise ValueError("tasksRaw must contain at least one task")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"tasksRaw must be valid JSON: {e}")


# Export commonly used schemas
__all__ = [
    "UpdateModeSchema",
    "RelatedFileSchema", 
    "TaskTemplateSchema",
    "GranularityRulesSchema",
    "TaskSplitRequestSchema",
    "SplitOperationSchema",
    "TaskSchema",
    "SplitResultSchema",
    "TaskDecompositionSchema",
    "RawTaskSplitSchema"
]