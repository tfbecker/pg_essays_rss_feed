#!/bin/bash

# Run both RSS feed generators
python angular_ventures_rss.py
python pg_essays.py

# Start the Flask server with gunicorn
gunicorn --bind 0.0.0.0:3000 server:app --log-level debug 