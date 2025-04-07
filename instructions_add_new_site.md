# Guide: Adding a New Website Scraper (Updated)

## 1. Create the Scraper Script

Create a new Python file named after your website (e.g., `anthropic_rss.py`). Use this template structure:

```python
import urllib.request
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
from htmldate import find_date
import html2text
import time
from urllib.parse import urljoin
from logger import RSSLogger

# Configure logging
logger = RSSLogger("anthropic_rss")

# Configure HTML to text converter
h = html2text.HTML2Text()
h.ignore_images = True
h.ignore_tables = True
h.escape_all = True
h.reference_links = True

# Browser-like headers to avoid 403 errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def fetch_and_update_articles():
    """Main function to fetch articles and generate RSS feed"""
    message = "Fetching and updating articles from Anthropic..."
    print(message)
    logger.log_info(message)
    
    articles = parse_main_page("https://www.anthropic.com/research")
    generate_rss_feed(articles)

def parse_main_page(base_url: str):
    """
    Parse the main blog page to get list of articles
    Returns: List of dictionaries with article info
    """
    articles = []
    try:
        response = requests.get(base_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Using the provided HTML structure for Anthropic's research page
        post_cards = soup.select("a.PostCard_post-card__z_Sqq")
        
        for post in post_cards[:10]:  # Limit to most recent 10 posts
            # Extract title
            title_elem = post.select_one("h3.PostCard_post-heading__Ob1pu")
            title = title_elem.text.strip() if title_elem else "No Title"
            
            # Extract link
            link = urljoin(base_url, post["href"])
            
            # Extract date
            date_elem = post.select_one("div.PostList_post-date__djrOA")
            date_str = date_elem.text.strip() if date_elem else ""
            
            # Get full article content
            content = fetch_article_content(link)
            
            articles.append({
                "title": title,
                "link": link,
                "date": date_str,
                "content": content
            })
            
            # Be nice to the server
            time.sleep(0.5)
            
    except Exception as e:
        error_msg = f"Error parsing Anthropic blog: {str(e)}"
        print(error_msg)
        logger.log_scrape_error(error_msg)
        
    return articles

def fetch_article_content(article_url):
    """Fetch and parse the full content of an article"""
    try:
        response = requests.get(article_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Using the HTML structure for individual Anthropic blog posts
        article_content = soup.select_one("div.PostDetail_post-detail__6Ldh_ article")
        
        if article_content:
            # Convert HTML to readable text
            content_text = h.handle(str(article_content))
            return content_text
        else:
            return "Content not available"
            
    except Exception as e:
        error_msg = f"Error fetching article {article_url}: {str(e)}"
        print(error_msg)
        logger.log_scrape_error(error_msg)
        return "Error retrieving content"

def generate_rss_feed(articles):
    """Generate RSS feed from scraped articles"""
    rss_feed = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss_feed, "channel")
    
    # Set feed metadata
    ET.SubElement(channel, "title").text = "Anthropic Research Blog"
    ET.SubElement(channel, "link").text = "https://www.anthropic.com/research"
    ET.SubElement(channel, "description").text = "Research articles from Anthropic"

    # Add articles to feed
    for article in articles:
        try:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = article["title"]
            ET.SubElement(item, "link").text = article["link"]
            ET.SubElement(item, "description").text = article["content"]
            ET.SubElement(item, "pubDate").text = article["date"]
        except Exception as e:
            error_msg = f"Error adding article to feed: {str(e)}"
            print(error_msg)
            logger.log_scrape_error(error_msg)

    # Save RSS feed
    try:
        tree = ET.ElementTree(rss_feed)
        tree.write("anthropic_feed.xml", encoding="utf-8", xml_declaration=True)
        logger.log_info("RSS feed saved to anthropic_feed.xml")
    except Exception as e:
        error_msg = f"Error saving RSS feed: {str(e)}"
        print(error_msg)
        logger.log_scrape_error(error_msg)

if __name__ == "__main__":
    fetch_and_update_articles()
```

## 2. Create a Start Script

Create a shell script named `start_anthropic.sh`:

```bash
#!/bin/bash
python3 anthropic_rss.py
python3 server.py anthropic_feed.xml /anthropic
```

Make it executable:
```bash
chmod +x start_anthropic.sh
```

## 3. Update Docker Configuration

The existing docker-compose.yml already has a single service for all feeds. You don't need to add a separate service, but if you want to test just your new feed, add this to docker-compose.yml:

```yaml
  anthropic-rss:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - ./logs:/app/logs
    command: ./start_anthropic.sh
```

## 4. Update the Server

Add your new endpoint to server.py:

```python
@app.route('/anthropic')
def serve_anthropic_rss():
    try:
        return send_file('anthropic_feed.xml', mimetype='application/rss+xml')
    except FileNotFoundError:
        logger.log_scrape_error("Anthropic Research RSS feed not found")
        abort(404, description="Anthropic Research RSS feed not found")
```

Also update the home route to list your new feed:
```python
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
    # ... rest of the function
```

And update the status route:
```python
@app.route('/status')
def status():
    # ... existing code
    feeds = {
        'angular': 'angular_ventures_feed.xml',
        'pg': 'pg_essays.xml',
        'gwern': 'gwern_feed.xml',
        'anthropic': 'anthropic_feed.xml'
    }
    # ... rest of the function
```

## 5. Update start_all.sh

Add your scraper to the `start_all.sh` script:

```bash
#!/bin/bash

# Function to run the scrapers
run_scrapers() {
    echo "Running RSS feed generators at $(date)"
    python angular_ventures_rss.py
    python pg_essays.py
    python gwern_rss.py
    python anthropic_rss.py
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
```

## 6. Update requirements.txt

Make sure all required packages are in requirements.txt:

```
flask
beautifulsoup4
requests
html2text
htmldate
regex
gunicorn
```

## 7. Testing Your Scraper

1. Test the scraper script alone:
```bash
python3 anthropic_rss.py
```

2. Check if the RSS feed file was created and contains valid content:
```bash
cat anthropic_feed.xml
```

3. Test the endpoint:
```bash
curl http://localhost:3000/anthropic
```

## 8. Troubleshooting

1. Check the logs for errors:
```bash
cat logs/anthropic_rss_*.log
```

2. Adjust your CSS selectors if the website structure changes

3. Test each component (fetching, parsing, feed generation) separately

## Important Notes

For the Anthropic blog example, note these specific elements:
- Post cards: `a.PostCard_post-card__z_Sqq`
- Title: `h3.PostCard_post-heading__Ob1pu`
- Date: `div.PostList_post-date__djrOA`
- Article content: `div.PostDetail_post-detail__6Ldh_ article`

Remember to:
1. Always respect the website's robots.txt
2. Implement rate limiting (already included with time.sleep)
3. Use error handling and logging (enhanced in the updated template)
4. Add proper date parsing for the pubDate field
5. **IMPORTANT**: Always use browser-like headers (as defined in the HEADERS constant) when making requests to avoid being blocked by anti-scraping measures. Many websites will return 403 Forbidden errors if you don't use proper headers that mimic a real browser.
6. Consider implementing fallback content if scraping fails repeatedly

The original guide was good, but these updates provide more specific guidance based on the actual project structure and the Anthropic example.
