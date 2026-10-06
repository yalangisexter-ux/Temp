import json
import sys
import io
import time
import random
import re
import os
from urllib.parse import quote, unquote, urlparse, parse_qs
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependencies. Install them with: "
        "pip install requests beautifulsoup4 pillow"
    ) from exc

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG = {
    "hibp_api_key": os.environ.get("HIBP_API_KEY", ""),
    "dehashed_email": os.environ.get("DEHASHED_EMAIL", ""),
    "dehashed_api_key": os.environ.get("DEHASHED_API_KEY", ""),
    "delay_min": 1.0,
    "delay_max": 2.5,
    "timeout": 20,
    "output_dir": "osint_results",
    "save_photos": True,
    "darkweb_enabled": True,
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

PROFILE_DATA = {
    "profile": {
        "name": "Karam Hemarusha",
        "dob": "19-11-1999",
        "age": 26,
        "gender": "Female",
        "community": "ST (Koya)",
        "height_cm": 164,
        "weight_kg": 78,
        "distinctive_marks": ["Mole on left cheek", "Mole on right eyebrow"],
    },
    "family": {
        "father": "Karam Harinath Babu",
        "mother": "Karam Parvathi",
        "sister": "Karam Shanvitha Rani",
    },
    "contact": {
        "primary_phone": "+919010183934",
        "secondary_phone": "+919490686935",
        "email_primary": "hemarusha19@gmail.com",
        "email_secondary": "hemarushaharinath.k@gmail.com",
        "instagram_handle": "@miss.h_a_pp_y",
    },
    "addresses": {
        "aadhaar_address": "1-81, Jaggavaram Village, Chuchirevulagudem Post, Kunavaram Mandal, East Godavari District, AP - 507121",
        "insurance_address_note": "PIN 533350, Alluri Sitarama Raju District",
    },
    "ids": {
        "aadhaar_partial": "5038 **** **** 8975",
        "pan": "KJCPK0810B",
        "caste_cert_no": "CGC011504710040",
    },
    "insurance": {
        "provider": "HDFC ERGO",
        "policy_no": "28000000607624",
        "plan": "my:Optima Secure",
        "nominee": "Karam Shanvitha Rani",
    },
}


class AdvancedOSINTAgent:
    def __init__(self):
        self.data = PROFILE_DATA
        self.name = self.data["profile"]["name"]
        self.first_name = self.name.split()[0]
        self.last_name = (
            " ".join(self.name.split()[1:]) if len(self.name.split()) > 1 else ""
        )
        self.phones = [
            p.replace("+91", "")
            for p in [
                self.data["contact"]["primary_phone"],
                self.data["contact"]["secondary_phone"],
            ]
        ]
        self.emails = [
            self.data["contact"]["email_primary"],
            self.data["contact"]["email_secondary"],
        ]
        self.pan = self.data["ids"]["pan"]
        self.ig_handle = self.data["contact"]["instagram_handle"].replace("@", "")
        self.usernames = self._generate_usernames()
        self.photos_downloaded = []
        self.results = {
            "target": self.name,
            "profile": self.data["profile"],
            "breach_data": [],
            "email_findings": {},
            "phone_findings": {},
            "username_availability": {},
            "social_media_presence": {},
            "social_media_content": {},
            "search_engine_results": {},
            "darkweb_findings": [],
            "domain_search": [],
            "discord_servers": [],
            "pan_findings": {},
            "address_search": [],
            "family_search": {},
            "content_platform_status": {},
            "financial_checks": {},
            "photos_downloaded": [],
            "summary": "",
        }
        self.session = requests.Session()
        os.makedirs(CONFIG["output_dir"], exist_ok=True)
        os.makedirs(os.path.join(CONFIG["output_dir"], "photos"), exist_ok=True)

    def _get_headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }

    def _generate_usernames(self):
        names = self.name.lower().replace(" ", "").replace("'", "")
        variations = set()
        variations.add(self.ig_handle)
        variations.add(names)
        variations.add(names.replace(" ", "_"))
        variations.add(names.replace(" ", "."))
        variations.add(names.split()[0] if " " in names else names)
        variations.add(self.first_name.lower())
        variations.add(self.last_name.lower() if self.last_name else "")
        variations.add(f"{self.first_name.lower()}{self.last_name.lower()}")
        variations.add(f"{self.first_name.lower()}_{self.last_name.lower()}")
        variations.add(f"{self.first_name.lower()}.{self.last_name.lower()}")
        for email in self.emails:
            variations.add(email.split("@")[0])
        variations.discard("")
        return list(variations)

    def log(self, msg):
        print(f"[OSINT-AGENT] {msg}")

    def _fetch(self, url, params=None, timeout=None, max_retries=3):
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(CONFIG["delay_min"], CONFIG["delay_max"]))
                self.session.headers.update(self._get_headers())
                response = self.session.get(
                    url, params=params, timeout=timeout or CONFIG["timeout"]
                )

                if response.status_code == 429:
                    wait = 5 + (attempt * 3)
                    self.log(f"[WARN] Rate limited (429), waiting {wait}s...")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    wait = 5 + (attempt * 3)
                    self.log(f"[WARN] Rate limited (429), waiting {wait}s...")
                    time.sleep(wait)
                    continue
                elif e.response.status_code in (403, 404, 503):
                    self.log(f"  HTTP {e.response.status_code} for {url[:80]}")
                    return e.response  # return the response anyway, caller checks status
                elif attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                else:
                    self.log(f"  HTTP error {e.response.status_code} for {url[:80]}")
                    return e.response
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                self.log(f"  Request error: {e}")
                return None
        return None

    def _download_photo(self, url, filename):
        if not CONFIG["save_photos"]:
            return None
        try:
            path = os.path.join(CONFIG["output_dir"], "photos", filename)
            response = self._fetch(url, timeout=10)
            if response and response.status_code == 200 and len(response.content) > 1000:
                with open(path, "wb") as f:
                    f.write(response.content)
                self.photos_downloaded.append(
                    {"url": url, "path": path, "size": len(response.content)}
                )
                self.log(f"[OK] Downloaded photo: {filename}")
                return path
            else:
                self.log(f"  Photo skip: {filename}")
        except Exception as e:
            self.log(f"[ERR] Photo download error: {e}")
        return None

    # ==========================================
    # DUCKDUCKGO SEARCH VIA INSTANT ANSWER API
    # ==========================================
    def _duckduckgo_search(self, query, max_results=10):
        """Search using DDG Instant Answer API (JSON, no JS challenge)."""
        results = []
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
                "t": "osint_agent",
            }
            time.sleep(1.0)
            self.session.headers.update(self._get_headers())
            response = self.session.get(url, params=params, timeout=15)

            if response and response.status_code == 200:
                data = response.json()

                for item in data.get("Results", []):
                    url = item.get("FirstURL", "") or item.get("Url", "")
                    title = item.get("Text", "") or item.get("Title", "")
                    if url and title:
                        results.append({"url": url, "title": title})

                for item in data.get("RelatedTopics", []):
                    if "Topics" in item:
                        for sub in item["Topics"]:
                            url = sub.get("FirstURL", "") or sub.get("Url", "")
                            title = sub.get("Text", "") or sub.get("Title", "")
                            if url and title:
                                results.append({"url": url, "title": title})
                    else:
                        url = item.get("FirstURL", "") or item.get("Url", "")
                        title = item.get("Text", "") or item.get("Title", "")
                        if url and title:
                            results.append({"url": url, "title": title})

                abstract_url = data.get("AbstractURL", "")
                abstract_text = data.get("AbstractText", "")
                if abstract_url and abstract_text:
                    results.append(
                        {"url": abstract_url, "title": abstract_text[:100]}
                    )

                if results:
                    return results[:max_results]
                else:
                    return []
            else:
                return []
        except Exception as e:
            self.log(f"[ERR] DDG API error: {e}")
        return results

    # ==========================================
    # STEP 1: SEARCH ENGINE
    # ==========================================
    def step_1_search_engine(self):
        self.log("=" * 60)
        self.log("STEP 1: DuckDuckGo Search Engine")
        self.log("=" * 60)

        search_params = {
            "Full Name": f'"{self.name}"',
            "Email Only": f'"{self.emails[0]}"',
            "Phone Only": f'"{self.phones[0]}"',
            "Username Only": f'"{self.ig_handle}"',
            "PAN Card": f'"{self.pan}"',
            "Full Name + Email": f'"{self.name}" "{self.emails[0]}"',
            "Full Name + Phone": f'"{self.name}" "{self.phones[0]}"',
            "Insurance Policy": f'"{self.data["insurance"]["policy_no"]}"',
            "DOB + Name": f'"19-11-1999" "{self.name}"',
            "Address Search": f'"{self.data["addresses"]["aadhaar_address"][:50]}"',
            "Father Name": f'"{self.data["family"]["father"]}"',
            "Mother Name": f'"{self.data["family"]["mother"]}"',
            "Sister Name": f'"{self.data["family"]["sister"]}"',
            "District + Name": f'"{self.name}" "East Godavari"',
            "Village + Name": f'"{self.name}" "Jaggavaram"',
            "PDF Files": f'filetype:pdf "{self.name}"',
            "DOC Files": f'filetype:doc "{self.name}"',
        }

        for param_name, query in search_params.items():
            try:
                links = self._duckduckgo_search(query)
                if links:
                    self.results["search_engine_results"][param_name] = links
                    self.log(f"[OK] {param_name}: {len(links)} results")
                    for link in links[:3]:
                        self.log(
                            f"  - {link['title'][:60]} | {link['url'][:60]}"
                        )
                else:
                    self.log(f"  {param_name}: No results")
            except Exception as e:
                self.log(f"[ERR] Search error '{param_name}': {e}")

    # ==========================================
    # STEP 2: HIBP BREACH CHECK
    # ==========================================
    def step_2_hibp_breach_check(self):
        self.log("=" * 60)
        self.log("STEP 2: HaveIBeenPwned Breach Check")
        self.log("=" * 60)

        for email in self.emails:
            try:
                url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email)}"
                headers = self._get_headers()
                headers["hibp-api-version"] = "3.0.0"

                if CONFIG["hibp_api_key"]:
                    headers["hibp-api-key"] = CONFIG["hibp_api_key"]

                time.sleep(1.5)
                response = self.session.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    breaches = response.json()
                    self.results["breach_data"].append(
                        {
                            "email": email,
                            "breaches": breaches,
                            "count": len(breaches),
                            "sources": [b.get("Name") for b in breaches],
                        }
                    )
                    self.log(f"[OK] Found {len(breaches)} breaches for {email}")
                    for b in breaches[:5]:
                        self.log(
                            f"  - {b.get('Name')}: {str(b.get('Description', ''))[:60]}..."
                        )
                elif response.status_code == 404:
                    self.log(f"[OK] No breaches found for {email}")
                    self.results["email_findings"][email] = {
                        "status": "clean",
                        "breach_count": 0,
                    }
                elif response.status_code == 401:
                    self.log(
                        f"[WARN] HIBP 401 — API key required. Set HIBP_API_KEY env var."
                    )
                    self.results["email_findings"][email] = {
                        "status": "api_key_required"
                    }
                elif response.status_code == 429:
                    self.log(f"[WARN] HIBP rate limited. Try again later.")
                    self.results["email_findings"][email] = {
                        "status": "rate_limited"
                    }
                else:
                    self.log(
                        f"[WARN] HIBP HTTP {response.status_code} for {email}"
                    )
                    self.results["email_findings"][email] = {
                        "status": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                self.log(f"[ERR] HIBP Error for {email}: {e}")
                self.results["email_findings"][email] = {
                    "status": "error",
                    "error": str(e),
                }

    # ==========================================
    # STEP 3: DEHASHED SEARCH
    # ==========================================
    def step_3_dehashed_search(self):
        self.log("=" * 60)
        self.log("STEP 3: Dehashed Database Search")
        self.log("=" * 60)

        if not CONFIG["dehashed_api_key"] or not CONFIG["dehashed_email"]:
            self.log(
                "[WARN] Dehashed credentials not set. Set DEHASHED_EMAIL and DEHASHED_API_KEY env vars."
            )
            return

        try:
            url = "https://api.dehashed.com/search"
            auth = requests.auth.HTTPBasicAuth(
                CONFIG["dehashed_email"], CONFIG["dehashed_api_key"]
            )

            queries = [
                f"email:{self.emails[0]}",
                f"email:{self.emails[1]}",
                f"phone:{self.phones[0]}",
                f"phone:{self.phones[1]}",
                f'name:"{self.name}"',
                f"username:{self.ig_handle}",
            ]

            for query in queries:
                time.sleep(1.0)
                params = {"query": query, "size": 100}
                response = self.session.get(
                    url, params=params, auth=auth, timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("total", 0)
                    if total > 0:
                        self.log(
                            f"[OK] Dehashed: {total} records for {query[:40]}"
                        )
                        for entry in data.get("entries", [])[:20]:
                            self.results["breach_data"].append(
                                {
                                    "source": "Dehashed",
                                    "email": entry.get("email"),
                                    "username": entry.get("username"),
                                    "password": entry.get(
                                        "password", "HIDDEN"
                                    ),
                                    "ip_address": entry.get("ip_address"),
                                    "name": entry.get("name"),
                                    "database": entry.get("database"),
                                    "phone": entry.get("phone"),
                                    "address": entry.get("address"),
                                }
                            )
                    else:
                        self.log(
                            f"  Dehashed: No results for {query[:40]}"
                        )
                elif response.status_code == 401:
                    self.log("[ERR] Invalid Dehashed API credentials")
                    return
                else:
                    self.log(
                        f"[WARN] Dehashed HTTP {response.status_code} for {query[:40]}"
                    )
        except Exception as e:
            self.log(f"[ERR] Dehashed Error: {e}")

    # ==========================================
    # STEP 4: USERNAME ENUMERATION
    # ==========================================
    def step_4_username_enumeration(self):
        self.log("=" * 60)
        self.log("STEP 4: Username Enumeration")
        self.log("=" * 60)

        platforms = [
            ("Instagram", f"https://instagram.com/{self.ig_handle}"),
            ("Twitter/X", f"https://x.com/{self.ig_handle}"),
            ("Reddit", f"https://reddit.com/user/{self.ig_handle}"),
            ("GitHub", f"https://github.com/{self.ig_handle}"),
            ("LinkedIn", f"https://linkedin.com/in/{self.ig_handle}"),
            ("TikTok", f"https://tiktok.com/@{self.ig_handle}"),
            ("Facebook", f"https://facebook.com/{self.ig_handle}"),
            ("Pinterest", f"https://pinterest.com/{self.ig_handle}"),
            ("YouTube", f"https://youtube.com/@{self.ig_handle}"),
            ("Snapchat", f"https://snapchat.com/add/{self.ig_handle}"),
            ("Twitch", f"https://twitch.tv/{self.ig_handle}"),
            ("Tumblr", f"https://{self.ig_handle}.tumblr.com"),
            ("Medium", f"https://medium.com/@{self.ig_handle}"),
            ("SoundCloud", f"https://soundcloud.com/{self.ig_handle}"),
            ("Spotify", f"https://open.spotify.com/user/{self.ig_handle}"),
            ("Discord", f"https://discord.com/users/{self.ig_handle}"),
            ("Steam", f"https://steamcommunity.com/id/{self.ig_handle}"),
            ("Roblox", f"https://roblox.com/users/{self.ig_handle}/profile"),
            ("Fansly", f"https://fansly.com/{self.ig_handle}"),
            ("Gumroad", f"https://gumroad.com/{self.ig_handle}"),
            ("Ko-fi", f"https://ko-fi.com/{self.ig_handle}"),
            ("OnlyFans", f"https://onlyfans.com/{self.ig_handle}"),
            ("Patreon", f"https://patreon.com/{self.ig_handle}"),
            ("BuyMeACoffee", f"https://buymeacoffee.com/{self.ig_handle}"),
            ("Substack", f"https://substack.com/@{self.ig_handle}"),
            ("Beacons", f"https://beacons.ai/{self.ig_handle}"),
        ]

        for platform_name, url in platforms:
            try:
                response = self._fetch(url, timeout=8)
                if response:
                    exists = response.status_code == 200
                    self.results["username_availability"][platform_name] = {
                        "url": url,
                        "exists": exists,
                        "status_code": response.status_code,
                    }
                    if exists:
                        self.log(f"[OK] {platform_name}: FOUND")
                    else:
                        self.log(
                            f"  {platform_name}: Not found ({response.status_code})"
                        )
                else:
                    self.results["username_availability"][platform_name] = {
                        "url": url,
                        "exists": False,
                        "status_code": "Error",
                    }
            except Exception as e:
                self.log(f"[ERR] {platform_name} Error: {e}")
                self.results["username_availability"][platform_name] = {
                    "status": "error",
                    "error": str(e),
                }

    # ==========================================
    # STEP 5: SOCIAL MEDIA CONTENT
    # ==========================================
    def step_5_social_media_content(self):
        self.log("=" * 60)
        self.log("STEP 5: Social Media Content Scraping")
        self.log("=" * 60)

        profiles = [
            ("Instagram", f"https://instagram.com/{self.ig_handle}"),
            ("Reddit", f"https://reddit.com/user/{self.ig_handle}"),
            ("Pinterest", f"https://pinterest.com/{self.ig_handle}"),
            ("Twitch", f"https://twitch.tv/{self.ig_handle}"),
            ("TikTok", f"https://tiktok.com/@{self.ig_handle}"),
        ]

        for platform, url in profiles:
            try:
                response = self._fetch(url, timeout=10)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    info = {
                        "url": url,
                        "status": "found",
                        "title": "",
                        "bio": "",
                        "photos": [],
                    }

                    title_tag = soup.find("title")
                    if title_tag:
                        info["title"] = title_tag.get_text(strip=True)

                    for meta in soup.find_all("meta"):
                        prop = meta.get("property", "")
                        if prop == "og:image":
                            img_url = meta.get("content", "")
                            if img_url and img_url.startswith("http"):
                                fname = (
                                    f"{platform.lower()}_{self.ig_handle}_og.jpg"
                                )
                                self._download_photo(img_url, fname)
                                info["photos"].append(
                                    {"url": img_url, "path": fname}
                                )
                        elif prop == "og:description":
                            info["bio"] = meta.get("content", "")[:200]

                    if platform == "Instagram":
                        for script in soup.find_all(
                            "script", type="application/ld+json"
                        ):
                            try:
                                data = json.loads(script.string)
                                if isinstance(data, dict) and "image" in data:
                                    img_url = data["image"].get("url", "")
                                    if img_url:
                                        fname = f"instagram_{self.ig_handle}_ld.jpg"
                                        self._download_photo(img_url, fname)
                                        info["photos"].append(
                                            {"url": img_url, "path": fname}
                                        )
                            except:
                                pass

                    if platform == "Pinterest":
                        img = soup.find(
                            "img", {"src": re.compile(r"pinimg\.com")}
                        )
                        if img:
                            img_url = img.get("src", "")
                            if img_url:
                                fname = (
                                    f"pinterest_{self.ig_handle}_profile.jpg"
                                )
                                self._download_photo(img_url, fname)
                                info["photos"].append(
                                    {"url": img_url, "path": fname}
                                )

                    self.results["social_media_content"][platform] = info
                    self.log(
                        f"[OK] {platform}: Scraped ({len(info['photos'])} photos)"
                    )
                else:
                    self.log(f"  {platform}: Not accessible")
            except Exception as e:
                self.log(f"[ERR] {platform} scrape error: {e}")

    # ==========================================
    # STEP 6: PHONE ANALYSIS
    # ==========================================
    def step_6_phone_analysis(self):
        self.log("=" * 60)
        self.log("STEP 6: Phone Number Analysis")
        self.log("=" * 60)

        for phone in self.phones:
            self.log(f"\nAnalyzing: +91{phone}")
            self.results["phone_findings"].setdefault(f"+91{phone}", {})

            try:
                url = f"https://wa.me/+91{phone}"
                response = self._fetch(url, timeout=8)
                self.results["phone_findings"][f"+91{phone}"]["WhatsApp"] = {
                    "url": url,
                    "exists": response and response.status_code == 200,
                    "status_code": response.status_code if response else "Error",
                }
                self.log(
                    f"  WhatsApp: {'FOUND' if response and response.status_code == 200 else 'Not found'}"
                )
            except Exception as e:
                self.log(f"  WhatsApp error: {e}")

            try:
                url = f"https://www.truecaller.com/search/in/{phone}"
                response = self._fetch(url, timeout=8)
                exists = (
                    response
                    and response.status_code == 200
                    and "not found" not in response.text.lower()
                )
                self.results["phone_findings"][f"+91{phone}"][
                    "Truecaller"
                ] = {
                    "url": url,
                    "exists": exists,
                    "status_code": response.status_code if response else "Error",
                }
                self.log(
                    f"  Truecaller: {'FOUND' if exists else 'Not found'}"
                )
            except Exception as e:
                self.log(f"  Truecaller error: {e}")

            try:
                links = self._duckduckgo_search(f"+91{phone} \"{self.name}\"")
                if links:
                    self.results["phone_findings"][f"+91{phone}"][
                        "search_results"
                    ] = links[:5]
                    self.log(f"  Web search: {len(links)} results")
                else:
                    self.log(f"  Web search: No results")
            except Exception as e:
                self.log(f"  Web search error: {e}")

    # ==========================================
    # STEP 7: DARKWEB / PASTE SEARCH
    # ==========================================
    def step_7_darkweb_search(self):
        self.log("=" * 60)
        self.log("STEP 7: Darkweb / Paste Search")
        self.log("=" * 60)

        if not CONFIG["darkweb_enabled"]:
            self.log("[WARN] Darkweb search disabled")
            return

        targets = (
            [self.name, self.pan]
            + [f"+91{p}" for p in self.phones]
            + self.emails
        )

        paste_sites = [
            "site:pastebin.com",
            "site:ghostbin.com",
            "site:rentry.co",
            "site:controlc.com",
        ]

        for target in targets:
            for site in paste_sites:
                try:
                    query = f'{site} "{target}"'
                    links = self._duckduckgo_search(query)
                    if links:
                        for link in links:
                            self.results["darkweb_findings"].append(
                                {
                                    "source": site.replace("site:", ""),
                                    "title": link["title"],
                                    "url": link["url"],
                                    "matched_keyword": target,
                                }
                            )
                        self.log(
                            f"[OK] {site.replace('site:', '')}: {len(links)} results for {str(target)[:30]}"
                        )
                    else:
                        self.log(
                            f"  {site.replace('site:', '')}: No results for {str(target)[:30]}"
                        )
                except Exception as e:
                    self.log(f"[ERR] Paste search error for {target}: {e}")

        try:
            query = f'site:doxbin.com "{self.name}"'
            links = self._duckduckgo_search(query)
            if links:
                for link in links:
                    self.results["darkweb_findings"].append(
                        {
                            "source": "Doxbin",
                            "title": link["title"],
                            "url": link["url"],
                            "matched_keyword": self.name,
                        }
                    )
                self.log(f"[OK] Doxbin: {len(links)} results")
        except Exception as e:
            self.log(f"[ERR] Doxbin search error: {e}")

    # ==========================================
    # STEP 8: DOMAIN SEARCH
    # ==========================================
    def step_8_domain_search(self):
        self.log("=" * 60)
        self.log("STEP 8: Domain Search")
        self.log("=" * 60)

        name_flat = self.name.lower().replace(" ", "").replace("'", "")
        domain_variations = [
            f"{name_flat}.com",
            f"{name_flat}.in",
            f"{name_flat}.org",
            f"{self.ig_handle}.com",
            f"{self.ig_handle}.in",
            f"{self.ig_handle}.org",
            f"{self.first_name.lower()}.com",
            f"{self.first_name.lower()}.in",
            f"{self.first_name.lower()}.org",
        ]

        for domain in domain_variations:
            try:
                for scheme in ("https://", "http://"):
                    url = f"{scheme}{domain}"
                    response = self._fetch(url, timeout=4)
                    if response and response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        title = soup.title.string if soup.title else "N/A"
                        self.results["domain_search"].append(
                            {
                                "domain": domain,
                                "status": "active",
                                "status_code": response.status_code,
                                "title": title[:100],
                                "html_size": len(response.text),
                            }
                        )
                        self.log(
                            f"[OK] Domain found: {domain} ({title[:40]})"
                        )
                        break
            except:
                pass

    # ==========================================
    # STEP 9: FAMILY SEARCH
    # ==========================================
    def step_9_family_search(self):
        self.log("=" * 60)
        self.log("STEP 9: Family Member Search")
        self.log("=" * 60)

        for relation, name in self.data["family"].items():
            try:
                query = f'"{name}"'
                links = self._duckduckgo_search(query)

                if links:
                    self.results["family_search"][relation] = {
                        "name": name,
                        "results": links[:5],
                    }
                    self.log(
                        f"[OK] {relation} ({name}): {len(links)} results"
                    )
                    for link in links[:2]:
                        self.log(f"  - {link['title'][:50]}")
                else:
                    self.log(f"  {relation} ({name}): No results")
            except Exception as e:
                self.log(f"[ERR] Family search error for {name}: {e}")

    # ==========================================
    # STEP 10: ADDRESS GEOLOCATION
    # ==========================================
    def step_10_address_geolocation(self):
        self.log("=" * 60)
        self.log("STEP 10: Address Geolocation Search")
        self.log("=" * 60)

        searches = [
            (f'"507121" "{self.name}"', "PIN Code Search"),
            (f'"Jaggavaram" "{self.name}"', "Village Search"),
            (f'"Kunavaram" "{self.name}"', "Mandal Search"),
            (f'"{self.name}" "East Godavari"', "District Search"),
        ]

        for query, source in searches:
            try:
                links = self._duckduckgo_search(query)
                if links:
                    self.results["address_search"].append(
                        {
                            "query": query,
                            "source": source,
                            "results": links[:5],
                        }
                    )
                    self.log(f"[OK] {source}: {len(links)} results")
                else:
                    self.log(f"  {source}: No results")
            except Exception as e:
                self.log(f"[ERR] Address search error: {e}")

    # ==========================================
    # STEP 11: FINANCIAL & ID CHECKS
    # ==========================================
    def step_11_financial_checks(self):
        self.log("=" * 60)
        self.log("STEP 11: Financial & ID Checks")
        self.log("=" * 60)

        try:
            query = f'"{self.pan}" PAN'
            links = self._duckduckgo_search(query)
            self.results["pan_findings"] = {
                "pan": self.pan,
                "search_results": links[:5] if links else [],
                "timestamp": datetime.now().isoformat(),
            }
            if links:
                self.log(
                    f"[OK] PAN {self.pan}: {len(links)} search results"
                )
            else:
                self.log(f"  PAN {self.pan}: No search results")
        except Exception as e:
            self.results["pan_findings"] = {
                "pan": self.pan,
                "status": "error",
                "error": str(e),
            }

        try:
            query = f'"{self.data["ids"]["caste_cert_no"]}" caste'
            links = self._duckduckgo_search(query)
            self.results["financial_checks"]["caste_cert"] = {
                "cert_no": self.data["ids"]["caste_cert_no"],
                "search_results": links[:5] if links else [],
            }
            if links:
                self.log(f"[OK] Caste cert: {len(links)} results")
        except:
            pass

        try:
            query = f'"{self.data["insurance"]["policy_no"]}" HDFC ERGO'
            links = self._duckduckgo_search(query)
            self.results["financial_checks"]["insurance"] = {
                "policy_no": self.data["insurance"]["policy_no"],
                "provider": self.data["insurance"]["provider"],
                "search_results": links[:5] if links else [],
            }
            if links:
                self.log(f"[OK] Insurance: {len(links)} results")
        except:
            pass

    # ==========================================
    # RUN ALL
    # ==========================================
    def run(self):
        self.log("=" * 80)
        self.log(f"  ADVANCED OSINT AGENT v2.1 (Fixed)")
        self.log(f"  Target: {self.name}")
        self.log(f"  Emails: {', '.join(self.emails)}")
        self.log(f"  Phones: {', '.join('+91'+p for p in self.phones)}")
        self.log(f"  Username: @{self.ig_handle}")
        self.log(f"  PAN: {self.pan}")
        self.log(
            f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.log("=" * 80)

        self.step_1_search_engine()
        self.step_2_hibp_breach_check()
        self.step_3_dehashed_search()
        self.step_4_username_enumeration()
        self.step_5_social_media_content()
        self.step_6_phone_analysis()
        self.step_7_darkweb_search()
        self.step_8_domain_search()
        self.step_9_family_search()
        self.step_10_address_geolocation()
        self.step_11_financial_checks()

        search_results = sum(
            [len(v) for v in self.results["search_engine_results"].values()]
        )
        social_profiles = sum(
            [
                1
                for v in self.results["username_availability"].values()
                if v.get("exists")
            ]
        )
        darkweb_findings = len(self.results.get("darkweb_findings", []))
        photos_saved = len(self.results.get("photos_downloaded", []))
        domain_found = len(self.results.get("domain_search", []))

        self.results["summary"] = {
            "target": self.name,
            "search_engine_results": search_results,
            "social_profiles_found": social_profiles,
            "darkweb_findings": darkweb_findings,
            "photos_saved": photos_saved,
            "domains_found": domain_found,
            "emails_checked": len(self.emails),
            "phones_checked": len(self.phones),
            "usernames_checked": len(self.usernames),
            "platforms_scanned": len(self.results["username_availability"]),
            "scan_completed": datetime.now().isoformat(),
        }

        self.log("=" * 80)
        self.log("  SCAN COMPLETE")
        self.log(f"  Search Results: {search_results}")
        self.log(f"  Social Profiles: {social_profiles}")
        self.log(f"  Darkweb Findings: {darkweb_findings}")
        self.log(f"  Domains Found: {domain_found}")
        self.log(f"  Photos Saved: {photos_saved}")
        self.log("=" * 80)

        return self.results


if __name__ == "__main__":
    agent = AdvancedOSINTAgent()
    results = agent.run()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        CONFIG["output_dir"], f"osint_results_{timestamp}.json"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[+] Results saved to: {output_file}")
    print(f"[+] Photos saved to: {os.path.join(CONFIG['output_dir'], 'photos')}")
    print(json.dumps(results, indent=2, ensure_ascii=False))