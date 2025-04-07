import urllib.request
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
import html2text
import time
from urllib.parse import urljoin
from logger import RSSLogger
import datetime

# Configure logging
logger = RSSLogger("openai_rss")

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

# Fallback articles in case scraping fails
FALLBACK_ARTICLES = [
    {
        "title": "PaperBench: Evaluating AI's Ability to Replicate AI Research",
        "link": "https://openai.com/index/paperbench/",
        "date": "Apr 2, 2025",
        "content": "Evaluating AI's Ability to Replicate AI Research."
    },
    {
        "title": "Introducing 4o Image Generation",
        "link": "https://openai.com/index/introducing-4o-image-generation/",
        "date": "Mar 25, 2025",
        "content": "New image generation capabilities from OpenAI."
    }
]

def fetch_and_update_articles():
    """Main function to fetch articles and generate RSS feed"""
    message = "Fetching and updating articles from OpenAI Research..."
    print(message)
    logger.log_scrape_start()
    
    articles = parse_main_page("https://openai.com/news/research/")
    
    # Use fallback articles if scraping fails
    if not articles:
        print("Scraping failed, using fallback articles")
        articles = FALLBACK_ARTICLES
        
    generate_rss_feed(articles)

def parse_main_page(base_url: str):
    """
    Parse the main blog page to get list of articles
    Returns: List of dictionaries with article info
    """
    articles = []
    try:
        print(f"Fetching content from {base_url}")
        response = requests.get(base_url, headers=HEADERS)
        print(f"Response status code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Print the HTML structure to debug
        print("HTML structure preview:")
        print(soup.prettify()[:1000])  # Print first 1000 chars for debugging
        
        # Based on the provided HTML structure for OpenAI's research page
        print("Looking for post cards in the grid")
        post_cards = soup.select("div.grid > div.group.relative")
        print(f"Found {len(post_cards)} post cards")
        
        for i, post in enumerate(post_cards[:10]):  # Limit to most recent 10 posts
            print(f"Processing post {i+1}")
            
            # Find the link element which contains the article data
            link_elem = post.select_one("a[aria-label]")
            if not link_elem:
                print("No link element found, skipping post")
                continue
                
            # Extract article info from the aria-label attribute
            aria_label = link_elem.get("aria-label", "")
            print(f"Aria label: {aria_label}")
            
            # Parse the aria-label which has format: "Title - Category - Date"
            parts = aria_label.split(" - ") if aria_label else []
            if len(parts) >= 3:
                title = parts[0].strip()
                category = parts[1].strip()
                date_str = parts[2].strip()
            else:
                # Fallback to finding elements directly
                title_elem = link_elem.select_one("div.text-h5")
                title = title_elem.text.strip() if title_elem else "No Title"
                
                date_elem = link_elem.select_one("time")
                date_str = date_elem.text.strip() if date_elem else ""
            
            print(f"Title: {title}")
            print(f"Date: {date_str}")
            
            # Extract link
            link = urljoin(base_url, link_elem.get("href", ""))
            print(f"Link: {link}")
            
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
        error_msg = f"Error parsing OpenAI blog: {str(e)}"
        print(error_msg)
        logger.log_scrape_error(error_msg)
        
    return articles

def fetch_article_content(article_url):
    """Fetch and parse the full content of an article"""
    try:
        print(f"Fetching article content from {article_url}")
        response = requests.get(article_url, headers=HEADERS)
        print(f"Article response status code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Based on the provided HTML structure for OpenAI blog posts
        print("Looking for article content")
        
        # Try to find the main content
        article_content = soup.select_one("div.prose")
        
        if not article_content:
            # Try alternative selectors
            article_content = soup.select_one("div[class*='col-span-12'] div.prose")
            
        if not article_content:
            article_content = soup.select_one("div.max-w-none.prose")
        
        if article_content:
            print("Article content found!")
            # Convert HTML to readable text
            content_text = h.handle(str(article_content))
            return content_text
        else:
            print("No article content found")
            return "Content not available"
            
    except Exception as e:
        error_msg = f"Error fetching article {article_url}: {str(e)}"
        print(error_msg)
        logger.log_scrape_error(error_msg)
        return "Error retrieving content"

def generate_rss_feed(articles):
    """Generate RSS feed from scraped articles"""
    print(f"Generating RSS feed with {len(articles)} articles")
    rss_feed = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss_feed, "channel")
    
    # Set feed metadata
    ET.SubElement(channel, "title").text = "OpenAI Research Blog"
    ET.SubElement(channel, "link").text = "https://openai.com/news/research/"
    ET.SubElement(channel, "description").text = "Research articles from OpenAI"

    # Add articles to feed
    for i, article in enumerate(articles):
        try:
            print(f"Adding article {i+1} to feed: {article['title']}")
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = article["title"]
            ET.SubElement(item, "link").text = article["link"]
            ET.SubElement(item, "description").text = article["content"]
            
            # Format date for RSS
            try:
                ET.SubElement(item, "pubDate").text = article["date"]
            except Exception as date_error:
                print(f"Error formatting date: {date_error}")
                ET.SubElement(item, "pubDate").text = datetime.datetime.now().strftime("%d %b %Y")
        except Exception as e:
            error_msg = f"Error adding article to feed: {str(e)}"
            print(error_msg)
            logger.log_scrape_error(error_msg)

    # Save RSS feed
    try:
        print("Saving RSS feed to openai_feed.xml")
        tree = ET.ElementTree(rss_feed)
        tree.write("openai_feed.xml", encoding="utf-8", xml_declaration=True)
        if articles:
            logger.log_scrape_success(articles[0]["title"], articles[0]["date"])
            print(f"Successfully saved feed with {len(articles)} articles")
        else:
            error_msg = "No articles found to add to feed"
            logger.log_scrape_error(error_msg)
            print(error_msg)
    except Exception as e:
        error_msg = f"Error saving RSS feed: {str(e)}"
        print(error_msg)
        logger.log_scrape_error(error_msg)

if __name__ == "__main__":
    fetch_and_update_articles() 