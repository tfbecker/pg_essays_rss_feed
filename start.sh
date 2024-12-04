#!/bin/bash

# Start the Angular Ventures RSS feed generator in the background
python angular_ventures_rss.py &

# Start the Flask server with gunicorn
gunicorn --bind 0.0.0.0:3000 pg_essays:app --log-level debug
