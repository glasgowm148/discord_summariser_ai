import os
from pathlib import Path
import requests
from typing import Optional, Dict, Any
import openai
from dotenv import load_dotenv
from .base_service import BaseService

class MetaService(BaseService):
    def __init__(self):
        super().__init__()
        # Load environment variables from config/.env
        env_path = Path('config/.env')
        if not env_path.exists():
            raise FileNotFoundError("config/.env file not found. Please copy config/.env.example to config/.env and fill in your values.")
        load_dotenv(env_path)
        
        self.fb_access_token = os.getenv("META_FB_ACCESS_TOKEN")
        self.ig_access_token = os.getenv("META_IG_ACCESS_TOKEN")
        self.fb_page_id = os.getenv("META_FB_PAGE_ID")
        self.ig_account_id = os.getenv("META_IG_ACCOUNT_ID")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not all([self.fb_access_token, self.ig_access_token, self.fb_page_id, 
                   self.ig_account_id, self.openai_api_key]):
            raise ValueError("Missing required Meta API credentials in .env file")
            
        openai.api_key = self.openai_api_key
        self.fb_api_url = f"https://graph.facebook.com/v17.0/{self.fb_page_id}/feed"
        self.ig_api_url = f"https://graph.facebook.com/v17.0/{self.ig_account_id}/media"
        
    def initialize(self) -> None:
        """Initialize service-specific resources."""
        # Verify API credentials are valid
        self._verify_credentials()

    def _verify_credentials(self) -> None:
        """Verify Meta API credentials are valid."""
        try:
            # Test Facebook credentials
            response = requests.get(
                f"https://graph.facebook.com/v17.0/{self.fb_page_id}",
                params={"access_token": self.fb_access_token}
            )
            response.raise_for_status()
            
            # Test Instagram credentials
            response = requests.get(
                f"https://graph.facebook.com/v17.0/{self.ig_account_id}",
                params={"access_token": self.ig_access_token}
            )
            response.raise_for_status()
        except Exception as e:
            self.handle_error(e, {"context": "Meta API credential verification"})
            raise

    async def format_content(self, content: str, platform: str) -> str:
        """Use GPT-4 to format content appropriately for the specified platform."""
        try:
            prompt = self._get_platform_prompt(platform, content)
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.handle_error(e, {"context": f"Content formatting for {platform}"})
            raise

    def _get_platform_prompt(self, platform: str, content: str) -> Dict[str, str]:
        """Get platform-specific prompt for content formatting."""
        prompts = {
            "facebook": {
                "system": "You are a social media expert specializing in Facebook content. "
                         "Format the given content into an engaging Facebook post that maximizes "
                         "engagement while maintaining professionalism. Keep hashtags minimal and strategic.",
                "user": f"Please format this content for Facebook:\n\n{content}"
            },
            "instagram": {
                "system": "You are a social media expert specializing in Instagram content. "
                         "Format the given content into an engaging Instagram post that uses "
                         "appropriate spacing, emojis, and hashtags strategically. Focus on "
                         "visual appeal and engagement.",
                "user": f"Please format this content for Instagram:\n\n{content}"
            }
        }
        return prompts.get(platform, prompts["facebook"])

    async def post_to_facebook(self, content: str) -> None:
        """Post formatted content to Facebook."""
        try:
            formatted_content = await self.format_content(content, "facebook")
            payload = {
                "message": formatted_content,
                "access_token": self.fb_access_token
            }
            
            response = requests.post(self.fb_api_url, data=payload)
            response.raise_for_status()
            self.logger.info("Successfully posted to Facebook")
            
        except Exception as e:
            self.handle_error(e, {"context": "Facebook posting"})
            raise

    async def post_to_instagram(self, content: str) -> None:
        """Post formatted content to Instagram."""
        try:
            formatted_content = await self.format_content(content, "instagram")
            # Note: Instagram requires an image for posts
            # This implementation assumes text-only posts for now
            # TODO: Implement image handling for Instagram posts
            self.logger.warning("Instagram posting requires image content - not implemented")
            
        except Exception as e:
            self.handle_error(e, {"context": "Instagram posting"})
            raise

    async def prompt_and_post(self, content: str) -> None:
        """Format content and prompt user before posting to Meta platforms."""
        try:
            # Format content for both platforms
            fb_content = await self.format_content(content, "facebook")
            ig_content = await self.format_content(content, "instagram")
            
            print("\nProposed Facebook post:")
            print("-" * 50)
            print(fb_content)
            print("-" * 50)
            
            print("\nProposed Instagram post:")
            print("-" * 50)
            print(ig_content)
            print("-" * 50)
            
            response = input("\nWould you like to post to Meta platforms? (y/n): ")
            if response.lower() == 'y':
                await self.post_to_facebook(fb_content)
                # await self.post_to_instagram(ig_content)  # Uncomment when image handling is implemented
                print("Content posted to Meta platforms successfully!")
            else:
                print("Post cancelled.")
                
        except Exception as e:
            self.handle_error(e, {"context": "Meta prompt and post"})
            raise
