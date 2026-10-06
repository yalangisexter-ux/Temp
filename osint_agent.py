import json
import sys
import io
import time
import random
import re
import os
from urllib.parse import quote
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependencies. Install them with: "
        "pip install requests beautifulsoup4"
    ) from exc

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG = {
    "hibp_api_key": os.environ.get("HIBP_API_KEY", ""),
    "dehashed_api_key": os.environ.get("DEHASHED_API_KEY", ""),
    "delay_min": 0.3,
    "delay_max": 0.8,
    "timeout": 15
}

# ==========================================
# 2. THE DATA: Target Profile
# ==========================================
PROFILE_DATA = {
    "profile": {
        "name": "Karam Hemarusha",
        "dob": "19-11-1999",
        "age": 26,
        "gender": "Female",
        "community": "ST (Koya)",
        "height_cm": 164,
        "weight_kg": 78,
        "distinctive_marks": ["Mole on left cheek", "Mole on right eyebrow"]
    },
    "family": {
        "father": "Karam Harinath Babu",
        "mother": "Karam Parvathi",
        "sister": "Karam Shanvitha Rani"
    },
    "contact": {
        "primary_phone": "+919010183934",
        "secondary_phone": "+919490686935",
        "email_primary": "hemarusha19@gmail.com",
        "email_secondary": "hemarushaharinath.k@gmail.com",
        "instagram_handle": "@miss.h_a_pp_y"
    },
    "addresses": {
        "aadhaar_address": "1-81, Jaggavaram Village, Chuchirevulagudem Post, Kunavaram Mandal, East Godavari District, AP - 507121",
        "insurance_address_note": "PIN 533350, Alluri Sitarama Raju District"
    },
    "ids": {
        "aadhaar_partial": "5038 **** **** 8975",
        "pan": "KJCPK0810B",
        "caste_cert_no": "CGC011504710040"
    },
    "insurance": {
        "provider": "HDFC ERGO",
        "policy_no": "28000000607624",
        "plan": "my:Optima Secure",
        "nominee": "Karam Shanvitha Rani"
    }
}

