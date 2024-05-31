name: RSS to Telegram

on:
  schedule:
    - cron: '0 * * * *'  # Runs every hour
  workflow_dispatch:  # Allows manual triggering from the GitHub Actions tab

jobs:
  rss_to_telegram:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run the RSS to Telegram script
      env:
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        RSS_FEED_URL: ${{ secrets.RSS_FEED_URL }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      run: |
        python rss_to_telegram.py
