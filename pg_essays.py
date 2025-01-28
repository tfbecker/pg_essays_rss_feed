import urllib.request
from urllib.parse import urljoin
import time
import os.path
import html2text
import regex as re
from htmldate import find_date
import requests
from bs4 import BeautifulSoup
import logging
import xml.etree.ElementTree as ET

"""
Publish a collection of Paul Graham essays as an RSS feed.
"""

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

h = html2text.HTML2Text()
h.ignore_images = True
h.ignore_tables = True
h.escape_all = True
h.reference_links = True
h.mark_code = True

def fetch_and_update_articles():
    global toc, ART_NO
    ART_NO = 0  # Reset ART_NO to 0 at the start of each fetch
    message = "Fetching and updating articles..."
    print(message)
    logging.info(message)
    toc = list(reversed(parse_main_page("https://paulgraham.com/", "articles.html")))
    message = "Articles updated."
    print(message)
    logging.info(message)
    generate_rss_feed()

def parse_main_page(base_url: str, articles_url: str):
    assert base_url.endswith("/"), f"Base URL must end with a slash: {base_url}"
    response = requests.get(base_url + articles_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all relevant 'td' elements
    td_cells = soup.select("table > tr > td > table > tr > td")
    chapter_links = []

    for td in td_cells:
        # use the heuristic that page links are an <a> inside a <font> with a small (bullet) image alongside
        img = td.find("img")
        if img and int(img.get("width", 0)) <= 15 and int(img.get("height", 0)) <= 15:
            a_tag = td.find("font").find("a") if td.find("font") else None
            if a_tag:
                chapter_links.append(
                    {"link": urljoin(base_url, a_tag["href"]), "title": a_tag.text}
                )

    return chapter_links

def generate_rss_feed():
    rss_feed = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss_feed, "channel")
    ET.SubElement(channel, "title").text = "Paul Graham Essays"
    ET.SubElement(channel, "link").text = "https://paulgraham.com/"
    ET.SubElement(channel, "description").text = "A collection of essays by Paul Graham."

    message = "Starting to generate RSS feed..."
    print(message)
    logging.info(message)
    for entry in toc[-5:]:
        global ART_NO
        ART_NO += 1
        URL = entry["link"]
        TITLE = entry["title"]
        message = f"Processing article {ART_NO}: {URL}"
        print(message)
        logging.info(message)
        if "http://www.paulgraham.com/https://" in URL:
            URL = URL.replace("http://www.paulgraham.com/https://", "https://")
            message = f"Corrected URL: {URL}"
            print(message)
            logging.info(message)
        message = f"Title: {TITLE}"
        print(message)
        logging.info(message)

        try:
            try:
                with urllib.request.urlopen(URL) as website:
                    content = website.read().decode("utf-8")
                    message = f"Successfully fetched content for {TITLE} in utf-8 encoding."
                    print(message)
                    logging.info(message)
            except UnicodeDecodeError:
                with urllib.request.urlopen(URL) as website:
                    content = website.read().decode("latin-1")
                    message = f"Successfully fetched content for {TITLE} in latin-1 encoding."
                    print(message)
                    logging.info(message)

            parsed = h.handle(content)
            DATE = find_date(URL)
            message = f"Parsed title: {TITLE}, Date: {DATE}"
            print(message)
            logging.info(message)

            parsed = parsed.replace("[](index.html)  \n  \n", "")
            message = f"Cleaned parsed content for {TITLE}"
            print(message)
            logging.info(message)

            parsed = [
                (
                    p.replace("\n", " ")
                    if re.match(r"^[\p{Z}\s]*(?:[^\p{Z}\s][\p{Z}\s]*){5,100}$", p)
                    else "\n" + p + "\n"
                )
                for p in parsed.split("\n")
            ]
            message = f"Formatted paragraphs for {TITLE}"
            print(message)
            logging.info(message)

            encoded = " ".join(parsed).encode()
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = TITLE
            ET.SubElement(item, "link").text = URL
            ET.SubElement(item, "description").text = encoded.decode()
            ET.SubElement(item, "pubDate").text = DATE

            message = f" {str(ART_NO).zfill(3)} {TITLE}"
            print(message)
            logging.info(message)

        except Exception as e:
            message = f" {str(ART_NO).zfill(3)} {entry['title']}, ({e})"
            print(message)
            logging.error(message)
        time.sleep(0.05)  # half sec/article is ~2min, be nice with servers!

    message = "Finished generating RSS feed."
    print(message)
    logging.info(message)
    
    # Save RSS feed to a file
    tree = ET.ElementTree(rss_feed)
    tree.write("pg_essays.xml", encoding="utf-8", xml_declaration=True)
    message = "RSS feed saved to pg_essays.xml."
    print(message)
    logging.info(message)

if __name__ == "__main__":
    fetch_and_update_articles()