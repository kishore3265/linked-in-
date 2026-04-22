"""
slacklinked.py — Slack bot that triggers LinkedIn Sales Navigator scraping.

Setup:
    1. Set environment variables before running:
           set SLACK_BOT_TOKEN=xoxb-...
           set SLACK_APP_TOKEN=xapp-...
    2. Run:  python slacklinked.py

Usage (in Slack):
    Send a Sales Navigator search URL to the bot, optionally with a page count.
    Examples:
        https://www.linkedin.com/sales/search/company?query=...
        scrape 10 pages https://www.linkedin.com/sales/search/company?query=...
        https://www.linkedin.com/sales/search/company?query=... 3

    The bot responds only to messages containing a valid Sales Navigator URL.
    If no page count is given, it defaults to 5 pages.
"""

import os
import re
import json
import glob
import threading

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ---------------------------------------------------------------------------
# Tokens — never hardcoded; must be set as environment variables
# ---------------------------------------------------------------------------
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise EnvironmentError(
        "Missing required environment variables.\n"
        "Please set both SLACK_BOT_TOKEN and SLACK_APP_TOKEN before running."
    )

# ---------------------------------------------------------------------------
# Bolt app
# ---------------------------------------------------------------------------
app = App(token=SLACK_BOT_TOKEN)

# ---------------------------------------------------------------------------
# Pattern: only accept linkedin.com/sales/search/... URLs
# ---------------------------------------------------------------------------
_SALES_NAV_PATTERN = re.compile(
    r"https://www\.linkedin\.com/sales/search/[^\s<>\"']+"
)

# Pattern to extract a standalone integer (e.g. "10 pages", "page 3", "3")
_PAGE_COUNT_PATTERN = re.compile(r"\b(\d+)\b")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_sales_nav_url(text: str):
    """Return the first Sales Navigator search URL found in *text*, or None."""
    match = _SALES_NAV_PATTERN.search(text)
    return match.group(0) if match else None


def extract_max_pages(text: str, default: int = 5) -> int:
    """
    Return the first standalone integer found in *text* that looks like a
    page count (1-100).  Falls back to *default* if none is found.
    """
    for match in _PAGE_COUNT_PATTERN.finditer(text):
        value = int(match.group(1))
        if 1 <= value <= 100:
            return value
    return default


def _find_newest_scrape_file() -> tuple:
    """
    Return (filepath, lead_count) for the most recently modified
    scraped_leads_*.json file in the working directory.
    Returns (None, 0) if no such file exists.
    """
    pattern = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_leads_*.json")
    files = glob.glob(pattern)
    if not files:
        return None, 0
    newest = max(files, key=os.path.getmtime)
    try:
        with open(newest, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = len(data) if isinstance(data, list) else 0
    except Exception:
        count = 0
    return os.path.basename(newest), count


# ---------------------------------------------------------------------------
# Scrape job — runs in a background daemon thread
# ---------------------------------------------------------------------------

def _scrape_job(url: str, max_pages: int, channel: str, client):
    """
    Runs the full Sales Navigator scrape pipeline in a background thread.
    Posts progress and completion (or error) messages back to *channel*.
    """
    # Import here so the bot starts up even if linkd.py has import-time issues
    # (e.g. chromedriver not on PATH) — they'll surface only when a job runs.
    try:
        from linkd import SalesNavigatorScraper
    except ImportError as exc:
        client.chat_postMessage(
            channel=channel,
            text=f":x: Failed to import scraper: `{exc}`\nMake sure `linkd.py` is in the same directory.",
        )
        return

    try:
        scraper = SalesNavigatorScraper(cookie_file="linkedin_cookies.json")
        scraper.run_continuation(continuation_url=url, max_pages=max_pages)

        filename, lead_count = _find_newest_scrape_file()
        if filename:
            client.chat_postMessage(
                channel=channel,
                text=(
                    f":white_check_mark: *Scrape complete!*\n"
                    f">Scraped *{lead_count}* companies across up to {max_pages} page(s).\n"
                    f">Results saved to `{filename}`"
                ),
            )
        else:
            client.chat_postMessage(
                channel=channel,
                text=":white_check_mark: Scrape finished, but no output file was found. Check the console for details.",
            )

    except Exception as exc:
        client.chat_postMessage(
            channel=channel,
            text=f":x: *Scrape failed with an error:*\n```{exc}```",
        )


# ---------------------------------------------------------------------------
# Slack event handler
# ---------------------------------------------------------------------------

@app.event("message")
def handle_message(event, say, client):
    """
    Listen for messages in channels/DMs where the bot is present.
    Only react when the message contains a Sales Navigator search URL.
    """
    # Ignore edited messages, bot messages, channel-join notices, etc.
    if event.get("subtype"):
        return

    text = event.get("text") or ""
    url = extract_sales_nav_url(text)

    # No valid Sales Navigator URL — stay silent
    if not url:
        return

    max_pages = extract_max_pages(text)
    channel = event["channel"]

    # Acknowledge immediately so the user knows the bot received the request
    say(
        text=(
            f":mag: Got it! Starting scrape for:\n"
            f">`{url}`\n"
            f">Pages to scrape: *{max_pages}*\n\n"
            f"I'll post here when it's done."
        )
    )

    # Kick off the scrape in a background thread so the bot stays responsive
    thread = threading.Thread(
        target=_scrape_job,
        args=(url, max_pages, channel, client),
        daemon=True,
    )
    thread.start()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting Slack bot via Socket Mode...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
