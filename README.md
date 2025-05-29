# Synology DSM - RSS-based Torrent Downloader

This tool allows you to check RSS feeds more frequently than the built-in 10-minute interval limitation in Synology Download Station.

## ⚙️ Configuration

Settings are provided via environment variables.

| Environment Variable | Description                                                                                               | Comment            |
| -------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------- |
| `DSM_HOST`           | The base URL of the DSM API                                                                               | _required_              |
| `DSM_USERNAME`       | DSM account username                                                                                      | _required_              |
| `DSM_PASSWORD`       | DSM account password                                                                                      | _required_              |
| `STORAGE_DIR`        | Directory used as a volume inside the container. This is where internal data (e.g. seen items) is stored. | `/app/storage`          |
| `FEED_FILE`          | Path to the feed configuration JSON file inside the container.                                            | `/app/config/feed.json` |

## 📄 `feed.json` Format

The feed configuration defines multiple feed sources and their download destinations.

```json
{
  "movies": {
    "rss": "https://example.com/movies.rss",
    "destination": "Downloads/Movies"
  },
  "series": {
    "rss": "https://example.com/series.rss",
    "destination": "Downloads/Series"
  }
}
```

## Example compose file

```yaml
services:
  app:
    image: varhegyisz/dsm-rss-downloader
    environment:
      - DSM_HOST=https://192.168.0.180:5001
      - DSM_USERNAME=admin
      - DSM_PASSWORD=verySecurePassword
    volumes:
      - ./src/storage:/app/storage
      - ./src/config/feed.json:/app/config/feed.json
```