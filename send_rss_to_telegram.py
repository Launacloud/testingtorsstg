import os
import requests
import feedparser
import json
import time
from bs4 import BeautifulSoup

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RSS_FEED_URL = os.getenv('RSS_FEED_URL')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CACHE_DIR = os.getenv('GITHUB_WORKSPACE', '.') + '/cache'
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, 'feed_cache.json')

# Path to store etag and modified information
CACHE_DIR = os.getenv('GITHUB_WORKSPACE', '.') + '/cache'
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, 'feed_cache.json')

# Function to load cache
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Function to save cache
def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

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

# Function to send RSS feed items to Telegram
def send_rss_to_telegram():
    cache = load_cache()
    etag = cache.get('etag')
    modified = cache.get('modified')
    
    feed = feedparser.parse(RSS_FEED_URL, etag=etag, modified=modified)
    
    if feed.status == 304:
        print("No new entries.")
        return
    
    # Update cache with new etag and modified values
    cache['etag'] = feed.get('etag')
    cache['modified'] = feed.get('modified')
    save_cache(cache)

    for entry in feed.entries:
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

# Main function
def main():
    send_rss_to_telegram()

if __name__ == "__main__":
    main()
