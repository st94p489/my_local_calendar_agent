import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from icalendar import Calendar, Event
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
        href = a["href"]
        if "patch.com" in href and "theater" in href.lower():
            links.append(href)

    return list(set(links))


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

    for e in events:
        event = Event()
        event.add("summary", e["title"])
        event.add("location", f"{e['venue']}, {e['city']}")
        event.add("dtstart", datetime.fromisoformat(e["start_time"]))
        event.add("dtend", datetime.fromisoformat(e["end_time"]))
        event.add("description", e["description"])

        uid = hashlib.md5((e["title"] + e["start_time"]).encode()).hexdigest()
        event.add("uid", uid)

        cal.add_component(event)

    with open(CAL_FILE, "wb") as f:
        f.write(cal.to_ical())


def main():
    urls = fetch_patch_events()

    events = []
    for u in urls[:5]:  # keep small initially
        try:
            events.append(extract_event(u))
        except:
            continue

    create_ics(events)


if __name__ == "__main__":
    main()
