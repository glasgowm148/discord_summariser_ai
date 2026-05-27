"""Lazy posting adapters for optional social integrations."""


class PostingAdapters:
    """Create optional posting services only when user chooses a post action."""

    def __init__(self):
        self.discord = None
        self.twitter = None
        self.reddit = None
        self.meta = None

    def discord_service(self):
        if self.discord is None:
            from services.social_media.discord_service import DiscordService
            self.discord = DiscordService()
        return self.discord

    def twitter_service(self):
        if self.twitter is None:
            from services.social_media.twitter_service import TwitterService
            self.twitter = TwitterService()
        return self.twitter

    def reddit_service(self):
        if self.reddit is None:
            from services.social_media.reddit_service import RedditService
            self.reddit = RedditService()
        return self.reddit

    def meta_service(self):
        if self.meta is None:
            from services.meta_service import MetaService
            self.meta = MetaService()
        return self.meta
