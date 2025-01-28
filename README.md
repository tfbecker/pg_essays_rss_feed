# This repository is inspired by: [https://github.com/ofou/graham-essays](https://github.com/ofou/graham-essays)

It exposes all the essays as an RSS feed and can be hosted, for example, on a server.

I use it to get notified of new essays automatically and use this with my RSS reader.

The official RSS feed on the website: [https://paulgraham.com/rss.html](https://paulgraham.com/rss.html) is broken.

# RSS Feed Generator

This service generates and serves RSS feeds for:
- Angular Ventures Blog
- Paul Graham Essays (optional)

## Features

- Scrapes the latest posts from Angular Ventures Blog
- Optionally scrapes Paul Graham's essays
- Serves feeds via a web interface
- Docker containerized for easy deployment

## Quick Start

1. Run only Angular Ventures feed (default):
```bash
docker-compose up
```

2. Run both Angular Ventures and Paul Graham feeds:
```bash
docker-compose run --service-ports angular-ventures-rss ./start_all.sh
```

## Accessing the Feeds

Once running, the feeds are available at:

- Web Interface: http://localhost:3000
- Angular Ventures RSS: http://localhost:3000/angular
- Paul Graham Essays RSS: http://localhost:3000/pg (when running with start_all.sh)

## Configuration

The service runs on port 3000 by default. You can modify this in the docker-compose.yml file if needed.

## Scripts

- `start_angular.sh`: Generates and serves only the Angular Ventures feed
- `start_all.sh`: Generates and serves both Angular Ventures and Paul Graham feeds

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

2. Start the Docker container:
    ```sh
    docker-compose up
    ```

The application will be available on port `80`.

