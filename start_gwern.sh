#!/bin/bash

# Run Gwern RSS feed generator
python gwern_rss.py

# Start the Flask server with gunicorn
gunicorn --bind 0.0.0.0:3000 server:app --log-level debug 