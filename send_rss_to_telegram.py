# Function to send RSS feed items to Telegram
def send_rss_to_telegram():
    cache = load_cache()
    etag = cache.get('etag')
    modified = cache.get('modified')
    last_entry_id = cache.get('last_entry_id', None)  # Initialize last_entry_id if not present
    
    print("Previous etag:", etag)
    print("Previous modified:", modified)

    print(f"Loading feed with etag: {etag} and modified: {modified}")
    feed = fetch_rss_feed(etag=etag, modified=modified)

    if feed.status == 304.:
        print("No new entries.")
        return

    # Update cache with new etag and modified values if they exist in the feed
    if 'etag' in feed:
        cache['etag'] = feed.etag
    if 'modified' in feed:
        cache['modified'] = feed.modified

    new_entries = []
    stop_processing = False
    for entry in reversed(feed.entries):  # Process entries in reverse order
        entry_id = entry.get('id', entry.get('link')).strip()  # Use link if id is not present and strip whitespace
        print(f"Processing entry with id: {entry_id}")
        if last_entry_id and entry_id == last_entry_id:
            print(f"Found the last processed entry with id: {entry_id}. Stopping further collection.")
            stop_processing = True
        if not stop_processing:
            new_entries.append(entry)

    if not new_entries:
        print("No new entries to process.")
        return

    # Process entries in reverse order to handle newer entries first
    for entry in reversed(new_entries):
        entry_id = entry.get('id', entry.get('link')).strip()  # Use link if id is not present and strip whitespace
        title = entry.title
        link = entry.get('link', entry.get('url'))  # Get link or url
        description = entry.get('content_html', entry.get('description'))  # Get content_html or description

        # Use BeautifulSoup to extract text from HTML description and filter out unsupported tags
        if description:
            soup = BeautifulSoup(description, 'html.parser')
            supported_tags = ['b', 'i', 'a']  # Supported tags: bold, italic, anchor
            for tag in soup.find_all():
                if tag.name not in supported_tags:
                    tag.decompose()
            description_text = soup.prettify()
        else:
            description_text = "No description available."

        print(f"Title: {title}")
        print(f"Link: {link}")
        print(f"Description: {description_text}")

        message = f"<b>{title}</b>\n<a href='{link}'>{link}</a>\n\n{description_text}"
        send_telegram_message(message)
        print(f"Message sent: {title}")

        # Update last_entry_id in cache after sending the message
        cache['last_entry_id'] = entry_id

    # Save cache if there are new entries
    save_cache(cache)
