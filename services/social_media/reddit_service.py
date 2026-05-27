# services/reddit_service.py
from playwright.async_api import async_playwright
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import re
import traceback

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

from services.base_service import BaseService

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

    async def _login(self, page):
        """Handle Reddit login process."""
        try:
            # Navigate to login page
            self.logger.info("Loading login page...")
            await page.goto('https://www.reddit.com/login')
            await page.wait_for_load_state('networkidle')

            # Capture and log page content for debugging
            self.logger.info("Current URL: " + page.url)

            # Fill login form using specific selectors
            self.logger.info("Filling login form...")

            # Username field with debugging
            username_selector = 'input[name="username"][type="text"]'
            self.logger.info(f"Looking for username field with selector: {username_selector}")
            username_input = page.locator(username_selector)
            is_visible = await username_input.is_visible()
            self.logger.info(f"Username field visible: {is_visible}")
            if not is_visible:
                page_content = await page.content()
                self.logger.info(f"Page content: {page_content[:500]}...")  # Log first 500 chars
                raise Exception("Username field not visible")

            await username_input.fill(self.username)
            self.logger.info("Username filled")

            # Password field with debugging
            # trunk-ignore(bandit/B105)
            password_selector = 'input[name="password"][type="password"]'
            self.logger.info(f"Looking for password field with selector: {password_selector}")
            password_input = page.locator(password_selector)
            is_visible = await password_input.is_visible()
            self.logger.info(f"Password field visible: {is_visible}")
            await password_input.fill(self.password)
            self.logger.info("Password filled")

            # Try pressing Enter instead of clicking the button
            self.logger.info("Pressing Enter to submit...")
            await password_input.press('Enter')

            # Wait for navigation
            self.logger.info("Waiting for navigation...")
            await page.wait_for_load_state('networkidle')
            self.logger.info(f"Navigation complete. New URL: {page.url}")

            # Try to access old reddit directly
            self.logger.info("Attempting to access old.reddit.com...")
            await page.goto('https://old.reddit.com')
            await page.wait_for_load_state('networkidle')
            self.logger.info(f"Old Reddit URL: {page.url}")

            # Check if we're logged in by looking for specific old.reddit.com elements
            karma_selector = 'span.userkarma'
            if await page.locator(karma_selector).is_visible():
                self.logger.info("Successfully logged in (karma element visible)")
                return True

            # If we can see a login form on old.reddit, we're not logged in
            if await page.locator('form#login-form').is_visible():
                self.logger.error("Not logged in (login form visible on old.reddit)")
                return False

            # Final check - try to access user profile
            self.logger.info("Attempting to access user profile...")
            await page.goto(f'https://old.reddit.com/user/{self.username}')
            await page.wait_for_load_state('networkidle')

            if '/login' in page.url:
                self.logger.error("Login failed - redirected to login page")
                return False

            self.logger.info("Successfully verified login")
            return True

        except Exception as e:
            self.handle_error(e, {
                "context": "Reddit login",
                "url": page.url if page else "unknown",
                "username_visible": await username_input.is_visible() if 'username_input' in locals() else "unknown",
                "password_visible": await password_input.is_visible() if 'password_input' in locals() else "unknown"
            })
            return False

    async def post_to_reddit(self, title: str, content: str) -> bool:
        """Post content to Reddit.
        If content is a valid URL, post as a link post.
        Otherwise, post as a self post."""
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=not self.debug,
                )

                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )

                page = await context.new_page()
                if self.debug:
                    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

                # Login
                self.logger.info("Logging into Reddit...")
                if not await self._login(page):
                    return False

                # Navigate to submission page
                self.logger.info(f"Navigating to r/{self.subreddit}...")
                await page.goto(f'https://old.reddit.com/r/{self.subreddit}/submit')
                await page.wait_for_load_state('networkidle')

                # Determine if content is a valid URL
                url_pattern = re.compile(r'^https?://\S+$')
                is_url = url_pattern.match(content)

                if is_url:
                    # Click the link tab
                    self.logger.info("Selecting link post type...")
                    link_tab = page.locator('a.link-button.choice')
                    await link_tab.click()

                    # Wait for URL input to be visible
                    self.logger.info("Waiting for URL input field...")
                    url_input = page.locator('input#url')
                    await url_input.wait_for(state='visible', timeout=10000)

                    # Fill in URL
                    self.logger.info(f"Filling post URL: {content}")
                    await url_input.fill(content)
                else:
                    # Click the text tab
                    self.logger.info("Selecting text post type...")
                    text_tab = page.locator('a.text-button.choice')
                    await text_tab.click()

                    # Fill in text content
                    self.logger.info("Filling post content...")
                    text_input = page.locator('textarea[name="text"]')
                    await text_input.fill(content)

                # Fill in the title
                self.logger.info("Filling post title...")
                title_input = page.locator('textarea[name="title"]')
                await title_input.fill(title)

                # Optional preview
                if os.getenv('REDDIT_PREVIEW', 'false').lower() == 'true':
                    await page.locator('button[name="preview"]').click()
                    input("Check the preview and press Enter to continue...")

                # Submit the form
                self.logger.info("Submitting post...")
                submit_button = page.locator('button[name="submit"]')
                await submit_button.click()

                # Increase timeout and add more robust navigation checks
                self.logger.info("Waiting for post confirmation...")
                try:
                    # Wait for comments page with extended timeout
                    await page.wait_for_url("**/comments/**", timeout=60000)
                    self.logger.info(f"Successfully posted to r/{self.subreddit}")
                    return True
                except Exception as nav_error:
                    # Fallback navigation check
                    self.logger.warning(f"Navigation timeout: {nav_error}")

                    # Check current page for potential success indicators
                    current_url = page.url
                    self.logger.info(f"Current page URL: {current_url}")

                    # Check for specific success indicators
                    success_indicators = [
                        '/comments/',  # Part of URL
                        'submitted successfully',  # Potential text
                        'your post has been submitted',  # Another potential text
                    ]

                    page_content = await page.content()
                    for indicator in success_indicators:
                        if indicator.lower() in page_content.lower():
                            self.logger.info(f"Success indicator found: {indicator}")
                            return True

                    # If no success indicators, capture and log page content for debugging
                    self.logger.error("Failed to confirm post submission")
                    self.logger.error(f"Page content: {page_content[:1000]}...")  # Log first 1000 chars
                    return False

            except Exception as e:
                error_details = {
                    "context": "Reddit posting",
                    "title": title,
                    "content": content,
                    "traceback": traceback.format_exc()
                }
                self.handle_error(e, error_details)
                return False
            finally:
                if self.debug:
                    input("Press Enter to close the browser...")