class RealOSINTAgent:
    def __init__(self):
        self.data = PROFILE_DATA
        self.name = self.data["profile"]["name"]
        self.first_name = self.name.split()[0]
        self.last_name = " ".join(self.name.split()[1:]) if len(self.name.split()) > 1 else ""
        self.phones = [p.replace("+91", "") for p in [self.data["contact"]["primary_phone"], self.data["contact"]["secondary_phone"]]]
        self.emails = [self.data["contact"]["email_primary"], self.data["contact"]["email_secondary"]]
        self.pan = self.data["ids"]["pan"]
        self.ig_handle = self.data["contact"]["instagram_handle"].replace("@", "")
        self.usernames = self._generate_usernames()
        self.results = {
            "target": self.name,
            "profile": self.data["profile"],
            "breach_data": [],
            "email_findings": {},
            "phone_findings": {},
            "username_availability": {},
            "social_media_presence": {},
            "social_media_content": {},
            "google_dorking": {},
            "domain_search": [],
            "discord_servers": [],
            "pan_findings": {},
            "address_search": [],
            "family_search": {},
            "content_platform_status": {},
            "financial_checks": {},
            "summary": ""
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _generate_usernames(self):
        names = self.name.lower().replace(" ", "").replace("'", "")
        variations = set()
        variations.add(self.ig_handle)
        variations.add(names)
        variations.add(names.replace(" ", "_"))
        variations.add(names.replace(" ", "."))
        variations.add(names.split()[0])
        variations.add(self.first_name.lower())
        variations.add(self.last_name.lower() if self.last_name else "")
        variations.add(f"{self.first_name.lower()}{self.last_name.lower()}")
        variations.add(f"{self.first_name.lower()}_{self.last_name.lower()}")
        variations.add(f"{self.first_name.lower()}.{self.last_name.lower()}")
        return list(variations)

    def log(self, msg):
        print(f"[OSINT-AGENT] {msg}")

    def _fetch(self, url, params=None, timeout=None):
        try:
            time.sleep(random.uniform(CONFIG["delay_min"], CONFIG["delay_max"]))
            response = self.session.get(url, params=params, timeout=timeout or CONFIG["timeout"])
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Fetch Error for {url}: {e}")
            return None

    def step_1_hibp_breach_check(self):
        self.log("="*50)
        self.log("STEP 1: HaveIBeenPwned Breach Check")
        self.log("="*50)
        for email in self.emails:
            try:
                url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
                headers = self.headers.copy()
                headers["hibp-api-version"] = "3.0.0"
                headers["user-agent"] = "OSINT-Agent/1.0"
                if CONFIG["hibp_api_key"]:
                    headers["hibp-api-key"] = CONFIG["hibp_api_key"]
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    breaches = response.json()
                    self.results["breach_data"].append({
                        "email": email, "breaches": breaches,
                        "count": len(breaches), "sources": [b.get("Name") for b in breaches]
                    })
                    self.log(f"[OK] Found {len(breaches)} breaches for {email}")
                    for b in breaches[:5]:
                        self.log(f"  - {b.get('Name')}: {b.get('Description', '')[:50]}...")
                elif response.status_code == 404:
                    self.log(f"[OK] No breaches found for {email}")
                    self.results["email_findings"][email] = {"status": "clean", "breach_count": 0}
                elif response.status_code == 403:
                    self.log(f"[WARN] Rate limited for {email}")
                    self.results["email_findings"][email] = {"status": "rate_limited"}
                else:
                    self.log(f"[WARN] HTTP {response.status_code} for {email}")
                    self.results["email_findings"][email] = {"status": f"HTTP {response.status_code}"}
            except Exception as e:
                self.log(f"[ERR] HIBP Error for {email}: {e}")
                self.results["email_findings"][email] = {"status": "error", "error": str(e)}

    def step_2_dehashed_search(self):
        self.log("="*50)
        self.log("STEP 2: Dehashed Database Search")
        self.log("="*50)
        if not CONFIG["dehashed_api_key"]:
            self.log("[WARN] Dehashed API key not set. Skipping.")
            return
        try:
            url = "https://api.dehashed.com/search"
            headers = {"Authorization": CONFIG["dehashed_api_key"], "Content-Type": "application/json"}
            data = {"query": f"email:{self.emails[0]} OR email:{self.emails[1]}", "size": 100, "page": 1}
            response = requests.post(url, json=data, headers=headers, timeout=15)
            if response.status_code == 200:
                results = response.json()
                if results.get("total", 0) > 0:
                    self.log(f"[OK] Found {results['total']} records in Dehashed")
                    for record in results.get("entries", [])[:10]:
                        self.results["breach_data"].append({
                            "source": "Dehashed", "email": record.get("email"),
                            "username": record.get("username"), "password": record.get("password", "HIDDEN"),
                            "ip_address": record.get("ip_address"), "name": record.get("name")
                        })
            elif response.status_code == 401:
                self.log("[ERR] Invalid Dehashed API key")
        except Exception as e:
            self.log(f"[ERR] Dehashed Error: {e}")

    def step_3_username_enumeration(self):
        self.log("="*50)
        self.log("STEP 3: Username Enumeration")
        self.log("="*50)
        platforms = [
            ("Instagram", f"https://instagram.com/{self.ig_handle}"),
            ("Twitter/X", f"https://twitter.com/{self.ig_handle}"),
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
            ("Blogger", f"https://{self.ig_handle}.blogspot.com"),
            ("Wordpress", f"https://{self.ig_handle}.wordpress.com"),
            ("Medium", f"https://medium.com/@{self.ig_handle}"),
            ("StackOverflow", f"https://stackoverflow.com/users/{self.ig_handle}"),
            ("DeviantArt", f"https://deviantart.com/{self.ig_handle}"),
            ("Flickr", f"https://flickr.com/people/{self.ig_handle}"),
            ("Vimeo", f"https://vimeo.com/{self.ig_handle}"),
            ("SoundCloud", f"https://soundcloud.com/{self.ig_handle}"),
            ("Spotify", f"https://open.spotify.com/user/{self.ig_handle}"),
            ("Discord", f"https://discord.com/users/{self.ig_handle}"),
            ("Steam", f"https://steamcommunity.com/id/{self.ig_handle}"),
            ("Roblox", f"https://roblox.com/users/{self.ig_handle}/profile"),
            ("Minecraft", f"https://namemc.com/profile/{self.ig_handle}"),
            ("Tinder", f"https://tinder.com/@{self.ig_handle}"),
            ("Bumble", f"https://bumble.com/@{self.ig_handle}"),
            ("Hinge", f"https://hinge.co/@{self.ig_handle}"),
            ("OnlyFans", f"https://onlyfans.com/{self.ig_handle}"),
            ("Fansly", f"https://fansly.com/{self.ig_handle}"),
            ("Patreon", f"https://patreon.com/{self.ig_handle}"),
            ("Gumroad", f"https://gumroad.com/{self.ig_handle}"),
            ("Ko-fi", f"https://ko-fi.com/{self.ig_handle}"),
            ("BuyMeACoffee", f"https://buymeacoffee.com/{self.ig_handle}"),
        ]
        for platform_name, url in platforms:
            try:
                response = self._fetch(url, timeout=10)
                if response:
                    is_available = response.status_code == 404 or "Not Found" in response.text
                    self.results["username_availability"][platform_name] = {
                        "url": url, "exists": not is_available, "status_code": response.status_code
                    }
                    if not is_available:
                        self.log(f"[OK] {platform_name}: FOUND")
                    else:
                        self.log(f"  {platform_name}: Not found")
            except Exception as e:
                self.log(f"[ERR] {platform_name} Error: {e}")
                self.results["username_availability"][platform_name] = {"status": "error", "error": str(e)}

    def step_4_google_dorking(self):
        self.log("="*50)
        self.log("STEP 4: Google Dorking")
        self.log("="*50)
        dorks = {
            "Email in quotes": f'"{self.emails[0]}"',
            "Email wildcard": f'{self.emails[0].split("@")[0]}*',
            "Phone number": f'"{self.phones[0]}"',
            "Full name": f'"{self.name}"',
            "Name + email": f'"{self.name}" "{self.emails[0]}"',
            "Name + phone": f'"{self.name}" "{self.phones[0]}"',
            "PAN card": f'"{self.pan}"',
            "Aadhaar partial": f'"{self.data["ids"]["aadhaar_partial"]}"',
            "Caste cert": f'"{self.data["ids"]["caste_cert_no"]}"',
            "Insurance policy": f'"{self.data["insurance"]["policy_no"]}"',
            "Username only": f'"{self.ig_handle}"',
            "Site:instagram": f'site:instagram.com "{self.name}"',
            "Site:twitter": f'site:twitter.com "{self.name}"',
            "Site:linkedin": f'site:linkedin.com "{self.name}"',
            "Site:facebook": f'site:facebook.com "{self.name}"',
            "Filetype PDF": f'filetype:pdf "{self.name}"',
            "Filetype DOC": f'filetype:doc "{self.name}"',
            "Filetype XLS": f'filetype:xls "{self.name}"',
            "Filetype PPT": f'filetype:ppt "{self.name}"',
            "Filetype CSV": f'filetype:csv "{self.name}"',
            "Site:reddit": f'site:reddit.com "{self.ig_handle}"',
            "Site:github": f'site:github.com "{self.ig_handle}"',
            "Site:onlyfans": f'site:onlyfans.com "{self.name}"',
            "Site:patreon": f'site:patreon.com "{self.name}"',
            "Pastebin": f'site:pastebin.com "{self.name}"',
            "Doxbin": f'site:doxbin.com "{self.name}"',
        }
        for dork_name, query in dorks.items():
            try:
                url = f"https://www.google.com/search?q={quote(query)}&num=20"
                response = self._fetch(url, timeout=15)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if 'https://' in href and '/url?q=' in href:
                            actual_url = href.split('/url?q=')[1].split('&')[0]
                            title = a.get_text(strip=True)
                            links.append({"url": actual_url, "title": title})
                    if links:
                        self.results["google_dorking"][dork_name] = links[:10]
                        self.log(f"[OK] {dork_name}: {len(links)} results")
                    else:
                        self.log(f"  {dork_name}: No results")
            except Exception as e:
                self.log(f"[ERR] Dork error '{dork_name}': {e}")

    def step_5_social_media_content(self):
        self.log("="*50)
        self.log("STEP 5: Social Media Content Scraping")
        self.log("="*50)
        profiles = [
            ("Instagram", f"https://instagram.com/{self.ig_handle}"),
            ("Reddit", f"https://reddit.com/user/{self.ig_handle}"),
            ("LinkedIn", f"https://linkedin.com/in/{self.ig_handle}"),
            ("TikTok", f"https://tiktok.com/@{self.ig_handle}"),
            ("Pinterest", f"https://pinterest.com/{self.ig_handle}"),
        ]
        for platform, url in profiles:
            try:
                response = self._fetch(url, timeout=10)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    info = {"url": url, "status": "found", "title": "", "bio": "", "followers": "", "following": "", "posts": ""}
                    title_tag = soup.find('title')
                    if title_tag:
                        info["title"] = title_tag.get_text(strip=True)
                    meta_tags = soup.find_all('meta')
                    for meta in meta_tags:
                        if meta.get('property') == 'og:description':
                            info["bio"] = meta.get('content', '')[:200]
                        elif meta.get('property') == 'og:title':
                            info["title"] = meta.get('content', '')
                    self.results["social_media_content"][platform] = info
                    self.log(f"[OK] {platform}: Scraped")
                else:
                    self.log(f"  {platform}: Not accessible")
            except Exception as e:
                self.log(f"[ERR] {platform} scrape error: {e}")

    def step_6_phone_analysis(self):
        self.log("="*50)
        self.log("STEP 6: Phone Number Analysis")
        self.log("="*50)
        for phone in self.phones:
            self.log(f"\nAnalyzing: {phone}")
            try:
                url = f"https://wa.me/{'+91' + phone}"
                response = self._fetch(url, timeout=10)
                self.results["phone_findings"].setdefault(phone, {})
                self.results["phone_findings"][phone]["WhatsApp"] = {"url": url, "exists": response.status_code == 200, "status_code": response.status_code if response else "Error"}
            except:
                pass
            try:
                url = f"https://www.truecaller.com/search/in/{phone}"
                response = self._fetch(url, timeout=10)
                self.results["phone_findings"][phone]["Truecaller"] = {"url": url, "exists": response.status_code == 200, "status_code": response.status_code if response else "Error"}
            except:
                pass
            try:
                url = f"https://sync.me/search/{phone}"
                response = self._fetch(url, timeout=10)
                if response:
                    self.results["phone_findings"][phone]["Sync.me"] = {"url": url, "exists": response.status_code == 200, "status_code": response.status_code}
            except:
                pass
            try:
                url = f"https://www.whocallswho.com/{phone}"
                response = self._fetch(url, timeout=10)
                if response:
                    self.results["phone_findings"][phone]["WhoCallsWho"] = {"url": url, "exists": response.status_code == 200, "status_code": response.status_code}
            except:
                pass

    def step_7_doxbin_search(self):
        self.log("="*50)
        self.log("STEP 7: Doxbin Search")
        self.log("="*50)
        targets = [self.name, self.pan] + self.phones + self.emails
        for target in targets:
            try:
                url = f"https://www.doxbin.com/search?q={quote(target)}"
                response = self._fetch(url, timeout=15)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results_found = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        title = link.get_text(strip=True)
                        if target.lower() in href.lower() or target.lower() in title.lower():
                            full_url = href if href.startswith('http') else f"https://www.doxbin.com{href}"
                            if full_url not in results_found:
                                results_found.append(full_url)
                                self.results["breach_data"].append({"source": "Doxbin", "title": title if title else "Unnamed Paste", "url": full_url, "matched_keyword": target})
                                self.log(f"[OK] Found: {title}")
                else:
                    self.log(f"  Doxbin blocked for {target[:20]}...")
            except Exception as e:
                self.log(f"[ERR] Doxbin Error for {target}: {e}")

    def step_8_domain_search(self):
        self.log("="*50)
        self.log("STEP 8: Domain Search")
        self.log("="*50)
        domain_variations = [
            f"{self.name.replace(' ', '')}.com",
            f"{self.name.replace(' ', '')}.in",
            f"{self.name.replace(' ', '')}.org",
            f"{self.ig_handle}.com",
            f"{self.ig_handle}.in",
            f"{self.ig_handle}.org",
            f"{self.first_name.lower()}.com",
        ]
        for domain in domain_variations:
            try:
                url = f"https://{domain}"
                response = self._fetch(url, timeout=5)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    self.results["domain_search"].append({"domain": domain, "status": "active", "status_code": response.status_code, "title": soup.title.string if soup.title else "N/A"})
                    self.log(f"[OK] Domain found: {domain}")
            except:
                pass

    def step_9_family_search(self):
        self.log("="*50)
        self.log("STEP 9: Family Member Search")
        self.log("="*50)
        family = self.data["family"]
        for relation, name in family.items():
            try:
                url = f"https://www.google.com/search?q={quote(f'\"{name}\"')}&num=10"
                response = self._fetch(url, timeout=15)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = []
                    for a in soup.find_all('a', href=True):
                        if 'https://' in a['href']:
                            links.append(a['href'])
                    if links:
                        self.results["family_search"][relation] = {"name": name, "results": links[:5]}
                        self.log(f"[OK] {relation} ({name}): {len(links)} results")
                    else:
                        self.log(f"  {relation} ({name}): No results")
            except Exception as e:
                self.log(f"[ERR] Family search error for {name}: {e}")

    def step_10_discord_search(self):
        self.log("="*50)
        self.log("STEP 10: Discord Server Search")
        self.log("="*50)
        try:
            url = "https://disboard.org/api/servers/search"
            params = {"search": quote(f"{self.name} leaks"), "limit": "5", "lang": "en"}
            response = self._fetch(url, params=params)
            if response and response.status_code == 200:
                data = response.json()
                servers = data.get('servers', [])
                self.results["discord_servers"] = []
                for server in servers[:5]:
                    self.results["discord_servers"].append({
                        "name": server.get('name'), "members": server.get('memberCount'),
                        "invite_link": server.get('inviteUrl'), "description": server.get('description', '')[:100]
                    })
                    self.log(f"[OK] Found Discord: {server.get('name')}")
            else:
                self.log("  Discord API blocked or no results")
        except Exception as e:
            self.log(f"[ERR] Discord search error: {e}")

    def step_11_content_platforms(self):
        self.log("="*50)
        self.log("STEP 11: Content Platform Check")
        self.log("="*50)
        platforms = [
            ("OnlyFinder", f"https://onlyfinder.com/{self.ig_handle}"),
            ("FanVue", f"https://fanvue.com/{self.ig_handle}"),
            ("Fansly", f"https://fansly.com/{self.ig_handle}"),
            ("Patreon", f"https://patreon.com/{self.ig_handle}"),
            ("Gumroad", f"https://gumroad.com/{self.ig_handle}"),
            ("Ko-fi", f"https://ko-fi.com/{self.ig_handle}"),
            ("BuyMeACoffee", f"https://buymeacoffee.com/{self.ig_handle}"),
            ("Substack", f"https://substack.com/@{self.ig_handle}"),
            ("Beacons", f"https://beacons.ai/{self.ig_handle}"),
        ]
        for platform, url in platforms:
            try:
                response = self._fetch(url, timeout=10)
                if response:
                    exists = response.status_code == 200
                    self.results["content_platform_status"][platform] = {"url": url, "exists": exists, "status_code": response.status_code}
                    if exists:
                        self.log(f"[OK] {platform}: FOUND")
                    else:
                        self.log(f"  {platform}: Not found")
            except Exception as e:
                self.results["content_platform_status"][platform] = {"status": "error", "error": str(e)}

    def step_12_financial_checks(self):
        self.log("="*50)
        self.log("STEP 12: Financial & ID Checks")
        self.log("="*50)
        try:
            url = f"https://www.incometax.gov.in/itav/validatePan/{self.pan}"
            response = self._fetch(url, timeout=10)
            if response:
                self.results["pan_findings"] = {"pan": self.pan, "status_code": response.status_code, "verified": response.status_code == 200, "timestamp": datetime.now().isoformat()}
                if response.status_code == 200:
                    self.log(f"[OK] PAN verified: {self.pan}")
                else:
                    self.log(f"  PAN check: HTTP {response.status_code}")
        except Exception as e:
            self.results["pan_findings"] = {"pan": self.pan, "status": "error", "error": str(e)}
        try:
            url = f"https://cso.telangana.gov.in/certificateverify/{self.data['ids']['caste_cert_no']}"
            response = self._fetch(url, timeout=10)
            if response:
                self.results["financial_checks"]["caste_cert"] = {"cert_no": self.data["ids"]["caste_cert_no"], "status_code": response.status_code, "verified": response.status_code == 200}
        except:
            pass
        try:
            url = f"https://www.hdfcergo.com/policy-status/{self.data['insurance']['policy_no']}"
            response = self._fetch(url, timeout=10)
            if response:
                self.results["financial_checks"]["insurance"] = {"policy_no": self.data["insurance"]["policy_no"], "provider": self.data["insurance"]["provider"], "status_code": response.status_code}
        except:
            pass

    def step_13_address_geolocation(self):
        self.log("="*50)
        self.log("STEP 13: Address Geolocation Search")
        self.log("="*50)
        address = self.data["addresses"]["aadhaar_address"]
        pin = "507121"
        searches = [
            (f"\"{pin}\" {self.name}", "PIN Code Search"),
            (f"\"{address.split(',')[0]}\" {self.name}", "Address Search"),
            (f"\"{self.name}\" \"East Godavari\"", "District Search"),
            (f"\"{self.name}\" \"Jaggavaram\"", "Village Search"),
            (f"\"Kunavaram\" {self.name}", "Mandal Search"),
        ]
        for query, source in searches:
            try:
                url = f"https://www.google.com/search?q={quote(query)}&num=10"
                response = self._fetch(url, timeout=15)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []
                    for a in soup.find_all('a', href=True):
                        if 'https://' in a['href'] and a['href'] not in results:
                            results.append(a['href'])
                    if results:
                        self.results["address_search"].append({"query": query, "source": source, "results": results[:5]})
                        self.log(f"[OK] {source}: {len(results)} results")
            except Exception as e:
                self.log(f"[ERR] Address search error: {e}")

    def run(self):
        self.log("="*60)
        self.log(f"  REAL OSINT AGENT v2.0")
        self.log(f"  Target: {self.name}")
        self.log(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("="*60)
        self.step_1_hibp_breach_check()
        self.step_2_dehashed_search()
        self.step_3_username_enumeration()
        self.step_4_google_dorking()
        self.step_5_social_media_content()
        self.step_6_phone_analysis()
        self.step_7_doxbin_search()
        self.step_8_domain_search()
        self.step_9_family_search()
        self.step_10_discord_search()
        self.step_11_content_platforms()
        self.step_12_financial_checks()
        self.step_13_address_geolocation()
        total_breaches = sum([b.get('count', 0) for b in self.results['breach_data'] if 'breaches' in b])
        social_profiles = sum([1 for v in self.results['username_availability'].values() if v.get('exists')])
        discord_servers = len(self.results.get('discord_servers', []))
        content_platforms = sum([1 for v in self.results['content_platform_status'].values() if v.get('exists')])
        self.results["summary"] = {
            "target": self.name, "total_breaches": total_breaches,
            "social_profiles_found": social_profiles, "discord_servers": discord_servers,
            "content_platforms": content_platforms, "emails_checked": len(self.emails),
            "phones_checked": len(self.phones), "usernames_checked": len(self.usernames),
            "platforms_scanned": len(self.results["username_availability"]),
            "scan_completed": datetime.now().isoformat()
        }
        self.log("="*60)
        self.log("  SCAN COMPLETE")
        self.log(f"  Breaches: {total_breaches}")
        self.log(f"  Social Profiles: {social_profiles}")
        self.log(f"  Discord Servers: {discord_servers}")
        self.log(f"  Content Platforms: {content_platforms}")
        self.log("="*60)
        return self.results

if __name__ == "__main__":
    agent = RealOSINTAgent()
    results = agent.run()
    output_file = f"osint_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Results saved to: {output_file}")
    print(json.dumps(results, indent=2))