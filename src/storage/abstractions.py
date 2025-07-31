"""Abstract storage interfaces for graph and table data."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel

from ..models.task import GraphEdge, GraphNode

# Generic type for table storage
T = TypeVar("T", bound=BaseModel)


class AbstractGraphStorage(ABC):
    """Abstract interface for graph-based task dependency storage."""
    
    @abstractmethod
    async def add_node(self, node: GraphNode) -> bool:
        """Add node to graph.
        
        Args:
            node: The graph node to add
            
        Returns:
            True if added successfully, False if node already exists
        """
        pass
    
    @abstractmethod
    async def add_edge(self, edge: GraphEdge) -> bool:
        """Add edge to graph.
        
        Args:
            edge: The graph edge to add
            
        Returns:
            True if added successfully, False if would create cycle
        """
        pass
    
    @abstractmethod
    async def get_node(self, node_id: UUID) -> Optional[GraphNode]:
        """Retrieve node by ID.
        
        Args:
            node_id: The node identifier
            
        Returns:
            GraphNode if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def remove_node(self, node_id: UUID) -> bool:
        """Remove node and all associated edges.
        
        Args:
            node_id: The node identifier
            
        Returns:
            True if removed, False if node didn't exist
        """
        pass
    
    @abstractmethod
    async def remove_edge(self, edge: GraphEdge) -> bool:
        """Remove specific edge from graph.
        
        Args:
            edge: The edge to remove
            
        Returns:
            True if removed, False if edge didn't exist
        """
        pass
    
    @abstractmethod
    async def get_dependencies(self, node_id: UUID) -> List[UUID]:
        """Get all nodes this node depends on.
        
        Args:
            node_id: The node identifier
            
        Returns:
            List of node IDs this node depends on
        """
        pass
    
    @abstractmethod
    async def get_dependents(self, node_id: UUID) -> List[UUID]:
        """Get all nodes that depend on this node.
        
        Args:
            node_id: The node identifier
            
        Returns:
            List of node IDs that depend on this node
        """
        pass
    
    @abstractmethod
    async def has_cycle(self) -> bool:
        """Check if graph contains cycles.
        
        Returns:
            True if graph has cycles, False otherwise
        """
        pass
    
    @abstractmethod
    async def topological_sort(self) -> List[UUID]:
        """Return topologically sorted node IDs.
        
        Returns:
            List of node IDs in topological order
            
        Raises:
            ValueError: If graph contains cycles
        """
        pass
    
    @abstractmethod
    async def get_all_nodes(self) -> List[GraphNode]:
        """Get all nodes in the graph.
        
        Returns:
            List of all graph nodes
        """
        pass
    
    @abstractmethod
    async def get_all_edges(self) -> List[GraphEdge]:
        """Get all edges in the graph.
        
        Returns:
            List of all graph edges
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        pass


class AbstractTableStorage(ABC, Generic[T]):
    """Abstract interface for tabular data storage."""
    
    def __init__(self, model_class: Type[T]) -> None:
        """Initialize with the model class for type safety.
        
        Args:
            model_class: The Pydantic model class this storage handles
        """
        self.model_class = model_class
    
    @abstractmethod
    async def create(self, item: T) -> T:
        """Create new item in table.
        
        Args:
            item: The item to create
            
        Returns:
            The created item
            
        Raises:
            ValueError: If item with same ID already exists
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, item_id: UUID) -> Optional[T]:
        """Retrieve item by ID.
        
        Args:
            item_id: The item identifier
            
        Returns:
            Item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_all(self) -> List[T]:
        """Get all items.
        
        Returns:
            List of all items in storage
        """
        pass
    
    @abstractmethod
    async def update(self, item: T) -> T:
        """Update existing item.
        
        Args:
            item: The item to update (must have existing ID)
            
        Returns:
            The updated item
            
        Raises:
            ValueError: If item doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: UUID) -> bool:
        """Delete item by ID.
        
        Args:
            item_id: The item identifier
            
        Returns:
            True if deleted, False if item didn't exist
        """
        pass
    
    @abstractmethod
    async def query(self, filters: Dict[str, Any]) -> List[T]:
        """Query items with filters.
        
        Args:
            filters: Dictionary of field names to values for filtering
            
        Returns:
            List of items matching the filters
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total count of items.
        
        Returns:
            Number of items in storage
        """
        pass
    
    @abstractmethod
    async def exists(self, item_id: UUID) -> bool:
        """Check if item exists.
        
        Args:
            item_id: The item identifier
            
        Returns:
            True if item exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Remove all items from storage."""
        pass