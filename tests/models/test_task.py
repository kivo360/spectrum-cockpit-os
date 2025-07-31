"""Comprehensive tests for enhanced task models."""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import ValidationError

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


class TestTaskStatus:
    """Test TaskStatus enum."""
    
    def test_task_status_values(self):
        """Test all task status enum values."""
        assert TaskStatus.PENDING == "PENDING"
        assert TaskStatus.IN_PROGRESS == "IN_PROGRESS"
        assert TaskStatus.COMPLETED == "COMPLETED"
        assert TaskStatus.BLOCKED == "BLOCKED"


class TestPriority:
    """Test Priority enum."""
    
    def test_priority_values(self):
        """Test all priority enum values."""
        assert Priority.P0 == "P0"
        assert Priority.P1 == "P1"
        assert Priority.P2 == "P2"
        assert Priority.P3 == "P3"


class TestComplexityLevel:
    """Test ComplexityLevel enum."""
    
    def test_complexity_level_values(self):
        """Test all complexity level enum values."""
        assert ComplexityLevel.SIMPLE == "SIMPLE"
        assert ComplexityLevel.MODERATE == "MODERATE"
        assert ComplexityLevel.COMPLEX == "COMPLEX"
        assert ComplexityLevel.EPIC == "EPIC"


class TestRelatedFileType:
    """Test RelatedFileType enum."""
    
    def test_related_file_type_values(self):
        """Test all related file type enum values."""
        assert RelatedFileType.TO_MODIFY == "TO_MODIFY"
        assert RelatedFileType.REFERENCE == "REFERENCE"
        assert RelatedFileType.CREATE == "CREATE"
        assert RelatedFileType.DEPENDENCY == "DEPENDENCY"
        assert RelatedFileType.OTHER == "OTHER"


class TestGraphNode:
    """Test GraphNode model."""
    
    def test_graph_node_creation(self):
        """Test creating a graph node."""
        node_id = uuid4()
        node = GraphNode(id=node_id, data={"name": "test_task"})
        
        assert node.id == node_id
        assert node.data == {"name": "test_task"}
    
    def test_graph_node_immutable(self):
        """Test that graph nodes are immutable."""
        node_id = uuid4()
        node = GraphNode(id=node_id, data={"name": "test_task"})
        
        with pytest.raises(ValidationError):
            node.id = uuid4()  # Should fail due to frozen=True
    
    def test_graph_node_empty_data(self):
        """Test graph node with empty data."""
        node_id = uuid4()
        node = GraphNode(id=node_id)
        
        assert node.id == node_id
        assert node.data == {}


class TestGraphEdge:
    """Test GraphEdge model."""
    
    def test_graph_edge_creation(self):
        """Test creating a graph edge."""
        from_id = uuid4()
        to_id = uuid4()
        edge = GraphEdge(from_id=from_id, to_id=to_id)
        
        assert edge.from_id == from_id
        assert edge.to_id == to_id
        assert edge.relationship == "depends_on"
    
    def test_graph_edge_custom_relationship(self):
        """Test graph edge with custom relationship."""
        from_id = uuid4()
        to_id = uuid4()
        edge = GraphEdge(
            from_id=from_id, to_id=to_id, relationship="blocks"
        )
        
        assert edge.relationship == "blocks"
    
    def test_graph_edge_immutable(self):
        """Test that graph edges are immutable."""
        from_id = uuid4()
        to_id = uuid4()
        edge = GraphEdge(from_id=from_id, to_id=to_id)
        
        with pytest.raises(ValidationError):
            edge.from_id = uuid4()  # Should fail due to frozen=True


