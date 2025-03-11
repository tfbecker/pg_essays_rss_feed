from flask import Flask, send_file, abort
import os

app = Flask(__name__)

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
    
    return f'''
    <html>
        <body>
            <h1>RSS Feeds</h1>
            <ul>
                {''.join(feeds)}
            </ul>
        </body>
    </html>
    '''

@app.route('/angular')
def serve_angular_rss():
    try:
        return send_file('angular_ventures_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        abort(404, description="Angular Ventures RSS feed not found")

@app.route('/pg')
def serve_pg_rss():
    try:
        return send_file('pg_essays.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        abort(404, description="Paul Graham Essays RSS feed not found")

@app.route('/gwern')
def serve_gwern_rss():
    try:
        return send_file('gwern_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        abort(404, description="Gwern Changelog RSS feed not found")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port) 