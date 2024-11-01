"""Base service class with common functionality."""
import logging
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod

class BaseService(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle errors in a consistent way across services."""
        error_type = type(error).__name__
        error_message = str(error)
        
        log_message = f"{error_type}: {error_message}"
        if context:
            log_message += f"\nContext: {context}"
            
        self.logger.error(log_message, exc_info=True)
        
    def validate_input(self, data: Any, required_fields: list) -> bool:
        """Validate input data has required fields."""
        if data is None:
            self.logger.error("Input data is None")
            return False
            
        if isinstance(data, dict):
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.logger.error(f"Missing required fields: {missing_fields}")
                return False
                
        return True
        
    @abstractmethod
    def initialize(self) -> None:
        """Initialize service-specific resources."""
        pass
