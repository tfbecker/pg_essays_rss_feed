import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import html2text
import time
from urllib.parse import urljoin
from logger import RSSLogger
import datetime

# Configure logging
logger = RSSLogger("groq_rss")

# Configure HTML to text converter
h = html2text.HTML2Text()
h.ignore_images = True
h.ignore_tables = True
h.escape_all = True
h.reference_links = True

# Browser-like headers to avoid 403 errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Fallback articles in case scraping fails
FALLBACK_ARTICLES = [
    {
        "title": "Inside the LPU: Deconstructing Groq's Speed",
        "link": "https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed",
        "date": "Dec 16, 2025",
        "content": "Legacy hardware forces a choice: faster inference with quality degradation, or accurate inference with unacceptable latency. The LPU–purpose-built hardware for inference–preserves quality while eliminating architectural bottlenecks."
    },
    {
        "title": "Advancing the American AI Stack",
        "link": "https://groq.com/blog/advancingamericanai",
        "date": "Dec 01, 2025",
        "content": "Groq's perspective on advancing American AI infrastructure."
    },
]


def fetch_and_update_articles():
    """Main function to fetch articles and generate RSS feed"""
    message = "Fetching and updating articles from Groq Blog..."
    print(message)
    logger.log_scrape_start()

    articles = parse_main_page("https://groq.com/blog/")

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

        # Find all article cards
        print("Looking for article cards with selector: article.card")
        cards = soup.select("article.card")
        print(f"Found {len(cards)} cards")

        if not cards:
            # Try alternative selector
            print("Trying alternative selector: li.Multicard_multicard__item__ACW9b")
            items = soup.select("li[class*='Multicard_multicard__item']")
            print(f"Found {len(items)} items")
            cards = [item.select_one("article") for item in items if item.select_one("article")]
            print(f"Extracted {len(cards)} article cards from items")

        for i, card in enumerate(cards[:15]):  # Limit to most recent 15 posts
            print(f"Processing card {i+1}")

            # Extract title and link
            title_elem = card.select_one("h2.card__title a")
            if not title_elem:
                title_elem = card.select_one("h2 a") or card.select_one("a")

            title = title_elem.text.strip() if title_elem else "No Title"
            href = title_elem.get("href", "") if title_elem else ""
            link = urljoin(base_url, href) if href else ""
            print(f"Title: {title}")
            print(f"Link: {link}")

            # Extract date
            date_elem = card.select_one("time.card__eyebrow") or card.select_one("time")
            date_str = date_elem.text.strip() if date_elem else ""
            print(f"Date: {date_str}")

            if not link or link == base_url:
                print("Skipping card - no valid link")
                continue

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
        error_msg = f"Error parsing Groq blog: {str(e)}"
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

        # Try multiple selectors for article content
        selectors = [
            "article",
            "div[class*='post-content']",
            "div[class*='article-content']",
            "div[class*='blog-content']",
            "main",
        ]

        article_content = None
        for selector in selectors:
            article_content = soup.select_one(selector)
            if article_content:
                print(f"Found content with selector: {selector}")
                break

        if article_content:
            # Remove navigation, footer, etc
            for unwanted in article_content.select("nav, footer, header, script, style"):
                unwanted.decompose()

            # Convert HTML to readable text
            content_text = h.handle(str(article_content))
            # Truncate if too long
            if len(content_text) > 5000:
                content_text = content_text[:5000] + "..."
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
    ET.SubElement(channel, "title").text = "Groq Blog"
    ET.SubElement(channel, "link").text = "https://groq.com/blog/"
    ET.SubElement(channel, "description").text = "Latest posts from the Groq Blog - LPU inference, AI infrastructure, and more"

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
        print("Saving RSS feed to groq_feed.xml")
        tree = ET.ElementTree(rss_feed)
        tree.write("groq_feed.xml", encoding="utf-8", xml_declaration=True)
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
