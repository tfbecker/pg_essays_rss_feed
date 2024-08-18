import urllib.request
from urllib.parse import urljoin
import time
import os.path
import html2text
import regex as re
from htmldate import find_date
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

"""
Publish a collection of Paul Graham essays as an RSS feed via Flask.
"""

h = html2text.HTML2Text()
h.ignore_images = True
h.ignore_tables = True
h.escape_all = True
h.reference_links = True
h.mark_code = True

ART_NO = 0  # Initialize to 0 so the first entry is 001

app = Flask(__name__)

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


@app.route('/rss')
def generate_rss_feed():
    rss_feed = []
    print("Starting to generate RSS feed...")
    for entry in toc[:10]:
        global ART_NO
        ART_NO += 1
        URL = entry["link"]
        print(f"Processing article {ART_NO}: {URL}")
        if "http://www.paulgraham.com/https://" in URL:
            URL = URL.replace("http://www.paulgraham.com/https://", "https://")
            print(f"Corrected URL: {URL}")
        TITLE = entry["title"]
        print(f"Title: {TITLE}")

        try:
            try:
                with urllib.request.urlopen(URL) as website:
                    content = website.read().decode("utf-8")
                    print(f"Successfully fetched content for {TITLE} in utf-8 encoding.")
            except UnicodeDecodeError:
                with urllib.request.urlopen(URL) as website:
                    content = website.read().decode("latin-1")
                    print(f"Successfully fetched content for {TITLE} in latin-1 encoding.")

            parsed = h.handle(content)
            title = "_".join(TITLE.split(" ")).lower()
            title = re.sub(r"[\W\s]+", "", title)
            DATE = find_date(URL)
            print(f"Parsed title: {title}, Date: {DATE}")

            parsed = parsed.replace("[](index.html)  \n  \n", "")
            print(f"Cleaned parsed content for {TITLE}")

            parsed = [
                (
                    p.replace("\n", " ")
                    if re.match(r"^[\p{Z}\s]*(?:[^\p{Z}\s][\p{Z}\s]*){5,100}$", p)
                    else "\n" + p + "\n"
                )
                for p in parsed.split("\n")
            ]
            print(f"Formatted paragraphs for {TITLE}")

            encoded = " ".join(parsed).encode()
            update_with_links = update_links_in_md(encoded)
            print(f"Updated links in markdown for {TITLE}")

            rss_feed.append({
                "article_no": str(ART_NO).zfill(3),
                "title": TITLE,
                "date": DATE,
                "url": URL,
                "content": update_with_links.decode()
            })

            print(f"✅ {str(ART_NO).zfill(3)} {TITLE}")

        except Exception as e:
            print(f"❌ {str(ART_NO).zfill(3)} {entry['title']}, ({e})")
        time.sleep(0.05)  # half sec/article is ~2min, be nice with servers!

    print("Finished generating RSS feed.")
    return jsonify(rss_feed)


if __name__ == '__main__':
    from waitress import serve
    print("Starting server on http://0.0.0.0:9777")
    serve(app, host='0.0.0.0', port=9777)