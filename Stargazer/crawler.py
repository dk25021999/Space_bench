import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time

# === Base URL ===
BASE_URL = "https://pwg.gsfc.nasa.gov/stargaze/IstarFSubj.htm?utm_source=chatgpt.com"

# === Fetch the Spaceflight index ===
response = requests.get(BASE_URL)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# Find the Spaceflight section
spaceflight_section = None
for header in soup.find_all(["h3", "strong"]):
    if "Spaceflight" in header.get_text():
        spaceflight_section = header.find_next_sibling("ul")
        break

if not spaceflight_section:
    raise Exception("Couldn't find the Spaceflight section!")

# Parse all link URLs in the Spaceflight part
links = []
for li in spaceflight_section.find_all("li"):
    a = li.find("a")
    if a and a.get("href"):
        href = a["href"]
        full_url = urljoin(BASE_URL, href)
        links.append((a.get_text(strip=True), full_url))

print(f"Found {len(links)} Spaceflight links.")

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

