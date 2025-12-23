#!/bin/bash
while true; do
    python groq_rss.py
    sleep 3600  # Run every hour
done
