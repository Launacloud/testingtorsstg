import os
import json
from datetime import datetime
from urllib.parse import urljoin
import requests
from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
import feedparser

from feed import feeds

def generate_feed(feed_config):
    r = requests.get(feed_config["url"])
    soup = BeautifulSoup(r.text, 'html.parser')

    titles = soup.select(feed_config["item_title_css"])
    urls = soup.select(feed_config["item_url_css"])
    descriptions = soup.select(feed_config["item_description_css"]) if feed_config["item_description_css"] else []
    authors = soup.select(feed_config["item_author_css"]) if feed_config["item_author_css"] else []
    dates = soup.select(feed_config["item_date_css"]) if feed_config["item_date_css"] else []
    extras = soup.select(feed_config["item_extra_css"]) if "item_extra_css" in feed_config else []
    extras2 = soup.select(feed_config["item_extra_css2"]) if "item_extra_css2" in feed_config else []

    fg = FeedGenerator()
    fg.id(feed_config["url"])
    fg.title(feed_config["title"])
    fg.subtitle(feed_config["subtitle"])
    fg.link(href=feed_config["url"], rel='alternate')
    fg.language(feed_config["language"])
    fg.author({'name': feed_config["author_name"], 'email': feed_config["author_email"]})

    atom_file_path = os.path.join(feed_config["output_path"], 'atom.xml')
    existing_ids = set()  # To track existing entry IDs
    output_data = []

    # Load existing entries if the XML file exists
    if os.path.exists(atom_file_path):
        existing_feed = feedparser.parse(atom_file_path)
        for entry in existing_feed.entries:
            fe = fg.add_entry()
            fe.id(entry.id)
            fe.title(entry.title)
            fe.link(href=entry.link)
            fe.description(entry.description)
            if hasattr(entry, 'author'):
                fe.author(name=entry.author)
            if hasattr(entry, 'published'):
                fe.published(entry.published)

            entry_data = {
                "Title": entry.title,
                "ID": entry.id,
                "Description": entry.description
            }
            if hasattr(entry, 'author'):
                entry_data["Author"] = entry.author
            output_data.append(entry_data)
            existing_ids.add(entry.id)  # Add ID to the set

    min_len = min(len(titles), len(urls) or len(titles), len(descriptions) or len(titles), len(authors) or len(titles), len(dates) or len(titles), len(extras) or len(titles), len(extras2) or len(titles))

    for i in range(min_len):
        item_url = urljoin(feed_config["url"], urls[i].get('href')) if urls else feed_config["url"]

        if item_url in existing_ids:
            continue  # Skip if the entry already exists

        fe = fg.add_entry()
        fe.title(titles[i].text)
        fe.id(item_url)
        fe.link(href=item_url, rel='alternate')

        description_text = descriptions[i].text if i < len(descriptions) else "No description found"
        description_text = BeautifulSoup(description_text, 'html.parser').text.strip()

        if extras:
            extra_text = extras[i].text if i < len(extras) else "No extra information found"
            description_text += f"\n\nExtra 1: {extra_text}"
        
        if extras2:
            extra2_text = extras2[i].text if i < len(extras2) else "No second extra information found"
            description_text += f"\n\nExtra 2: {extra2_text}"

        fe.description(description_text)

        if authors:
            author_text = authors[i].text if i < len(authors) else "No author found"
            fe.author(name=author_text)

        entry_data = {
            "Title": titles[i].text,
            "ID": item_url,
            "Description": description_text
        }
        if authors:
            entry_data["Author"] = author_text
        output_data.append(entry_data)

    output_path = feed_config["output_path"]
    os.makedirs(output_path, exist_ok=True)

    fg.atom_file(atom_file_path)

    json_file_path = os.path.join(output_path, 'feed.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"XML file '{atom_file_path}' updated successfully.")
    print(f"JSON file '{json_file_path}' created successfully.")

for feed_config in feeds:
    generate_feed(feed_config)
