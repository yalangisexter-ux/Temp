import requests
from bs4 import BeautifulSoup
import json

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
headers = {"User-Agent": ua, "Accept": "text/html,*/*", "Accept-Language": "en-US,en;q=0.9"}

r = requests.get("https://www.bing.com/search", params={"q": "hemarusha19@gmail.com", "count": 10}, headers=headers, timeout=15)
print("status:", r.status_code)
print("len:", len(r.text))

soup = BeautifulSoup(r.text, "html.parser")

# Bing v3: results are in <li class="b_algo">
results = soup.select("li.b_algo")
print("\nli.b_algo count:", len(results))
for li in results[:5]:
    h2 = li.find("h2")
    if h2:
        a = h2.find("a")
        if a:
            href = a.get("href", "")
            title = a.get_text(strip=True)
            print("  ", title[:60], "|", href[:80])

# Also try: <div id="b_results"> > <li class="b_algo">
# Fallback: any h2 with a link
if not results:
    print("\nTrying fallback selectors...")
    for a in soup.select("h2 a"):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if href and title and "bing.com" not in href:
            print("  ", title[:60], "|", href[:80])