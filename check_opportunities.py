import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

LISTING_URL = "https://thehomeshare.ie/opportunities/"
BASE_URL = "https://thehomeshare.ie"
STATE_FILE = Path(__file__).parent / "data" / "seen_opportunities.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_opportunities():
    response = requests.get(LISTING_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    opportunities = {}
    for card in soup.select("article.opp-card"):
        link = card.select_one("a.btn-read-more")
        title_el = card.select_one("h2.opp-title")
        if not link or not title_el:
            continue
        href = link["href"]
        url = urljoin(BASE_URL, href)
        opportunities[href] = {
            "title": title_el.get_text(strip=True),
            "url": url,
        }
    return opportunities


def load_seen():
    if not STATE_FILE.exists():
        return None
    with STATE_FILE.open() as f:
        return set(json.load(f))


def save_seen(slugs):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w") as f:
        json.dump(sorted(slugs), f, indent=2)


def send_email(new_opportunities):
    smtp_host = os.environ.get("SMTP_HOST", "smtp-mail.outlook.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USERNAME"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    email_from = os.environ.get("EMAIL_FROM", smtp_user)
    email_to = os.environ["EMAIL_TO"]

    count = len(new_opportunities)
    subject = f"{count} new HomeShare opportunit{'y' if count == 1 else 'ies'} listed"
    lines = [f"{opp['title']}\n{opp['url']}\n" for opp in new_opportunities]
    body = "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(email_from, [email_to], msg.as_string())


def main():
    opportunities = fetch_opportunities()
    if not opportunities:
        print("No opportunity listings found on the page — skipping.", file=sys.stderr)
        return

    seen = load_seen()

    if seen is None:
        # First ever run: seed the state file without emailing, so we don't
        # treat every currently-live listing as "new".
        save_seen(opportunities.keys())
        print(f"Bootstrapped state file with {len(opportunities)} existing listings.")
        return

    new_slugs = [slug for slug in opportunities if slug not in seen]

    if new_slugs:
        new_opportunities = [opportunities[slug] for slug in new_slugs]
        for opp in new_opportunities:
            print(f"New opportunity: {opp['title']} -> {opp['url']}")
        send_email(new_opportunities)
    else:
        print("No new opportunities.")

    save_seen(seen.union(opportunities.keys()))


if __name__ == "__main__":
    main()
