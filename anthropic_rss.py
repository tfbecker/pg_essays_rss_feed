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
import datetime

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

# Fallback articles in case scraping fails
FALLBACK_ARTICLES = [
    {
        "title": "Reasoning models don't always say what they think",
        "link": "https://www.anthropic.com/research/reasoning-models-dont-say-think",
        "date": "3 Apr 2025",
        "content": "Since late last year, 'reasoning models' have been everywhere. These are AI models—such as Claude 3.7 Sonnet—that show their working: as well as their eventual answer, you can read the (often fascinating and convoluted) way that they got there."
    },
    {
        "title": "Anthropic Economic Index: Insights from Claude 3.7 Sonnet",
        "link": "https://www.anthropic.com/news/anthropic-economic-index-insights-from-claude-sonnet-3-7",
        "date": "27 Mar 2025",
        "content": "Economic research and insights from Claude 3.7 Sonnet"
    },
    {
        "title": "Tracing the thoughts of a large language model",
        "link": "https://www.anthropic.com/research/tracing-thoughts-language-model",
        "date": "27 Mar 2025",
        "content": "Research on tracing thought processes in language models"
    },
    {
        "title": "Auditing language models for hidden objectives",
        "link": "https://www.anthropic.com/research/auditing-hidden-objectives",
        "date": "13 Mar 2025",
        "content": "Research on auditing language models for hidden objectives"
    },
    {
        "title": "Forecasting rare language model behaviors",
        "link": "https://www.anthropic.com/research/forecasting-rare-behaviors",
        "date": "25 Feb 2025",
        "content": "Research on forecasting rare language model behaviors"
    }
]

def fetch_and_update_articles():
    """Main function to fetch articles and generate RSS feed"""
    message = "Fetching and updating articles from Anthropic..."
    print(message)
    logger.log_scrape_start()
    
    articles = parse_main_page("https://www.anthropic.com/research")
    
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
                
        # Using the provided HTML structure for Anthropic's research page
        print("Looking for post cards with selector: a.PostCard_post-card__z_Sqq")
        post_cards = soup.select("a.PostCard_post-card__z_Sqq")
        print(f"Found {len(post_cards)} post cards")
        
        if not post_cards:
            # Try alternative selectors
            print("Trying alternative selector: a[class*='PostCard_post-card']")
            post_cards = soup.select("a[class*='PostCard_post-card']")
            print(f"Found {len(post_cards)} post cards with alternative selector")
            
        for i, post in enumerate(post_cards[:10]):  # Limit to most recent 10 posts
            print(f"Processing post {i+1}")
            
            # Extract title
            title_elem = post.select_one("h3.PostCard_post-heading__Ob1pu")
            if not title_elem:
                print("Trying alternative title selector: h3[class*='post-heading']")
                title_elem = post.select_one("h3[class*='post-heading']")
                
            title = title_elem.text.strip() if title_elem else "No Title"
            print(f"Title: {title}")
            
            # Extract link
            link = urljoin(base_url, post["href"])
            print(f"Link: {link}")
            
            # Extract date
            date_elem = post.select_one("div.PostList_post-date__djrOA")
            if not date_elem:
                print("Trying alternative date selector: div[class*='post-date']")
                date_elem = post.select_one("div[class*='post-date']")
                
            date_str = date_elem.text.strip() if date_elem else ""
            print(f"Date: {date_str}")
            
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
        print(f"Fetching article content from {article_url}")
        response = requests.get(article_url, headers=HEADERS)
        print(f"Article response status code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Using the HTML structure for individual Anthropic blog posts
        print("Looking for article content with selector: div.PostDetail_post-detail__6Ldh_ article")
        article_content = soup.select_one("div.PostDetail_post-detail__6Ldh_ article")
        
        if not article_content:
            print("Trying alternative selector: div[class*='PostDetail_post-detail'] article")
            article_content = soup.select_one("div[class*='PostDetail_post-detail'] article")
            
        if not article_content:
            print("Trying broader selector: article")
            article_content = soup.select_one("article")
        
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
    ET.SubElement(channel, "title").text = "Anthropic Research Blog"
    ET.SubElement(channel, "link").text = "https://www.anthropic.com/research"
    ET.SubElement(channel, "description").text = "Research articles from Anthropic"

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
                # For fallback articles, date is already properly formatted
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
        print("Saving RSS feed to anthropic_feed.xml")
        tree = ET.ElementTree(rss_feed)
        tree.write("anthropic_feed.xml", encoding="utf-8", xml_declaration=True)
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