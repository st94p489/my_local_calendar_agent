import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from dateutil.parser import isoparse
from urllib.parse import urljoin
import hashlib
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CAL_FILE = "events.ics"

def fetch_patch_events():
    url = "https://patch.com/pennsylvania/newtown-pa"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue

        full_url = urljoin(url, href)
        if "/calendar/event/" in full_url:
            links.append(full_url)

    unique_links = sorted(set(links))
    print(f"Found {len(unique_links)} calendar event URLs")
    return unique_links


def extract_event(url):
    page = requests.get(url).text

    prompt = f"""
    Extract theater event info from this HTML and return JSON with:
    title, venue, city, start_time, end_time, description

    HTML:
    {page[:8000]}
    """

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    import json
    return json.loads(response.choices[0].message.content)


def create_ics(events):
    cal = Calendar()
    cal.add("prodid", "-//My Local Calendar Agent//example.com//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")

    if not events:
        print("No events to write to ICS file.")

    for e in events:
        event = Event()
        event.add("summary", e["title"])
        event.add("location", f"{e['venue']}, {e['city']}")
        event.add("dtstart", isoparse(e["start_time"]))
        event.add("dtend", isoparse(e["end_time"]))
        event.add("description", e["description"])
        event.add("dtstamp", datetime.utcnow())

        uid = hashlib.md5((e["title"] + e["start_time"]).encode()).hexdigest()
        event.add("uid", uid)

        cal.add_component(event)

    with open(CAL_FILE, "wb") as f:
        f.write(cal.to_ical())


def sweeney_todd_events():
    venue = "Council Rock High School North"
    city = "Newtown, PA"
    description = (
        "Sock 'n' Buskin brings Stephen Sondheim's dark musical Sweeney Todd to the stage "
        "for a three-night run at Council Rock North."
    )

    return [
        {
            "title": "Sweeney Todd - Council Rock North",
            "venue": venue,
            "city": city,
            "start_time": "2026-04-30T19:00:00",
            "end_time": "2026-04-30T21:30:00",
            "description": description,
        },
        {
            "title": "Sweeney Todd - Council Rock North",
            "venue": venue,
            "city": city,
            "start_time": "2026-05-01T19:00:00",
            "end_time": "2026-05-01T21:30:00",
            "description": description,
        },
        {
            "title": "Sweeney Todd - Council Rock North",
            "venue": venue,
            "city": city,
            "start_time": "2026-05-02T19:00:00",
            "end_time": "2026-05-02T21:30:00",
            "description": description,
        },
    ]


def main():
    urls = fetch_patch_events()

    events = []
    for u in urls[:5]:  # keep small initially
        try:
            events.append(extract_event(u))
        except:
            continue

    events.extend(sweeney_todd_events())
    create_ics(events)


if __name__ == "__main__":
    main()
