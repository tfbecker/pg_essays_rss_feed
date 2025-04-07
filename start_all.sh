#!/bin/bash

# Function to run the scrapers
run_scrapers() {
    echo "Running RSS feed generators at $(date)"
    python angular_ventures_rss.py
    python pg_essays.py
    python gwern_rss.py
    python anthropic_rss.py
    python openai_rss.py
}

# Run immediately on startup
run_scrapers

# Start the Flask server with gunicorn in the background
gunicorn --bind 0.0.0.0:3000 server:app --log-level info &

# Run scrapers every hour
while true; do
    sleep 3600
    run_scrapers
done 