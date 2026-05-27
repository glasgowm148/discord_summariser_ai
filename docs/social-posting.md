# Social Posting

Posting is opt-in during interactive runs. `scripts/summarise.py` prints output and asks before sending.

## Discord

Service: `services/social_media/discord_service.py`

Environment: `DISCORD_WEBHOOK_URL` plus optional regional webhook URLs.

Flow:

1. Final summary is generated.
2. User confirms send.
3. Code chooses weekly or daily webhook behavior based on days covered.

## Reddit

Service: `services/social_media/reddit_service.py`

Environment:

```bash
REDDIT_USERNAME=...
REDDIT_PASSWORD=...
REDDIT_SUBREDDIT=ergonauts
REDDIT_DEBUG=false
REDDIT_PREVIEW=false
```

Implementation uses Playwright against old Reddit. `REDDIT_DEBUG=true` opens browser visibly. `REDDIT_PREVIEW=true` pauses before submit.

## Twitter/X

Service: `services/social_media/twitter_service.py`

Requires OAuth values in `config/.env`. Main flow previews formatted text and posts after confirmation.

## Meta

Service: `services/meta_service.py`

Requires Facebook/Instagram access tokens and account/page IDs. Flow asks before posting.

## Reaction Bots

`services/social_media/reddit_comment_bot.py` watches Discord reactions:

- custom `reddit` emoji -> generate Reddit title/content and post;
- custom `twitter` emoji -> post message to Twitter/X.

Run:

```bash
python services/social_media/reddit_comment_bot.py
```

Logs:

```text
output/YYYY-MM-DD/logs/discord_bot.log
```

`services/social_media/announcement_to_regional.py` watches announcement channel and posts translated versions to regional webhooks.
