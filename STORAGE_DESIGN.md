# Storage Architecture Design

> **Start Small → Validate → Expand → Scale**
> Following incremental methodology for reliable development

## 🎯 Design Philosophy

### Incremental Implementation Approach
1. **Start Small (Week 1):** Basic abstract interfaces with in-memory mock implementation
2. **Validate (Week 1):** Comprehensive test suite validates core patterns work
3. **Expand (Week 2):** NetworkX graph + DuckDB table implementations
4. **Scale (Week 3):** Production backends, performance optimization, error handling

### Core Principles
- **Abstract First:** Clear interfaces before concrete implementations
- **Test-Driven:** Tests drive implementation, not the reverse
- **Incremental Validation:** Each step proven before proceeding
- **Pydantic v2 Native:** Modern validation patterns throughout

## 🏗️ Abstract Storage Interfaces

### Graph Storage Interface
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID

class GraphNode(BaseModel):
    """Node in the task dependency graph"""
    id: UUID = Field(..., description="Unique node identifier")
    data: Dict[str, Any] = Field(default_factory=dict, description="Node metadata")
    
    model_config = {"frozen": True}  # Immutable nodes

class GraphEdge(BaseModel):
    """Directed edge representing dependency relationship"""
    from_id: UUID = Field(..., description="Source node ID")
    to_id: UUID = Field(..., description="Target node ID") 
    relationship: str = Field("depends_on", description="Edge relationship type")
    
    model_config = {"frozen": True}  # Immutable edges

class AbstractGraphStorage(ABC):
    """Abstract interface for graph-based task dependency storage"""
    
    @abstractmethod
    async def add_node(self, node: GraphNode) -> bool:
        """Add node to graph. Returns True if added, False if exists"""
        pass
    
    @abstractmethod
    async def add_edge(self, edge: GraphEdge) -> bool:
        """Add edge to graph. Returns True if added, False if creates cycle"""
        pass
    
    @abstractmethod
    async def get_node(self, node_id: UUID) -> Optional[GraphNode]:
        """Retrieve node by ID"""
        pass
    
    @abstractmethod
    async def get_dependencies(self, node_id: UUID) -> List[UUID]:
        """Get all nodes this node depends on"""
        pass
    
    @abstractmethod
    async def get_dependents(self, node_id: UUID) -> List[UUID]:
        """Get all nodes that depend on this node"""
        pass
    
    @abstractmethod
    async def has_cycle(self) -> bool:
        """Check if graph contains cycles"""
        pass
    
    @abstractmethod
    async def topological_sort(self) -> List[UUID]:
        """Return topologically sorted node IDs"""
        pass
```

### Table Storage Interface  
```python
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class AbstractTableStorage(ABC, Generic[T]):
    """Abstract interface for tabular task data storage"""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    @abstractmethod
    async def create(self, item: T) -> T:
        """Create new item in table"""
        pass
    
    @abstractmethod
    async def get_by_id(self, item_id: UUID) -> Optional[T]:
        """Retrieve item by ID"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[T]:
        """Get all items"""
        pass
    
    @abstractmethod
    async def update(self, item: T) -> T:
        """Update existing item"""
        pass
    
    @abstractmethod  
    async def delete(self, item_id: UUID) -> bool:
        """Delete item by ID. Returns True if deleted"""
        pass
    
    @abstractmethod
    async def query(self, filters: Dict[str, Any]) -> List[T]:
        """Query items with filters"""
        pass
```

## 📊 Enhanced Task Schema (Pydantic v2)

### Core Task Model
```python
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Annotated
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, ConfigDict

class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS" 
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"

class Priority(str, Enum):
    """Task priority levels"""
    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium (Default)
    P3 = "P3"  # Low

class ComplexityLevel(str, Enum):
    """Task complexity indicators"""
    SIMPLE = "SIMPLE"      # 1-4 hours
    MODERATE = "MODERATE"   # 4-8 hours  
    COMPLEX = "COMPLEX"     # 8-16 hours
    EPIC = "EPIC"          # 16+ hours (should be split)

class RelatedFileType(str, Enum):
    """Types of file relationships"""
    TO_MODIFY = "TO_MODIFY"
    REFERENCE = "REFERENCE"
    CREATE = "CREATE"
    DEPENDENCY = "DEPENDENCY"
    OTHER = "OTHER"

class RelatedFile(BaseModel):
    """File associated with task execution"""
    path: str = Field(..., min_length=1, description="File path")
    type: RelatedFileType = Field(..., description="Relationship type")
    description: str = Field(..., min_length=1, description="File role description")
    line_start: Optional[int] = Field(None, gt=0, description="Start line number")
    line_end: Optional[int] = Field(None, gt=0, description="End line number")
    
    @field_validator('line_end')
    @classmethod
    def validate_line_range(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure line_end >= line_start if both provided"""
        if v is not None and info.data.get('line_start') is not None:
            if v < info.data['line_start']:
                raise ValueError('line_end must be >= line_start')
        return v

