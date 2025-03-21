from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class StorageInterface(ABC):
    """Base interface for storage implementations."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the storage.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def store_reviews(self, reviews: List[Dict[str, Any]]) -> bool:
        """Store reviews in the storage.
        
        Args:
            reviews: List of review dictionaries to store.
            
        Returns:
            bool: True if storage successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_reviews(self) -> List[Dict[str, Any]]:
        """Retrieve reviews from the storage.
        
        Returns:
            List of review dictionaries.
        """
        pass
    
    @abstractmethod
    def clear_data(self) -> bool:
        """Clear all data in the storage.
        
        Returns:
            bool: True if clearing successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the storage."""
        pass 