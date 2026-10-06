import requests, json

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
headers = {"User-Agent": ua, "Accept": "application/json,*/*"}
r = requests.get(
    "https://api.duckduckgo.com/",
    params={"q": '"Karam Hemarusha"', "format": "json", "no_html": "1", "skip_disambig": "1", "t": "test"},
    headers=headers,
    timeout=15,
)
print("status:", r.status_code)
print("len:", len(r.text))
print("first 300:", repr(r.text[:300]))
try:
    d = r.json()
    print("Results:", len(d.get("Results", [])))
    print("RelatedTopics:", len(d.get("RelatedTopics", [])))
    if d.get("Results"):
        for item in d["Results"]:
            print("  -", item.get("FirstURL", ""), "|", item.get("Text", "")[:80])
except Exception as e:
    print("JSON error:", e)