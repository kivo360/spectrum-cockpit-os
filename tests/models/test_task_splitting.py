"""
Test suite for task splitting models and functionality.

Tests the core task splitting models, schemas, and validation logic
following TDD principles.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Any

from src.models.task_splitting import (
    UpdateMode,
    TaskSplitRequest,
    TaskTemplate,
    SplitResult,
    SplitOperation,
    TaskDecomposition,
    GranularityRules
)
from src.models.task import Task, TaskStatus, Priority, ComplexityLevel
from src.schemas.splitting_schemas import (
    TaskSplitRequestSchema,
    TaskTemplateSchema,
    SplitResultSchema
)

class TestUpdateMode:
    """Test the UpdateMode enum."""
    
    def test_update_mode_values(self):
        """Test that UpdateMode has all required values."""
        assert UpdateMode.APPEND == "append"
        assert UpdateMode.OVERWRITE == "overwrite"
        assert UpdateMode.SELECTIVE == "selective"
        assert UpdateMode.CLEAR_ALL_TASKS == "clearAllTasks"
    
    def test_update_mode_from_string(self):
        """Test creating UpdateMode from string values."""
        assert UpdateMode("append") == UpdateMode.APPEND
        assert UpdateMode("overwrite") == UpdateMode.OVERWRITE
        assert UpdateMode("selective") == UpdateMode.SELECTIVE
        assert UpdateMode("clearAllTasks") == UpdateMode.CLEAR_ALL_TASKS


class TestGranularityRules:
    """Test granularity validation rules."""
    
    def test_default_granularity_rules(self):
        """Test default granularity rule values."""
        rules = GranularityRules()
        assert rules.min_task_duration_hours == 1
        assert rules.max_task_duration_hours == 16
        assert rules.max_subtasks_per_split == 10
        assert rules.max_task_raw_length == 5000
        assert rules.max_depth_levels == 3
        assert rules.max_task_name_length == 100
        assert rules.min_description_length == 10
    
    def test_custom_granularity_rules(self):
        """Test creating custom granularity rules."""
        rules = GranularityRules(
            min_task_duration_hours=2,
            max_task_duration_hours=8,
            max_subtasks_per_split=5
        )
        assert rules.min_task_duration_hours == 2
        assert rules.max_task_duration_hours == 8
        assert rules.max_subtasks_per_split == 5
    
    def test_validate_task_count(self):
        """Test task count validation."""
        rules = GranularityRules(max_subtasks_per_split=3)
        
        # Valid count
        assert rules.validate_task_count(2) is True
        assert rules.validate_task_count(3) is True
        
        # Invalid count
        assert rules.validate_task_count(4) is False
        assert rules.validate_task_count(0) is False
    
    def test_validate_task_name_length(self):
        """Test task name length validation."""
        rules = GranularityRules()
        
        # Valid lengths
        assert rules.validate_task_name_length("Valid task name") is True
        assert rules.validate_task_name_length("A" * 100) is True
        
        # Invalid lengths
        assert rules.validate_task_name_length("") is False
        assert rules.validate_task_name_length("A" * 101) is False
    
    def test_validate_description_length(self):
        """Test description length validation."""
        rules = GranularityRules()
        
        # Valid lengths
        assert rules.validate_description_length("Valid description here") is True
        
        # Invalid lengths
        assert rules.validate_description_length("Too short") is False
        assert rules.validate_description_length("") is False


class TestTaskTemplate:
    """Test TaskTemplate model."""
    
    def test_create_basic_template(self):
        """Test creating a basic task template."""
        template = TaskTemplate(
            name="Setup Development Environment",
            description="Initialize project with required dependencies and configuration",
            implementation_guide="1. Install Node.js\n2. Run npm install\n3. Configure environment",
            dependencies=[]
        )
        
        assert template.name == "Setup Development Environment"
        assert template.description == "Initialize project with required dependencies and configuration"
        assert template.implementation_guide == "1. Install Node.js\n2. Run npm install\n3. Configure environment"
        assert template.dependencies == []
        assert template.notes is None
        assert template.related_files == []
        assert template.verification_criteria is None
    
    def test_create_template_with_dependencies(self):
        """Test creating template with dependencies."""
        template = TaskTemplate(
            name="Implement User Authentication",
            description="Create login/logout functionality with session management",
            implementation_guide="Use NextAuth.js for authentication flow",
            dependencies=["Setup Development Environment", "Database Schema Design"],
            notes="Consider OAuth providers",
            verification_criteria="User can successfully login and logout"
        )
        
        assert template.dependencies == ["Setup Development Environment", "Database Schema Design"]
        assert template.notes == "Consider OAuth providers"
        assert template.verification_criteria == "User can successfully login and logout"
    
    def test_template_to_task_conversion(self):
        """Test converting template to actual Task."""
        template = TaskTemplate(
            name="Test Task",
            description="Test task description for conversion",
            implementation_guide="Test implementation steps",
            dependencies=[]
        )
        
        task = template.to_task()
        
        assert isinstance(task, Task)
        assert task.name == template.name
        assert task.description == template.description
        assert task.implementation_guide == template.implementation_guide
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.P2  # Default priority
    
    def test_template_validation(self):
        """Test template validation rules."""
        # Valid template
        valid_template = TaskTemplate(
            name="Valid Name",
            description="This is a valid description that meets minimum length requirements",
            implementation_guide="Valid implementation guide",
            dependencies=[]
        )
        assert valid_template.name == "Valid Name"
        
        # Test name length validation in schema
        with pytest.raises(ValueError, match="String should have at most 100 characters"):
            TaskTemplate(
                name="A" * 101,  # Too long
                description="Valid description that meets minimum requirements",
                implementation_guide="Valid guide",
                dependencies=[]
            )


class TestTaskSplitRequest:
    """Test TaskSplitRequest model."""
    
    def test_create_basic_split_request(self):
        """Test creating a basic task split request."""
        templates = [
            TaskTemplate(
                name="Task 1",
                description="First task description with sufficient length",
                implementation_guide="Implementation steps for task 1",
                dependencies=[]
            )
        ]
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=templates,
            global_analysis_result="Build a web application"
        )
        
        assert request.update_mode == UpdateMode.CLEAR_ALL_TASKS
        assert len(request.task_templates) == 1
        assert request.global_analysis_result == "Build a web application"
        assert isinstance(request.granularity_rules, GranularityRules)
    
    def test_split_request_with_custom_rules(self):
        """Test split request with custom granularity rules."""
        templates = [
            TaskTemplate(
                name="Task 1",
                description="Task description with adequate length for testing",
                implementation_guide="Implementation guide",
                dependencies=[]
            )
        ]
        
        custom_rules = GranularityRules(max_subtasks_per_split=5)
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.APPEND,
            task_templates=templates,
            granularity_rules=custom_rules
        )
        
        assert request.granularity_rules.max_subtasks_per_split == 5
    
    def test_validate_request_task_count(self):
        """Test validation of task count in request."""
        # Create templates that exceed max count
        templates = []
        for i in range(12):  # Exceeds default max of 10
            templates.append(TaskTemplate(
                name=f"Task {i}",
                description=f"Description for task {i} with sufficient length",
                implementation_guide=f"Implementation for task {i}",
                dependencies=[]
            ))
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=templates
        )
        
        # Should be able to create but validation should fail
        assert not request.validate_granularity()
    
    def test_validate_granularity_success(self):
        """Test successful granularity validation."""
        templates = [
            TaskTemplate(
                name="Valid Task",
                description="This is a valid task description with adequate length",
                implementation_guide="Valid implementation guide",
                dependencies=[]
            )
        ]
        
        request = TaskSplitRequest(
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            task_templates=templates
        )
        
        assert request.validate_granularity() is True


class TestSplitOperation:
    """Test SplitOperation model for tracking operations."""
    
    def test_create_split_operation(self):
        """Test creating a split operation record."""
        operation = SplitOperation(
            operation_type="split_tasks",
            update_mode=UpdateMode.SELECTIVE,
            tasks_before_count=5,
            tasks_after_count=8,
            tasks_added=3,
            tasks_updated=2,
            tasks_removed=0
        )
        
        assert operation.operation_type == "split_tasks"
        assert operation.update_mode == UpdateMode.SELECTIVE
        assert operation.tasks_before_count == 5
        assert operation.tasks_after_count == 8
        assert operation.tasks_added == 3
        assert operation.tasks_updated == 2
        assert operation.tasks_removed == 0
        assert isinstance(operation.timestamp, datetime)
    
    def test_operation_summary(self):
        """Test operation summary generation."""
        operation = SplitOperation(
            operation_type="split_tasks",
            update_mode=UpdateMode.OVERWRITE,
            tasks_before_count=10,
            tasks_after_count=7,
            tasks_added=2,
            tasks_updated=0,
            tasks_removed=5
        )
        
        summary = operation.get_summary()
        assert "overwrite" in summary.lower()
        assert "10" in summary  # before count
        assert "7" in summary   # after count
        assert "2" in summary   # added
        assert "5" in summary   # removed


class TestSplitResult:
    """Test SplitResult model."""
    
    def test_create_successful_result(self):
        """Test creating a successful split result."""
        created_tasks = [
            Task(
                name="Task 1",
                description="First task created from split operation",
                implementation_guide="Implementation guide for task 1"
            )
        ]
        
        operation = SplitOperation(
            operation_type="split_tasks",
            update_mode=UpdateMode.CLEAR_ALL_TASKS,
            tasks_before_count=0,
            tasks_after_count=1,
            tasks_added=1,
            tasks_updated=0,
            tasks_removed=0
        )
        
        result = SplitResult(
            success=True,
            created_tasks=created_tasks,
            operation=operation,
            message="Successfully created 1 task"
        )
        
        assert result.success is True
        assert len(result.created_tasks) == 1
        assert result.created_tasks[0].name == "Task 1"
        assert result.operation.tasks_added == 1
        assert result.message == "Successfully created 1 task"
        assert result.errors == []
    
    def test_create_failed_result(self):
        """Test creating a failed split result."""
        result = SplitResult(
            success=False,
            created_tasks=[],
            operation=None,
            message="Split operation failed",
            errors=["Task name too long", "Invalid dependency reference"]
        )
        
        assert result.success is False
        assert len(result.created_tasks) == 0
        assert result.operation is None
        assert "failed" in result.message
        assert len(result.errors) == 2


class TestTaskDecomposition:
    """Test TaskDecomposition utility class."""
    
    def test_create_decomposition(self):
        """Test creating a task decomposition."""
        original_task = Task(
            name="Build Web Application",
            description="Create a full-stack web application with authentication",
            implementation_guide="Use modern frameworks and best practices"
        )
        
        subtasks = [
            TaskTemplate(
                name="Setup Development Environment",
                description="Initialize project structure and dependencies",
                implementation_guide="Use create-react-app and setup backend",
                dependencies=[]
            ),
            TaskTemplate(
                name="Implement Authentication",
                description="Create user login and registration system",
                implementation_guide="Use JWT tokens and secure password hashing",
                dependencies=["Setup Development Environment"]
            )
        ]
        
        decomposition = TaskDecomposition(
            original_task=original_task,
            subtask_templates=subtasks,
            decomposition_strategy="functional_modules"
        )
        
        assert decomposition.original_task.name == "Build Web Application"
        assert len(decomposition.subtask_templates) == 2
        assert decomposition.decomposition_strategy == "functional_modules"
        assert isinstance(decomposition.created_at, datetime)
    
    def test_decomposition_validation(self):
        """Test decomposition validation."""
        original_task = Task(
            name="Simple Task",
            description="A simple task for testing decomposition validation",
            implementation_guide="Simple implementation"
        )
        
        # Valid decomposition
        valid_subtasks = [
            TaskTemplate(
                name="Subtask 1",
                description="First subtask with adequate description length",
                implementation_guide="Implementation 1",
                dependencies=[]
            )
        ]
        
        decomposition = TaskDecomposition(
            original_task=original_task,
            subtask_templates=valid_subtasks
        )
        
        assert decomposition.validate() is True
        
        # Invalid decomposition - too many subtasks
        invalid_subtasks = []
        for i in range(15):  # Exceeds default max of 10
            invalid_subtasks.append(TaskTemplate(
                name=f"Task {i}",
                description=f"Description for subtask {i} with sufficient length",
                implementation_guide=f"Implementation {i}",
                dependencies=[]
            ))
        
        invalid_decomposition = TaskDecomposition(
            original_task=original_task,
            subtask_templates=invalid_subtasks
        )
        
        assert invalid_decomposition.validate() is False


class TestSplittingSchemas:
    """Test Pydantic schemas for task splitting."""
    
    def test_task_split_request_schema(self):
        """Test TaskSplitRequest schema validation."""
        valid_data = {
            "update_mode": "clearAllTasks",
            "task_templates": [
                {
                    "name": "Test Task",
                    "description": "Test task description with adequate length",
                    "implementation_guide": "Test implementation guide",
                    "dependencies": []
                }
            ],
            "global_analysis_result": "Test analysis"
        }
        
        validated = TaskSplitRequestSchema.model_validate(valid_data)
        
        assert validated.update_mode == "clearAllTasks"
        assert len(validated.task_templates) == 1
        assert validated.global_analysis_result == "Test analysis"
    
    def test_task_template_schema(self):
        """Test TaskTemplate schema validation."""
        valid_data = {
            "name": "Valid Task Name",
            "description": "This is a valid task description with sufficient length",
            "implementation_guide": "Valid implementation guide with steps",
            "dependencies": ["Dependency Task"],
            "notes": "Additional notes",
            "verification_criteria": "Success criteria"
        }
        
        validated = TaskTemplateSchema.model_validate(valid_data)
        
        assert validated.name == "Valid Task Name"
        assert len(validated.dependencies) == 1
        assert validated.notes == "Additional notes"
    
    def test_split_result_schema(self):
        """Test SplitResult schema validation."""
        valid_data = {
            "success": True,
            "created_tasks": [],
            "operation": {
                "operation_type": "split_tasks",
                "update_mode": "append",
                "tasks_before_count": 0,
                "tasks_after_count": 1,
                "tasks_added": 1,
                "tasks_updated": 0,
                "tasks_removed": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "message": "Success",
            "errors": []
        }
        
        validated = SplitResultSchema.model_validate(valid_data)
        
        assert validated.success is True
        assert validated.message == "Success"
        assert len(validated.errors) == 0