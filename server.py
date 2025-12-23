from flask import Flask, send_file, abort, jsonify
import os
import json
from datetime import datetime
from logger import RSSLogger

app = Flask(__name__)
logger = RSSLogger("rss_server")

@app.route('/')
def home():
    # Check which feeds are available
    feeds = []
    if os.path.exists('angular_ventures_feed.xml'):
        feeds.append('<li><a href="/angular">Angular Ventures Blog RSS Feed</a></li>')
    if os.path.exists('pg_essays.xml'):
        feeds.append('<li><a href="/pg">Paul Graham Essays RSS Feed</a></li>')
    if os.path.exists('gwern_feed.xml'):
        feeds.append('<li><a href="/gwern">Gwern Changelog RSS Feed</a></li>')
    if os.path.exists('anthropic_feed.xml'):
        feeds.append('<li><a href="/anthropic">Anthropic Research RSS Feed</a></li>')
    if os.path.exists('openai_feed.xml'):
        feeds.append('<li><a href="/openai">OpenAI Research RSS Feed</a></li>')
    if os.path.exists('groq_feed.xml'):
        feeds.append('<li><a href="/groq">Groq Blog RSS Feed</a></li>')

    return f'''
    <html>
        <body>
            <h1>RSS Feeds</h1>
            <ul>
                {''.join(feeds)}
            </ul>
            <p><a href="/status">View Feed Status</a></p>
        </body>
    </html>
    '''

@app.route('/status')
def status():
    status_data = {
        "server_time": datetime.now().isoformat(),
        "feeds": {}
    }
    
    # Check each feed file and its last modification time
    feeds = {
        'angular': 'angular_ventures_feed.xml',
        'pg': 'pg_essays.xml',
        'gwern': 'gwern_feed.xml',
        'anthropic': 'anthropic_feed.xml',
        'openai': 'openai_feed.xml',
        'groq': 'groq_feed.xml'
    }
    
    for feed_name, feed_file in feeds.items():
        if os.path.exists(feed_file):
            mtime = datetime.fromtimestamp(os.path.getmtime(feed_file))
            status_data["feeds"][feed_name] = {
                "available": True,
                "last_updated": mtime.isoformat(),
                "age_minutes": round((datetime.now() - mtime).total_seconds() / 60, 2)
            }
        else:
            status_data["feeds"][feed_name] = {
                "available": False,
                "last_updated": None,
                "age_minutes": None
            }
    
    return jsonify(status_data)

@app.route('/angular')
def serve_angular_rss():
    try:
        return send_file('angular_ventures_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        logger.log_scrape_error("Angular Ventures RSS feed not found")
        abort(404, description="Angular Ventures RSS feed not found")

@app.route('/pg')
def serve_pg_rss():
    try:
        return send_file('pg_essays.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        logger.log_scrape_error("Paul Graham Essays RSS feed not found")
        abort(404, description="Paul Graham Essays RSS feed not found")

@app.route('/gwern')
def serve_gwern_rss():
    try:
        return send_file('gwern_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        logger.log_scrape_error("Gwern Changelog RSS feed not found")
        abort(404, description="Gwern Changelog RSS feed not found")

@app.route('/anthropic')
def serve_anthropic_rss():
    try:
        return send_file('anthropic_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        logger.log_scrape_error("Anthropic Research RSS feed not found")
        abort(404, description="Anthropic Research RSS feed not found")

@app.route('/openai')
def serve_openai_rss():
    try:
        return send_file('openai_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        logger.log_scrape_error("OpenAI Research RSS feed not found")
        abort(404, description="OpenAI Research RSS feed not found")

@app.route('/groq')
def serve_groq_rss():
    try:
        return send_file('groq_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        logger.log_scrape_error("Groq Blog RSS feed not found")
        abort(404, description="Groq Blog RSS feed not found")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port) 