#!/bin/bash

# Run the Angular Ventures RSS feed generator once
python angular_ventures_rss.py

# Start the Flask server with gunicorn
gunicorn --bind 0.0.0.0:3000 server:app --log-level debug 