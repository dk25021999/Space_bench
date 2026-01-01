import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time

# === Base URL ===
BASE_URL = "https://pwg.gsfc.nasa.gov/stargaze"

# === Fetch the Spaceflight index ===
response = requests.get(BASE_URL)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

spaceflight_items = []
in_spaceflight = False

for tag in soup.find_all(["h3", "li"]):

    # Detect Spaceflight section start
    if tag.name == "h3" and "Spaceflight" in tag.get_text():
        in_spaceflight = True
        continue

    # Stop when next section begins
    if tag.name == "h3" and "Sun and Solar System" in tag.get_text():
        break

    # Collect list items under Spaceflight
    if in_spaceflight and tag.name == "li":
        a = tag.find("a")
        if a:
            text = a.get_text(strip=True)
            href = urljoin(BASE_URL, a.get("href"))
            spaceflight_items.append({
                "title": text,
                "url": href
            })

# Print results
for item in spaceflight_items:
    print(item["title"])
    print(item["url"])
    print("-" * 40)


links = [(item["title"], item["url"]) for item in spaceflight_items]



# === Scrape each linked Q&A page ===
scraped_data = {}

for title, url in links:
    print(f"Scraping: {title} — {url}")
    try:
        r = requests.get(url)
        r.raise_for_status()
        sub_soup = BeautifulSoup(r.text, "html.parser")

        # Extract all text content from this Q&A page
        page_text = sub_soup.get_text(separator="\n", strip=True)
        scraped_data[title] = page_text

    except Exception as e:
        print(f"Error fetching {url}: {e}")
    
    # Delay to be polite
    time.sleep(1.0)

# === Save the results (one section per file) ===
import os

os.makedirs("spaceflight_answers", exist_ok=True)

for title, content in scraped_data.items():
    # sanitize file name
    fname = "".join(c if c.isalnum() or c in "._-" else "_" for c in title)
    with open(f"spaceflight_answers/{fname}.txt", "w", encoding="utf-8") as f:
        f.write(content)

print("Done. All Spaceflight text saved to spaceflight_answers/")

