import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import re
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

def fetch_and_parse_blog():
    url = "https://newsletter.angularventures.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    response = requests.get(url, headers=headers)
    print("Response status code:", response.status_code)
    print("\nFirst 1000 characters of HTML:")
    print(response.text[:1000])
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    # Find all grid containers that might contain posts
    grid_container = soup.find('div', class_='grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3')
    
    if grid_container:
        for article in grid_container.find_all('div', class_='transparent', recursive=False)[:5]:
            try:
                # Find the main link and title
                link_element = article.find('a', href=lambda x: x and '/p/' in x)
                title_element = article.find('h2')
                date_element = article.find('time')
                description_element = article.find('p', class_='line-clamp-2')
                
                if not all([link_element, title_element, date_element]):
                    continue
                
                link = f"https://newsletter.angularventures.com{link_element['href']}"
                title = title_element.text.strip()
                date_str = date_element.get('datetime')
                description = description_element.text.strip() if description_element else ""
                
                # Parse the ISO format date
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                
                print(f"Found post: {title} ({date_str})")
                
                posts.append({
                    'title': title,
                    'link': link,
                    'description': description,
                    'pub_date': date
                })
            except Exception as e:
                print(f"Error processing article: {str(e)}")
                continue
    
    return posts

def generate_rss_feed(posts):
    feed = FeedGenerator()
    feed.title("Angular Ventures Blog")
    feed.link(href="https://newsletter.angularventures.com/")
    feed.description("Latest posts from Angular Ventures")
    feed.language("en")
    
    for post in posts:
        entry = feed.add_entry()
        entry.title(post['title'])
        entry.link(href=post['link'])
        entry.description(post['description'])
        entry.pubDate(post['pub_date'])
    
    feed.rss_file('angular_ventures_feed.xml')

def update_feed():
    print(f"[{datetime.now()}] Updating Angular Ventures RSS feed...")
    try:
        posts = fetch_and_parse_blog()
        generate_rss_feed(posts)
        print(f"[{datetime.now()}] Successfully updated Angular Ventures RSS feed with {len(posts)} posts")
    except Exception as e:
        print(f"[{datetime.now()}] Error updating Angular Ventures RSS feed: {str(e)}")

def main():
    print(f"[{datetime.now()}] Starting Angular Ventures RSS feed generator...")
    update_feed()
    print(f"[{datetime.now()}] Finished generating Angular Ventures RSS feed")

if __name__ == "__main__":
    main()
