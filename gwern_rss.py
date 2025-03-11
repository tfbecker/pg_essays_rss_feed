from dataclasses import dataclass
import datetime
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import re
from feedgen.feed import FeedGenerator
import logging

"""
Generate an RSS feed for Gwern Branwen's changelog.
This script fetches the changelog from gwern.net/changelog, parses the updates,
and generates an RSS feed.
"""

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Update:
    """A month in the changelog"""
    month: str
    changes: str
    link: str
    date: datetime.datetime


def fetch_and_update_gwern_changelog():
    message = "Fetching and updating Gwern changelog..."
    print(message)
    logging.info(message)
    
    try:
        changelog_page = requests.get("https://gwern.net/changelog")
    except Exception as e:
        message = f"There appears to be a problem accessing https://gwern.net/changelog: {e}"
        print(message)
        logging.error(message)
        return
    
    soup = BeautifulSoup(changelog_page.content.decode(changelog_page.encoding or "utf-8"), "html.parser")
    main_document = soup.find("div", id = "markdownBody")
    if not main_document or isinstance(main_document, NavigableString):
        message = "Could not find the main body of the document (i.e. element with id 'markdownBody')"
        print(message)
        logging.error(message)
        return
    
    # Only match sections that have an id starting with 4 numbers
    potential_yearly_sections = main_document.find_all("section", id=re.compile(r"^\d\d\d\d.*$"))
    if any(not isinstance(section, Tag) for section in potential_yearly_sections):
        message = "Some of the sections of the main body appear empty"
        print(message)
        logging.error(message)
        return
    
    if len(potential_yearly_sections) < 5:
        message = f"Changelog appears to be missing values. Only {len(potential_yearly_sections)} sections found."
        print(message)
        logging.warning(message)
    
    updates: list[Update] = []
    for yearly_section in potential_yearly_sections:
        if len(updates) > 20:
            break 
        
        assert(isinstance(yearly_section, Tag))
        months = yearly_section.find_all("section", id=re.compile(r"^.*\d\d\d\d$"))
        year = yearly_section.get("id")
        assert(isinstance(year, str))
        try:
            year = int(year)
        except ValueError:
            year = datetime.datetime.today().year
            
        for month in months:
            assert(isinstance(month, Tag))
            
            month_title = month.find("h2")
            assert(isinstance(month_title, Tag))
            month_link = month_title.find("a")
            assert(isinstance(month_link, Tag))
            month_text = month_link.text

            month_list = month.find("ul")
            if not isinstance(month_list, Tag):
                continue

            month_id = month.get("id")
            assert(isinstance(month_id, str))
            month_datetime = datetime.datetime.strptime(month_id[:-5], "%B").month
    
            updates.append(Update(
                                  month_text,
                                  str(month_list),
                                  f"https://gwern.net/changelog#{month_id}",
                                  datetime.datetime(year=year, month=(month_datetime % 12) + 1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.datetime.today().astimezone().tzinfo)
                              ))
    
    message = f"Found {len(updates)} updates from the Gwern changelog."
    print(message)
    logging.info(message)
            
    generate_rss_feed(updates)

def generate_rss_feed(updates):
    message = "Generating RSS feed..."
    print(message)
    logging.info(message)
    
    feed = FeedGenerator()
    feed.author(name = "Gwern Branwen", email = "gwern@gwern.net")
    feed.contributor(name = "Gwern Branwen", email = "gwern@gwern.net")    
    feed.description("A feed trying its best to mirror the content at https://gwern.net/changelog")
    feed.language("en")
    feed.link(href="https://gwern.net/changelog", rel="alternate")
    feed.title("Gwern Changelog")
    
    for update in updates:
        entry = feed.add_entry(order="append")
        entry.title(update.month)
        entry.author(name = "Gwern Branwen", email = "gwern@gwern.net")
        entry.content(update.changes, type="CDATA")
        entry.link(href=update.link, rel="related")
        entry.published(update.date)
    
    feed.rss_file("gwern_feed.xml", pretty=True)
    message = "RSS feed saved to gwern_feed.xml."
    print(message)
    logging.info(message)

if __name__ == "__main__":
    fetch_and_update_gwern_changelog() 