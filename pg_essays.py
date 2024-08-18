import urllib.request
from urllib.parse import urljoin
import time
import os.path
import html2text
import regex as re
from htmldate import find_date
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import json

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

ART_NO = 0  # Initialize to 0 so the first entry is 001

def fetch_and_update_articles():
    global toc
    message = "Fetching and updating articles..."
    print(message)
    logging.info(message)
    toc = list(reversed(parse_main_page("https://paulgraham.com/", "articles.html")))
    message = "Articles updated."
    print(message)
    logging.info(message)
    generate_rss_feed()

def parse_main_page(base_url: str, articles_url: str):
    assert base_url.endswith(
        "/"), f"Base URL must end with a slash: {base_url}"
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
                    {"link": urljoin(
                        base_url, a_tag["href"]), "title": a_tag.text}
                )

    return chapter_links

toc = list(reversed(parse_main_page("https://paulgraham.com/", "articles.html")))

def update_links_in_md(joined):
    matches = re.findall(b"\[\d+\]", joined)

    if not matches:
        return joined

    for match in set(matches):

        def update_links(match):
            counter[0] += 1
            note_name = f"{title}_note{note_number}"
            if counter[0] == 1:
                return bytes(f"[{note_number}](#{note_name})", "utf-8")
            elif counter[0] == 2:
                return bytes(f"<a name={note_name}>[{note_number}]</a>", "utf-8")

        counter = [0]

        note_number = int(match.decode().strip("[]"))
        match_regex = match.replace(b"[", b"\[").replace(b"]", b"\]")

        joined = re.sub(match_regex, update_links, joined)

    return joined

def generate_rss_feed():
    rss_feed = []
    message = "Starting to generate RSS feed..."
    print(message)
    logging.info(message)
    for entry in toc[-5:]:
        global ART_NO
        ART_NO += 1
        URL = entry["link"]
        message = f"Processing article {ART_NO}: {URL}"
        print(message)
        logging.info(message)
        if "http://www.paulgraham.com/https://" in URL:
            URL = URL.replace("http://www.paulgraham.com/https://", "https://")
            message = f"Corrected URL: {URL}"
            print(message)
            logging.info(message)
        TITLE = entry["title"]
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
            title = "_".join(TITLE.split(" ")).lower()
            title = re.sub(r"[\W\s]+", "", title)
            DATE = find_date(URL)
            message = f"Parsed title: {title}, Date: {DATE}"
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
            update_with_links = update_links_in_md(encoded)
            message = f"Updated links in markdown for {TITLE}"
            print(message)
            logging.info(message)

            rss_feed.append({
                "article_no": str(ART_NO).zfill(3),
                "title": TITLE,
                "date": DATE,
                "url": URL,
                "content": update_with_links.decode()
            })

            message = f"✅ {str(ART_NO).zfill(3)} {TITLE}"
            print(message)
            logging.info(message)

        except Exception as e:
            message = f"❌ {str(ART_NO).zfill(3)} {entry['title']}, ({e})"
            print(message)
            logging.error(message)
        time.sleep(0.05)  # half sec/article is ~2min, be nice with servers!

    message = "Finished generating RSS feed."
    print(message)
    logging.info(message)
    
    # Save RSS feed to a file
    with open('rss_feed.json', 'w') as f:
        json.dump(rss_feed, f)
    message = "RSS feed saved to rss_feed.json."
    print(message)
    logging.info(message)
    
if __name__ == '__main__':
    # Initialize the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_update_articles, 'interval', days=1)
    scheduler.start()

    # Fetch articles initially
    fetch_and_update_articles()

    # Serve the static file using a simple HTTP server
    import http.server
    import socketserver

    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler

    message = f"Serving rss_feed.json on http://0.0.0.0:{PORT}"
    print(message)
    logging.info(message)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()