class TaskDependency(BaseModel):
    """Task dependency reference"""
    task_id: UUID = Field(..., description="UUID of dependent task")
    
    model_config = ConfigDict(frozen=True)

# UUID validation pattern for string UUIDs
UUID_V4_REGEX = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'

class Task(BaseModel):
    """Enhanced task model with 15+ structured fields"""
    
    # Core identification
    id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    name: str = Field(..., max_length=100, min_length=1, description="Task name")
    
    # Core content  
    description: str = Field(..., min_length=10, description="Detailed task description")
    implementation_guide: str = Field(..., min_length=10, description="How to implement this task")
    verification_criteria: Optional[str] = Field(None, description="How to verify completion")
    
    # Status and metadata
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current execution status")
    priority: Priority = Field(default=Priority.P2, description="Task priority level")
    complexity: Optional[ComplexityLevel] = Field(None, description="Estimated complexity")
    estimated_hours: Optional[int] = Field(None, gt=0, le=40, description="Estimated work hours")
    
    # Relationships
    dependencies: List[TaskDependency] = Field(default_factory=list, description="Task dependencies")
    related_files: List[RelatedFile] = Field(default_factory=list, description="Associated files")
    
    # Organization
    category: Optional[str] = Field(None, max_length=50, description="Task category")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Validation
    model_config = ConfigDict(
        validate_assignment=True,  # Validate on field assignment
        use_enum_values=True,      # Use enum values in serialization
        frozen=False               # Allow updates
    )
    
    @field_validator('name')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Ensure task name follows proper format"""
        if not v.strip():
            raise ValueError('Task name cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('estimated_hours')
    @classmethod 
    def validate_complexity_hours_alignment(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure estimated hours align with complexity level"""
        if v is None:
            return v
            
        complexity = info.data.get('complexity')
        if complexity == ComplexityLevel.SIMPLE and v > 4:
            raise ValueError('SIMPLE tasks should be ≤4 hours')
        elif complexity == ComplexityLevel.MODERATE and (v <= 4 or v > 8):
            raise ValueError('MODERATE tasks should be 4-8 hours')  
        elif complexity == ComplexityLevel.COMPLEX and (v <= 8 or v > 16):
            raise ValueError('COMPLEX tasks should be 8-16 hours')
        elif complexity == ComplexityLevel.EPIC and v <= 16:
            raise ValueError('EPIC tasks should be >16 hours (consider splitting)')
            
        return v
```

## 🧪 Test-Driven Development Strategy

### Phase 1: Abstract Interface Tests
```python
# tests/test_abstract_interfaces.py
import pytest
from abc import ABC
from uuid import uuid4
from src.storage.abstractions import AbstractGraphStorage, AbstractTableStorage
from src.models.task import Task, GraphNode, GraphEdge

class TestAbstractGraphStorage:
    """Test abstract graph storage interface compliance"""
    
    @pytest.fixture
    def mock_graph_storage(self):
        """Create mock implementation for testing"""
        class MockGraphStorage(AbstractGraphStorage):
            def __init__(self):
                self.nodes = {}
                self.edges = []
                
            async def add_node(self, node: GraphNode) -> bool:
                if node.id in self.nodes:
                    return False
                self.nodes[node.id] = node
                return True
                
            # ... implement all abstract methods
            
        return MockGraphStorage()
    
    async def test_node_creation_and_retrieval(self, mock_graph_storage):
        """Test basic node operations work"""
        node_id = uuid4()
        node = GraphNode(id=node_id, data={'name': 'test_task'})
        
        # Test creation
        assert await mock_graph_storage.add_node(node) == True
        
        # Test retrieval  
        retrieved = await mock_graph_storage.get_node(node_id)
        assert retrieved == node
        
        # Test duplicate prevention
        assert await mock_graph_storage.add_node(node) == False
    
    async def test_dependency_graph_operations(self, mock_graph_storage):
        """Test dependency relationship management"""
        # Create nodes
        task1_id, task2_id = uuid4(), uuid4()
        node1 = GraphNode(id=task1_id, data={'name': 'task1'})
        node2 = GraphNode(id=task2_id, data={'name': 'task2'})
        
        await mock_graph_storage.add_node(node1)
        await mock_graph_storage.add_node(node2)
        
        # Create dependency: task2 depends on task1
        edge = GraphEdge(from_id=task2_id, to_id=task1_id)
        assert await mock_graph_storage.add_edge(edge) == True
        
        # Test dependency queries
        dependencies = await mock_graph_storage.get_dependencies(task2_id)
        assert task1_id in dependencies
        
        dependents = await mock_graph_storage.get_dependents(task1_id)
        assert task2_id in dependents
