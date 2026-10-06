import requests
from bs4 import BeautifulSoup
import re

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
headers = {"User-Agent": ua, "Accept": "text/html,*/*", "Accept-Language": "en-US,en;q=0.9"}

r = requests.get(
    "https://www.google.com/search",
    params={"q": "hemarusha19@gmail.com", "num": 10},
    headers=headers,
    timeout=15,
)
print("status:", r.status_code)
print("len:", len(r.text))

soup = BeautifulSoup(r.text, "html.parser")

# Modern Google: results in <a> with href starting with /url?q=
# or <div class="g"> > <a>
for a in soup.find_all("a", href=True):
    href = a["href"]
    if href.startswith("/url?q="):
        real_url = href.split("/url?q=")[1].split("&")[0]
        title = a.get_text(strip=True)
        if title and "google" not in real_url:
            print("  ", title[:60], "|", real_url[:80])