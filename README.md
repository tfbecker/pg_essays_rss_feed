# This repository is inspired by: [https://github.com/ofou/graham-essays](https://github.com/ofou/graham-essays)

It exposes all the essays as an RSS feed and can be hosted, for example, on a server.

I use it to get notified of new essays automatically and use this with my RSS reader.

The official RSS feed on the website: [https://paulgraham.com/rss.html](https://paulgraham.com/rss.html) is broken.

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

