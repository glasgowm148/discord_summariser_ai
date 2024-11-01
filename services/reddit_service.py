# services/reddit_service.py
from playwright.sync_api import sync_playwright
import os
from pathlib import Path
from dotenv import load_dotenv
from services.base_service import BaseService
import logging

class RedditService(BaseService):
    def __init__(self):
        super().__init__()
        env_path = Path('config/.env')
        if not env_path.exists():
            raise FileNotFoundError("config/.env file not found")
        load_dotenv(env_path)
        
        self.username = os.getenv('REDDIT_USERNAME')
        self.password = os.getenv('REDDIT_PASSWORD')
        self.subreddit = os.getenv('REDDIT_SUBREDDIT', 'ergonauts')
        self.debug = os.getenv('REDDIT_DEBUG', 'false').lower() == 'true'
        self.initialize()

    def initialize(self) -> None:
        """Initialize service (implementing abstract method from BaseService)."""
        pass
    
    def _login(self, page) -> bool:
            """Handle Reddit login process."""
            try:
                # Navigate to login page
                self.logger.info("Loading login page...")
                page.goto('https://www.reddit.com/login')
                page.wait_for_load_state('networkidle')
                
                # Capture and log page content for debugging
                self.logger.info("Current URL: " + page.url)
                
                # Fill login form using specific selectors
                self.logger.info("Filling login form...")
                
                # Username field with debugging
                username_selector = 'input[name="username"][type="text"]'
                self.logger.info(f"Looking for username field with selector: {username_selector}")
                username_input = page.locator(username_selector)
                is_visible = username_input.is_visible()
                self.logger.info(f"Username field visible: {is_visible}")
                if not is_visible:
                    page_content = page.content()
                    self.logger.info(f"Page content: {page_content[:500]}...")  # Log first 500 chars
                    raise Exception("Username field not visible")
                
                username_input.fill(self.username)
                self.logger.info("Username filled")
                
                # Password field with debugging
                password_selector = 'input[name="password"][type="password"]'
                self.logger.info(f"Looking for password field with selector: {password_selector}")
                password_input = page.locator(password_selector)
                is_visible = password_input.is_visible()
                self.logger.info(f"Password field visible: {is_visible}")
                password_input.fill(self.password)
                self.logger.info("Password filled")
                
                # Try pressing Enter instead of clicking the button
                self.logger.info("Pressing Enter to submit...")
                password_input.press('Enter')
                
                # Wait for navigation
                self.logger.info("Waiting for navigation...")
                page.wait_for_load_state('networkidle')
                self.logger.info(f"Navigation complete. New URL: {page.url}")
                
                # Try to access old reddit directly
                self.logger.info("Attempting to access old.reddit.com...")
                page.goto('https://old.reddit.com')
                page.wait_for_load_state('networkidle')
                self.logger.info(f"Old Reddit URL: {page.url}")
                
                # Check if we're logged in by looking for specific old.reddit.com elements
                karma_selector = 'span.userkarma'
                if page.locator(karma_selector).is_visible():
                    self.logger.info("Successfully logged in (karma element visible)")
                    return True
                    
                # If we can see a login form on old.reddit, we're not logged in
                if page.locator('form#login-form').is_visible():
                    self.logger.error("Not logged in (login form visible on old.reddit)")
                    return False
                
                # Final check - try to access user profile
                self.logger.info("Attempting to access user profile...")
                page.goto(f'https://old.reddit.com/user/{self.username}')
                page.wait_for_load_state('networkidle')
                
                if '/login' in page.url:
                    self.logger.error("Login failed - redirected to login page")
                    return False
                    
                self.logger.info("Successfully verified login")
                return True
                    
            except Exception as e:
                self.handle_error(e, {
                    "context": "Reddit login",
                    "url": page.url if page else "unknown",
                    "username_visible": username_input.is_visible() if 'username_input' in locals() else "unknown",
                    "password_visible": password_input.is_visible() if 'password_input' in locals() else "unknown"
                })
                return False

    def post_to_reddit(self, title: str, content: str) -> bool:
        """Post content to Reddit."""
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=not self.debug,
                )
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                
                page = context.new_page()
                if self.debug:
                    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
                
                # Login
                self.logger.info("Logging into Reddit...")
                if not self._login(page):
                    return False

                # Navigate to submission page
                self.logger.info(f"Navigating to r/{self.subreddit}...")
                page.goto(f'https://old.reddit.com/r/{self.subreddit}/submit')
                page.wait_for_load_state('networkidle')
                
                # Click the text tab using the correct selector from the screenshot
                self.logger.info("Selecting text post type...")
                page.locator('a.text-button.choice').click()
                
                # Fill in the form
                self.logger.info("Filling post title...")
                title_input = page.locator('textarea[name="title"]')
                title_input.fill(title)
                
                self.logger.info("Filling post content...")
                text_input = page.locator('textarea[name="text"]')
                text_input.fill(content)
                
                # Optional preview
                if os.getenv('REDDIT_PREVIEW', 'false').lower() == 'true':
                    page.locator('button[name="preview"]').click()
                    input("Check the preview and press Enter to continue...")
                
                # Submit the form
                self.logger.info("Submitting post...")
                submit_button = page.locator('button[name="submit"]')
                submit_button.click()
                
                # Wait for submission to complete
                page.wait_for_url("**/comments/**", timeout=30000)
                
                self.logger.info(f"Successfully posted to r/{self.subreddit}")
                return True
                
            except Exception as e:
                self.handle_error(e, {"context": "Reddit posting"})
                return False
            finally:
                if self.debug:
                    input("Press Enter to close the browser...")

   