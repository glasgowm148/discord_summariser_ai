import os
from pathlib import Path
import requests
from typing import Dict
from openai import OpenAI
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
            
        self.client = OpenAI(api_key=self.openai_api_key)
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
                params={"access_token": self.fb_access_token},
                timeout=10
            )
            response.raise_for_status()
            
            # Test Instagram credentials
            response = requests.get(
                f"https://graph.facebook.com/v17.0/{self.ig_account_id}",
                params={"access_token": self.ig_access_token},
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            self.handle_error(e, {"context": "Meta API credential verification"})
            raise

    async def format_content(self, content: str, platform: str) -> str:
        """Use GPT-4o-mini to format content appropriately for the specified platform."""
        try:
            prompt = self._get_platform_prompt(platform, content)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                temperature=0.3,
                max_tokens=1500
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
                         "Select the best bullet-point from the given content to highlight in a Facebook post. "
                         "Strip any markdown formatting and ensure the post is engaging and professional.",
                "user": f"Please select the best bullet-point from this content for Facebook and strip markdown:\n\n{content}"
            },
            "instagram": {
                "system": "You are a social media expert specializing in Instagram content. "
                         "Select the best bullet-point from the given content to highlight in an Instagram post. "
                         "Strip any markdown formatting and ensure the post uses appropriate spacing, emojis, and hashtags strategically.",
                "user": f"Please select the best bullet-point from this content for Instagram and strip markdown:\n\n{content}"
            }
        }
        return prompts.get(platform, prompts["facebook"])

    async def generate_image(self, content: str) -> str:
        """Generate an abstract, artistic image to accompany the content without any text."""
        try:
            # Extract key themes from the content
            theme_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract 2-3 key visual themes from the content, focusing on abstract concepts that would make an interesting image. Avoid any text or literal representations. Format as a comma-separated list."},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=100
            )
            themes = theme_response.choices[0].message.content.strip()
            
            # Create an artistic prompt that avoids text
            image_prompt = f"Create an abstract, artistic visualization inspired by these themes: {themes}. Use vibrant colors and geometric shapes. Do not include any text, letters, numbers, or words. Make it suitable for social media. Style: modern digital art, minimalist, professional."
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024",
                quality="standard",
                style="vivid"
            )
            return response.data[0].url
        except Exception as e:
            self.handle_error(e, {"context": "Image generation"})
            raise

    async def post_to_facebook(self, content: str) -> None:
        """Post formatted content to Facebook."""
        try:
            formatted_content = await self.format_content(content, "facebook")
            image_url = await self.generate_image(content)
            payload = {
                "message": formatted_content,
                "access_token": self.fb_access_token,
                "url": image_url
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
            image_url = await self.generate_image(content)
            payload = {
                "caption": formatted_content,
                "image_url": image_url,
                "access_token": self.ig_access_token
            }
            
            response = requests.post(self.ig_api_url, data=payload)
            response.raise_for_status()
            self.logger.info("Successfully posted to Instagram")
            
        except Exception as e:
            self.handle_error(e, {"context": "Instagram posting"})
            raise

    async def prompt_and_post(self, content: str) -> None:
        """Format content and prompt user before posting to Meta platforms."""
        try:
            # Format content for both platforms
            fb_content = await self.format_content(content, "facebook")
            ig_content = await self.format_content(content, "instagram")
            fb_image_url = await self.generate_image(content)
            ig_image_url = await self.generate_image(content)
            
            print("\nProposed Facebook post:")
            print("-" * 50)
            print(fb_content)
            print(f"Image URL: {fb_image_url}")
            print("-" * 50)
            
            print("\nProposed Instagram post:")
            print("-" * 50)
            print(ig_content)
            print(f"Image URL: {ig_image_url}")
            print("-" * 50)
            
            response = input("\nWould you like to post to Meta platforms? (y/n): ")
            if response.lower() == 'y':
                await self.post_to_facebook(fb_content)
                await self.post_to_instagram(ig_content)
                print("Content posted to Meta platforms successfully!")
            else:
                print("Post cancelled.")
                
        except Exception as e:
            self.handle_error(e, {"context": "Meta prompt and post"})
            raise
