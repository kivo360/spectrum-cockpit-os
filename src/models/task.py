"""Enhanced task models with Pydantic v2 validation."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    """Task execution status."""
    
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class Priority(str, Enum):
    """Task priority levels."""
    
    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium (Default)
    P3 = "P3"  # Low


class ComplexityLevel(str, Enum):
    """Task complexity indicators."""
    
    SIMPLE = "SIMPLE"      # 1-4 hours
    MODERATE = "MODERATE"   # 4-8 hours
    COMPLEX = "COMPLEX"     # 8-16 hours
    EPIC = "EPIC"          # 16+ hours (should be split)


class RelatedFileType(str, Enum):
    """Types of file relationships."""
    
    TO_MODIFY = "TO_MODIFY"
    REFERENCE = "REFERENCE"
    CREATE = "CREATE"
    DEPENDENCY = "DEPENDENCY"
    OTHER = "OTHER"


class GraphNode(BaseModel):
    """Node in the task dependency graph."""
    
    id: UUID = Field(..., description="Unique node identifier")
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Node metadata"
    )
    
    model_config = ConfigDict(frozen=True)  # Immutable nodes


class GraphEdge(BaseModel):
    """Directed edge representing dependency relationship."""
    
    from_id: UUID = Field(..., description="Source node ID")
    to_id: UUID = Field(..., description="Target node ID")
    relationship: str = Field("depends_on", description="Edge relationship type")
    
    model_config = ConfigDict(frozen=True)  # Immutable edges


class RelatedFile(BaseModel):
    """File associated with task execution."""
    
    path: str = Field(..., min_length=1, description="File path")
    type: RelatedFileType = Field(..., description="Relationship type")
    description: str = Field(
        ..., min_length=1, description="File role description"
    )
    line_start: Optional[int] = Field(None, gt=0, description="Start line number")
    line_end: Optional[int] = Field(None, gt=0, description="End line number")
    
    @field_validator("line_end")
    @classmethod
    def validate_line_range(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure line_end >= line_start if both provided."""
        if v is not None and info.data.get("line_start") is not None:
            if v < info.data["line_start"]:
                raise ValueError("line_end must be >= line_start")
        return v


class TaskDependency(BaseModel):
    """Task dependency reference."""
    
    task_id: UUID = Field(..., description="UUID of dependent task")
    
    model_config = ConfigDict(frozen=True)


class Task(BaseModel):
    """Enhanced task model with 15+ structured fields."""
    
    # Core identification
    id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    name: str = Field(
        ..., max_length=100, min_length=1, description="Task name"
    )
    
    # Core content
    description: str = Field(
        ..., min_length=10, description="Detailed task description"
    )
    implementation_guide: str = Field(
        ..., min_length=10, description="How to implement this task"
    )
    verification_criteria: Optional[str] = Field(
        None, description="How to verify completion"
    )
    
    # Status and metadata
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current execution status"
    )
    priority: Priority = Field(
        default=Priority.P2, description="Task priority level"
    )
    complexity: Optional[ComplexityLevel] = Field(
        None, description="Estimated complexity"
    )
    estimated_hours: Optional[int] = Field(
        None, gt=0, le=40, description="Estimated work hours"
    )
    
    # Relationships
    dependencies: List[TaskDependency] = Field(
        default_factory=list, description="Task dependencies"
    )
    related_files: List[RelatedFile] = Field(
        default_factory=list, description="Associated files"
    )
    
    # Organization
    category: Optional[str] = Field(
        None, max_length=50, description="Task category"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp"
    )
    
    # Validation configuration
    model_config = ConfigDict(
        validate_assignment=True,  # Validate on field assignment
        use_enum_values=True,      # Use enum values in serialization
        frozen=False               # Allow updates
    )
    
    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Ensure task name follows proper format."""
        if not v.strip():
            raise ValueError("Task name cannot be empty or whitespace")
        return v.strip()
    
    @field_validator("estimated_hours")
    @classmethod
    def validate_complexity_hours_alignment(
        cls, v: Optional[int], info
    ) -> Optional[int]:
        """Ensure estimated hours align with complexity level."""
        if v is None:
            return v
            
        complexity = info.data.get("complexity")
        if complexity == ComplexityLevel.SIMPLE and v > 4:
            raise ValueError("SIMPLE tasks should be ≤4 hours")
        elif complexity == ComplexityLevel.MODERATE and (v <= 4 or v > 8):
            raise ValueError("MODERATE tasks should be 4-8 hours")
        elif complexity == ComplexityLevel.COMPLEX and (v <= 8 or v > 16):
            raise ValueError("COMPLEX tasks should be 8-16 hours")
        elif complexity == ComplexityLevel.EPIC and v <= 16:
            raise ValueError("EPIC tasks should be >16 hours (consider splitting)")
            
        return v
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)