# services/twitter_service.py
import os
from pathlib import Path
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

class TwitterService:
    def __init__(self):
        # Load environment variables from config/.env
        env_path = Path('config/.env')
        if not env_path.exists():
            raise FileNotFoundError("config/.env file not found. Please copy config/.env.example to config/.env and fill in your values.")
        load_dotenv(env_path)
        
        self.auth = OAuth1(
            os.getenv("TWITTER_CONSUMER_KEY"),
            os.getenv("TWITTER_CONSUMER_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        self.api_url = "https://api.twitter.com/2/tweets"
        self.twitter_mapping = {
            "Rosen Bridge": "@RosenBridge_erg",
            "Keystone Wallet": "@KeystoneWallet",
            "Nautilus Wallet": "@NautilusWallet",
            "Zengate": "@ZengateGlobal",
            "PaideiaDAO": "@PaideiaDAO",
            "NautilusWallet": "@NautilusWallet",
            "SigmaUSD": "@SigmaUSD",
            "Dexy_Ergo": "@Dexy_Ergo",
            "ChainCash": "@ChainCash",
            "SatergoWallet": "@SatergoWallet",
            "LithosProtocol": "@LithosProtocol",
            "Sigmanauts": "@Sigmanauts",
        }

    def send_tweet(self, content: str) -> None:
        """Send a tweet with proper Twitter handle mapping."""
        mapped_content = self._map_twitter_handles(content)
        payload = {"text": mapped_content}
        
        print("Sending tweet...")
        try:
            response = requests.post(self.api_url, auth=self.auth, json=payload, timeout=10)  # Added timeout
            if response.status_code in (200, 201):
                print("Tweet sent successfully.")
            else:
                error_detail = response.json().get('detail') or response.json().get('errors', response.json())
                print(f"Error sending tweet: {error_detail}")
        except Exception as e:
            print(f"Exception while sending tweet: {e}")

    def _map_twitter_handles(self, content: str) -> str:
        """Map content keywords to proper Twitter handles."""
        mapped_content = content
        for key, value in self.twitter_mapping.items():
            mapped_content = mapped_content.replace(key, value)
        return mapped_content
