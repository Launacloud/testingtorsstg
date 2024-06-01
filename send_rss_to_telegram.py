import os
import requests
import feedparser
import json
from bs4 import BeautifulSoup

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RSS_FEED_URL = os.getenv('RSS_FEED_URL')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GITHUB_WORKSPACE = os.getenv('GITHUB_WORKSPACE', '/tmp')

# Set cache directory and file path
CACHE_DIR = os.path.join(GITHUB_WORKSPACE, 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'feed_cache.json')

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

print(f"Using cache directory: {CACHE_DIR}")
print(f"Using cache file: {CACHE_FILE}")

# Ensure cache directory and file exist
def ensure_cache_file():
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"Cache directory ensured: {CACHE_DIR}")
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'w') as f:
            json.dump({}, f)
        print(f"Cache file created: {CACHE_FILE}")
    else:
        print(f"Cache file exists: {CACHE_FILE}")

# Function to load cache
def load_cache():
    ensure_cache_file()
    with open(CACHE_FILE, 'r') as f:
        print(f"Loading cache from file: {CACHE_FILE}")
        return json.load(f)

# Function to save cache
def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)
    print(f"Cache saved to file: {CACHE_FILE}")
    print_cache()

# Function to print cache
def print_cache():
    with open(CACHE_FILE, 'r') as f:
        cache_content = json.load(f)
        print(f"Cache content: {json.dumps(cache_content, indent=2)}")

# Function to send a message to a Telegram chat
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'false'  # Enable link previews
    }
    response = requests.post(url, data=payload)
    print(f"Response status code: {response.status_code}")
    print(f"Response text: {response.text}")
    if response.status_code != 200:
        raise Exception(f"Error sending message: {response.text}")

# Function to send RSS feed items to Telegram with conditional requests
def send_rss_to_telegram():
    cache = load_cache()
    etag = cache.get('etag')
    modified = cache.get('modified')
    last_entry_id = cache.get('last_entry_id', None)  # Initialize last_entry_id if not present

    print(f"Loading feed with etag: {etag} and modified: {modified}")
    feed = fetch_rss_feed(etag=etag, modified=modified)

    if feed.status == 304:
        print("No new entries.")
        return

    # Update cache with new etag and modified values
    cache['etag'] = feed.get('etag')
    cache['modified'] = feed.get('modified')

    new_entries = []
    for entry in feed.entries:
        entry_id = entry.get('id', entry.get('link'))  # Use link if id is not present
        print(f"Processing entry with id: {entry_id}")
        if last_entry_id and entry_id <= last_entry_id:
            print(f"Skipping entry with id: {entry_id} as it is not newer than last_entry_id: {last_entry_id}")
            continue
        new_entries.append(entry)

    if not new_entries:
        print("No new entries to process.")
        return

    for entry in reversed(new_entries):  # Process entries in reverse order to handle newer entries first
        entry_id = entry.get('id', entry.get('link'))  # Use link if id is not present
        title = entry.title
        link = entry.get('link', entry.get('url'))  # Get link or url
        description = entry.get('content_html', entry.get('description'))  # Get content_html or description

        # Use BeautifulSoup to extract text from HTML description and filter out unsupported tags
        soup = BeautifulSoup(description, 'html.parser')
        supported_tags = ['b', 'i', 'a']  # Supported tags: bold, italic, anchor
        # Filter out unsupported tags
        for tag in soup.find_all():
            if tag.name not in supported_tags:
                tag.decompose()
        description_text = soup.get_text()
        message = f"<b>{title}</b>\n{link}\n\n{description_text}"
        send_telegram_message(message)
        print(f"Message sent: {title}")

        if last_entry_id and entry_id == last_entry_id:
            print("Stopping script as last_entry_id matches current entry