class TestRelatedFile:
    """Test RelatedFile model."""
    
    def test_related_file_creation(self):
        """Test creating a related file."""
        file_ref = RelatedFile(
            path="src/main.py",
            type=RelatedFileType.TO_MODIFY,
            description="Main application file"
        )
        
        assert file_ref.path == "src/main.py"
        assert file_ref.type == RelatedFileType.TO_MODIFY
        assert file_ref.description == "Main application file"
        assert file_ref.line_start is None
        assert file_ref.line_end is None
    
    def test_related_file_with_line_range(self):
        """Test related file with line range."""
        file_ref = RelatedFile(
            path="src/main.py",
            type=RelatedFileType.TO_MODIFY,
            description="Main application file",
            line_start=10,
            line_end=20
        )
        
        assert file_ref.line_start == 10
        assert file_ref.line_end == 20
    
    def test_related_file_invalid_line_range(self):
        """Test related file with invalid line range fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            RelatedFile(
                path="src/main.py",
                type=RelatedFileType.TO_MODIFY,
                description="Main application file",
                line_start=20,
                line_end=10  # End before start
            )
        
        assert "line_end must be >= line_start" in str(exc_info.value)
    
    def test_related_file_empty_path_fails(self):
        """Test related file with empty path fails validation."""
        with pytest.raises(ValidationError):
            RelatedFile(
                path="",
                type=RelatedFileType.TO_MODIFY,
                description="Test file"
            )
    
    def test_related_file_empty_description_fails(self):
        """Test related file with empty description fails validation."""
        with pytest.raises(ValidationError):
            RelatedFile(
                path="src/main.py",
                type=RelatedFileType.TO_MODIFY,
                description=""
            )
    
    def test_related_file_zero_line_numbers_fail(self):
        """Test related file with zero line numbers fail validation."""
        with pytest.raises(ValidationError):
            RelatedFile(
                path="src/main.py",
                type=RelatedFileType.TO_MODIFY,
                description="Test file",
                line_start=0
            )


class TestTaskDependency:
    """Test TaskDependency model."""
    
    def test_task_dependency_creation(self):
        """Test creating a task dependency."""
        task_id = uuid4()
        dependency = TaskDependency(task_id=task_id)
        
        assert dependency.task_id == task_id
    
    def test_task_dependency_immutable(self):
        """Test that task dependencies are immutable."""
        task_id = uuid4()
        dependency = TaskDependency(task_id=task_id)
        
        with pytest.raises(ValidationError):
            dependency.task_id = uuid4()  # Should fail due to frozen=True


class TestTask:
    """Test enhanced Task model with comprehensive validation."""
    
    def test_minimal_valid_task(self):
        """Test creating task with minimum required fields."""
        task = Task(
            name="Test Task",
            description="A test task for validation",
            implementation_guide="Follow the test procedure"
        )
        
        assert isinstance(task.id, UUID)
        assert task.name == "Test Task"
        assert task.description == "A test task for validation"
        assert task.implementation_guide == "Follow the test procedure"
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.P2
        assert len(task.dependencies) == 0
        assert len(task.related_files) == 0
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
    
    def test_task_with_all_fields(self):
        """Test creating task with all optional fields."""
        dependency_id = uuid4()
        related_file = RelatedFile(
            path="src/test.py",
            type=RelatedFileType.TO_MODIFY,
            description="Test file to modify"
        )
        
        task = Task(
            name="Complex Task",
            description="A complex task with all fields populated",
            implementation_guide="Detailed implementation steps",
            verification_criteria="How to verify completion",
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.P1,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=6,
            dependencies=[TaskDependency(task_id=dependency_id)],
            related_files=[related_file],
            category="Development",
            notes="Important task notes"
        )
        
        assert task.name == "Complex Task"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == Priority.P1
        assert task.complexity == ComplexityLevel.MODERATE
        assert task.estimated_hours == 6
        assert len(task.dependencies) == 1
        assert task.dependencies[0].task_id == dependency_id
        assert len(task.related_files) == 1
        assert task.category == "Development"
        assert task.notes == "Important task notes"
    
    def test_task_name_validation_empty_fails(self):
        """Test task with empty name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="",
                description="A test task",
                implementation_guide="Test guide"
            )
        
        # Pydantic v2 gives different error message for min_length validation
        assert "at least 1 character" in str(exc_info.value)
    
    def test_task_name_validation_whitespace_fails(self):
        """Test task with whitespace-only name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="   ",
                description="A test task",
                implementation_guide="Test guide"
            )
        
        assert "Task name cannot be empty" in str(exc_info.value)
    
    def test_task_name_validation_strips_whitespace(self):
        """Test task name strips leading/trailing whitespace."""
        task = Task(
            name="  Test Task  ",
            description="A test task",
            implementation_guide="Test guide"
        )
        
        assert task.name == "Test Task"
    
    def test_task_description_too_short_fails(self):
        """Test task with too short description fails validation."""
        with pytest.raises(ValidationError):
            Task(
                name="Test Task",
                description="Short",  # Less than 10 characters
                implementation_guide="Test implementation"
            )
    
    def test_task_implementation_guide_too_short_fails(self):
        """Test task with too short implementation guide fails validation."""
        with pytest.raises(ValidationError):
            Task(
                name="Test Task",
                description="A test task for validation",
                implementation_guide="Short"  # Less than 10 characters
            )
    
    def test_task_name_too_long_fails(self):
        """Test task with too long name fails validation."""
        with pytest.raises(ValidationError):
            Task(
                name="x" * 101,  # More than 100 characters
                description="A test task for validation",
                implementation_guide="Test implementation guide"
            )
    
    def test_task_category_too_long_fails(self):
        """Test task with too long category fails validation."""
        with pytest.raises(ValidationError):
            Task(
                name="Test Task",
                description="A test task for validation",
                implementation_guide="Test implementation guide",
                category="x" * 51  # More than 50 characters
            )
    
    def test_task_estimated_hours_validation_simple_too_high(self):
        """Test SIMPLE task with too many hours fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="Simple Task",
                description="Should be simple task",
                implementation_guide="Quick implementation",
                complexity=ComplexityLevel.SIMPLE,
                estimated_hours=8  # Too many for SIMPLE
            )
        
        assert "SIMPLE tasks should be ≤4 hours" in str(exc_info.value)
    
    def test_task_estimated_hours_validation_moderate_too_low(self):
        """Test MODERATE task with too few hours fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="Moderate Task",
                description="Should be moderate complexity",
                implementation_guide="Moderate implementation",
                complexity=ComplexityLevel.MODERATE,
                estimated_hours=3  # Too few for MODERATE
            )
        
        assert "MODERATE tasks should be 4-8 hours" in str(exc_info.value)
    
    def test_task_estimated_hours_validation_moderate_too_high(self):
        """Test MODERATE task with too many hours fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="Moderate Task",
                description="Should be moderate complexity",
                implementation_guide="Moderate implementation",
                complexity=ComplexityLevel.MODERATE,
                estimated_hours=10  # Too many for MODERATE
            )
        
        assert "MODERATE tasks should be 4-8 hours" in str(exc_info.value)
    
    def test_task_estimated_hours_validation_complex_valid(self):
        """Test COMPLEX task with valid hours passes validation."""
        task = Task(
            name="Complex Task",
            description="Complex task requiring significant work",
            implementation_guide="Complex implementation process",
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=12
        )
        
        assert task.estimated_hours == 12
    
    def test_task_estimated_hours_validation_epic_too_low(self):
        """Test EPIC task with too few hours fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="Epic Task",
                description="Should be epic complexity",
                implementation_guide="Epic implementation",
                complexity=ComplexityLevel.EPIC,
                estimated_hours=10  # Too few for EPIC
            )
        
        assert "EPIC tasks should be >16 hours" in str(exc_info.value)
    
    def test_task_estimated_hours_validation_too_high_fails(self):
        """Test task with estimated hours > 40 fails validation."""
        with pytest.raises(ValidationError):
            Task(
                name="Test Task",
                description="A test task for validation",
                implementation_guide="Test implementation guide",
                estimated_hours=50  # More than 40 hours
            )
    
    def test_task_estimated_hours_zero_fails(self):
        """Test task with zero estimated hours fails validation."""
        with pytest.raises(ValidationError):
            Task(
                name="Test Task",
                description="A test task for validation",
                implementation_guide="Test implementation guide",
                estimated_hours=0
            )
    
    def test_task_update_timestamp(self):
        """Test updating task timestamp."""
        task = Task(
            name="Test Task",
            description="A test task for validation",
            implementation_guide="Test implementation guide"
        )
        
        original_updated_at = task.updated_at
        task.update_timestamp()
        
        assert task.updated_at > original_updated_at
    
    def test_task_with_dependencies(self):
        """Test task with multiple dependencies."""
        dep1_id = uuid4()
        dep2_id = uuid4()
        
        task = Task(
            name="Dependent Task",
            description="Task with dependencies",
            implementation_guide="Implement after dependencies",
            dependencies=[
                TaskDependency(task_id=dep1_id),
                TaskDependency(task_id=dep2_id)
            ]
        )
        
        assert len(task.dependencies) == 2
        assert task.dependencies[0].task_id == dep1_id
        assert task.dependencies[1].task_id == dep2_id
    
    def test_task_with_related_files(self):
        """Test task with multiple related files."""
        file1 = RelatedFile(
            path="src/main.py",
            type=RelatedFileType.TO_MODIFY,
            description="Main file to modify"
        )
        file2 = RelatedFile(
            path="tests/test_main.py",
            type=RelatedFileType.CREATE,
            description="Test file to create"
        )
        
        task = Task(
            name="File Task",
            description="Task with related files",
            implementation_guide="Work with specified files",
            related_files=[file1, file2]
        )
        
        assert len(task.related_files) == 2
        assert task.related_files[0].path == "src/main.py"
        assert task.related_files[1].path == "tests/test_main.py"
    
    def test_task_model_config_validation(self):
        """Test task model configuration settings."""
        task = Task(
            name="Test Task",
            description="A test task for validation",
            implementation_guide="Test implementation guide"
        )
        
        # Test validate_assignment=True
        task.name = "Updated Task Name"  # Should work
        assert task.name == "Updated Task Name"
        
        # Test use_enum_values=True in serialization
        task_dict = task.model_dump()
        assert task_dict["status"] == "PENDING"  # String value, not enum
        assert task_dict["priority"] == "P2"  # String value, not enum