"""Service for uploading summaries to HackMD."""
import os
import requests
from typing import List, Optional

from services.base_service import BaseService


class HackMDService(BaseService):
    """Handles uploading summaries to HackMD."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HackMD service.
        
        :param api_key: HackMD API key. If not provided, tries to read from environment.
        """
        super().__init__()
        self.api_key = api_key or os.getenv('HACKMD_API_KEY')
        
        if not self.api_key:
            self.logger.error("No HackMD API key provided")
            raise ValueError("HackMD API key is required")
        
        # Call initialize method
        self.initialize()

    def initialize(self) -> None:
        """
        Initialize service-specific resources.
        
        This method is required by the BaseService abstract class.
        For HackMDService, we'll do basic validation and logging.
        """
        self.logger.info("Initializing HackMDService")
        
        # Validate API key
        if not self.api_key:
            self.handle_error(
                ValueError("HackMD API key is not set"),
                {"context": "HackMDService initialization"}
            )

    def create_note(self, title: str, content: str) -> Optional[str]:
        """
        Create a new note on HackMD.
        
        :param title: Title of the note
        :param content: Markdown content of the note
        :return: URL of the created note, or None if creation fails
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'title': title,
                'content': content,
                'readPermission': 'owner',  # Only the creator can read
                'writePermission': 'owner'  # Only the creator can write
            }
            
            response = requests.post(
                'https://api.hackmd.io/v1/notes', 
                json=payload, 
                headers=headers
            )
            
            response.raise_for_status()
            note_data = response.json()
            
            # Return the public URL of the note
            return f"https://hackmd.io/{note_data['id']}"
        
        except Exception as e:
            self.handle_error(e, {"context": "HackMD note creation"})
            return None
