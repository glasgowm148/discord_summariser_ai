# Configuration

Configuration lives in `config/.env`. Keep real tokens out of git.

```bash
cp config/.env.example config/.env
```

Then fill values for Discord, OpenAI, Twitter/X, Reddit, HackMD, and Meta as needed.

## DiscordChatExporter

Set token in `config/.env` instead of pasting it into scripts or docs:

```bash
DISCORD_TOKEN=your_discord_token
```

Export one channel:

```bash
DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli export \
  --channel 669989266478202917 \
  --token "$DISCORD_TOKEN" \
  --after 2025-01-01 \
  --format Json \
  -o output/$(date -u '+%Y-%m-%d')/guild
```

Export guild:

```bash
DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli exportguild \
  --guild 668903786361651200 \
  --token "$DISCORD_TOKEN" \
  --format Json \
  --include-vc false \
  --parallel 10 \
  -p 1000 \
  -o output/$(date -u '+%Y-%m-%d')/guild
```

List channels:

```bash
DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli channels \
  --guild 668903786361651200 \
  --token "$DISCORD_TOKEN"
```

Useful Ergo channel IDs:

| Channel ID | Channel |
| --- | --- |
| 669989266478202917 | Lobby / development |
| 964131671609860126 | Infra / Interop / rosen |
| 840313005064585246 | Development / dev-support |
| 849659724495323206 | Development / ergoscript-support |
| 670288337747312646 | Lobby / support |
| 908347206988365864 | Lobby / ask-anything |
| 668913770059268125 | Lobby / mining |
| 1073483623459725322 | Development / dev-tooling |
| 802828538197573682 | Financial / sigmausd |

Guild IDs:

| Guild ID | Guild |
| --- | --- |
| 668903786361651200 | Ergo |
| 597161478075711499 | Phenotype |
