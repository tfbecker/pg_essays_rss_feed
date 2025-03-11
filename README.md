# This repository is inspired by: [https://github.com/ofou/graham-essays](https://github.com/ofou/graham-essays)

It exposes all the essays as an RSS feed and can be hosted, for example, on a server.

I use it to get notified of new essays automatically and use this with my RSS reader.

The official RSS feed on the website: [https://paulgraham.com/rss.html](https://paulgraham.com/rss.html) is broken.

# RSS Feed Generator

This service generates and serves RSS feeds for:
- Angular Ventures Blog
- Paul Graham Essays
- Gwern Branwen's Changelog

## Features

- Scrapes the latest posts from Angular Ventures Blog
- Scrapes Paul Graham's essays
- Scrapes Gwern Branwen's changelog updates
- Serves feeds via a web interface
- Docker containerized for easy deployment

## Quick Start

1. Run only Angular Ventures feed:
```bash
docker-compose run --service-ports angular-ventures-rss
```

2. Run only Gwern RSS feed:
```bash
docker-compose run --service-ports gwern-rss
```

3. Run all feeds (Angular Ventures, Paul Graham, and Gwern):
```bash
docker-compose run --service-ports all-rss-feeds
```

## Accessing the Feeds

Once running, the feeds are available at:

- Web Interface: http://localhost:3000
- Angular Ventures RSS: http://localhost:3000/angular
- Paul Graham Essays RSS: http://localhost:3000/pg
- Gwern Changelog RSS: http://localhost:3000/gwern

## Configuration

The service runs on port 3000 by default. You can modify this in the docker-compose.yml file if needed.

## Scripts

- `start_angular.sh`: Generates and serves only the Angular Ventures feed
- `start_gwern.sh`: Generates and serves only the Gwern changelog feed
- `start_all.sh`: Generates and serves all feeds (Angular Ventures, Paul Graham, and Gwern)

## Development

To build from source:
```bash
docker-compose build
```

To rebuild without cache:
```bash
docker-compose build --no-cache
```

## Hosting via Docker

You can host this repository using Docker. Follow these steps:

1. Build the Docker image:
    ```sh
    docker-compose build
    ```

2. Start the Docker container with all feeds:
    ```sh
    docker-compose up all-rss-feeds
    ```

The application will be available on port `3000`.

## Credit

- Paul Graham Essays RSS implementation inspired by [https://github.com/ofou/graham-essays](https://github.com/ofou/graham-essays)
- Gwern RSS implementation inspired by [https://github.com/49Indium/gwern-rss](https://github.com/49Indium/gwern-rss)

