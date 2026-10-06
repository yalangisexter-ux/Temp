import requests
from bs4 import BeautifulSoup
import re, json

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
headers = {"User-Agent": ua, "Accept": "text/html,*/*", "Accept-Language": "en-US,en;q=0.9"}

# Disable auto-redirect to see the Location header
s = requests.Session()
s.max_redirects = 0

r = s.get("https://www.bing.com/search", params={"q": "hemarusha19@gmail.com", "count": 10}, headers=headers, timeout=15)
print("status:", r.status_code)
soup = BeautifulSoup(r.text, "html.parser")

results = soup.select("li.b_algo h2 a")
print("hits:", len(results))
for a in results[:3]:
    href = a.get("href", "")
    title = a.get_text(strip=True)
    # Try to get the real URL by following the redirect
    try:
        rr = s.get(href, headers=headers, timeout=5, allow_redirects=True)
        final_url = rr.url
    except:
        final_url = href
    print("  ", title[:60], "|", final_url[:100])