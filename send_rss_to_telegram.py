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
            print("Stopping script as last_entry_id matches current entry ID.")
            break

        if not last_entry_id or entry_id > last_entry_id:
            last_entry_id = entry_id

    cache['last_entry_id'] = last_entry_id
    save_cache(cache)  # Save cache outside of the loop

# Main function
def main():
    send_rss_to_telegram()

if __name__ == "__main__":
    main()