```

### Phase 2: Pydantic Model Tests  
```python
# tests/test_task_models.py
import pytest
from uuid import uuid4
from pydantic import ValidationError
from src.models.task import Task, TaskStatus, Priority, ComplexityLevel, RelatedFile

class TestTaskModel:
    """Test enhanced task model validation"""
    
    def test_minimal_valid_task(self):
        """Test creating task with minimum required fields"""
        task = Task(
            name="Test Task",
            description="A test task for validation",
            implementation_guide="Follow the test procedure"
        )
        
        assert task.id is not None
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.P2
        assert len(task.dependencies) == 0
        assert task.created_at is not None
    
    def test_task_name_validation(self):
        """Test task name validation rules"""
        # Empty name should fail
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="",
                description="A test task", 
                implementation_guide="Test guide"
            )
        assert "Task name cannot be empty" in str(exc_info.value)
        
        # Whitespace-only name should fail
        with pytest.raises(ValidationError):
            Task(
                name="   ",
                description="A test task",
                implementation_guide="Test guide" 
            )
    
    def test_complexity_hours_validation(self):
        """Test complexity-hours alignment validation"""
        # SIMPLE task with too many hours should fail
        with pytest.raises(ValidationError) as exc_info:
            Task(
                name="Simple Task",
                description="Should be simple",
                implementation_guide="Quick implementation",
                complexity=ComplexityLevel.SIMPLE,
                estimated_hours=8  # Too many for SIMPLE
            )
        assert "SIMPLE tasks should be ≤4 hours" in str(exc_info.value)
        
        # Valid MODERATE task should pass
        task = Task(
            name="Moderate Task", 
            description="Moderate complexity task",
            implementation_guide="Moderate implementation",
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=6
        )
        assert task.estimated_hours == 6
    
    def test_related_file_line_range_validation(self):
        """Test file line range validation"""
        # Invalid line range should fail
        with pytest.raises(ValidationError) as exc_info:
            RelatedFile(
                path="test.py",
                type="TO_MODIFY", 
                description="Test file",
                line_start=10,
                line_end=5  # End before start
            )
        assert "line_end must be >= line_start" in str(exc_info.value)
        
        # Valid line range should pass
        file_ref = RelatedFile(
            path="test.py",
            type="TO_MODIFY",
            description="Test file", 
            line_start=5,
            line_end=10
        )
        assert file_ref.line_start == 5
        assert file_ref.line_end == 10
```

## 🚀 Implementation Roadmap

### Week 1: Foundation (Start Small + Validate)
- [ ] **Day 1-2:** Abstract interfaces + basic Pydantic models
- [ ] **Day 3-4:** Comprehensive test suite (80+ tests)  
- [ ] **Day 5:** In-memory mock implementations for validation
- [ ] **Validation Criteria:** All tests pass, interfaces proven

### Week 2: Core Implementations (Expand)
- [ ] **Day 1-2:** NetworkX graph storage implementation
- [ ] **Day 3-4:** DuckDB table storage implementation  
- [ ] **Day 5:** Integration testing and validation
- [ ] **Validation Criteria:** Real backends work with existing tests

### Week 3: Production Ready (Scale)
- [ ] **Day 1-2:** Error handling, connection pooling, retries
- [ ] **Day 3-4:** Performance optimization and benchmarking
- [ ] **Day 5:** Production deployment configuration
- [ ] **Validation Criteria:** Performance targets met, production ready

## 🔧 Development Commands

### Setup Development Environment
```bash
# Install UV and dependencies  
uv add pydantic>=2.5.0
uv add pytest>=7.4.0 pytest-asyncio>=0.21.0 pytest-cov>=4.1.0
uv add networkx>=3.2.0  
uv add duckdb>=0.9.0

# Development dependencies
uv add --dev ruff>=0.1.0 mypy>=1.7.0 pre-commit>=3.5.0
```

### Testing Commands
```bash
# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Type checking  
uv run mypy src/ tests/

# Linting and formatting
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Quality Gates
- **Test Coverage:** ≥90% line coverage, ≥80% branch coverage
- **Type Safety:** 100% mypy compliance
- **Code Quality:** 100% ruff compliance  
- **Performance:** <100ms for single operations, <1s for batch operations

## 📋 Success Criteria

### Phase 1 Success (Week 1)
- [ ] Abstract interfaces defined with full type safety
- [ ] 50+ comprehensive tests covering all edge cases
- [ ] In-memory implementations validate all patterns
- [ ] Pydantic v2 models with complete validation

### Phase 2 Success (Week 2)  
- [ ] NetworkX and DuckDB implementations pass all tests
- [ ] Performance benchmarks established
- [ ] Integration testing with real data flows
- [ ] Error handling for all failure modes

### Phase 3 Success (Week 3)
- [ ] Production deployment configurations
- [ ] Monitoring and observability integration
- [ ] Performance optimization complete
- [ ] Documentation and examples ready

---

**Next Action:** Create abstract interface files and begin test suite development