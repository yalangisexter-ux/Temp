#!/usr/bin/env python3
"""
================================================================================
  MASTER OSINT AGENT — Single script combining all working project code
  Target: Karam Hemarusha
  Generates: HTML report + JSON data
================================================================================
"""

import json, sys, io, os, re, time, random, base64
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

# ============================================================
# 1. TARGET PROFILE
# ============================================================
PROFILE = {
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


# ============================================================
# 2. MASTER OSINT AGENT
# ============================================================
class MasterOSINTAgent:
    def __init__(self):
        self.data = PROFILE
        self.name = self.data["profile"]["name"]
        self.first_name = self.name.split()[0]
        self.last_name = " ".join(self.name.split()[1:]) if len(self.name.split()) > 1 else ""
        self.phones = [p.replace("+91", "") for p in [self.data["contact"]["primary_phone"], self.data["contact"]["secondary_phone"]]]
        self.emails = [self.data["contact"]["email_primary"], self.data["contact"]["email_secondary"]]
        self.pan = self.data["ids"]["pan"]
        self.ig_handle = self.data["contact"]["instagram_handle"].replace("@", "")

        # Generate username variations
        self.usernames = self._generate_usernames()

        # Results container
        self.R = {
            "target": self.name,
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profile": self.data["profile"],
            "family": self.data["family"],
            "contact": self.data["contact"],
            "addresses": self.data["addresses"],
            "ids": self.data["ids"],
            "insurance": self.data["insurance"],

            # Scan results
            "web_search_results": [],
            "breach_data": [],
            "email_findings": {},
            "phone_findings": {},
            "username_availability": {},
            "social_media_content": {},
            "google_dorking": {},
            "domain_search": [],
            "discord_servers": [],
            "pan_findings": {},
            "address_search": [],
            "family_search": {},
            "content_platform_status": {},
            "financial_checks": {},
            "dark_web_leaks": [],
            "telegram_candidates": [],
            "summary": {}
        }

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })

    def _generate_usernames(self):
        names = self.name.lower().replace(" ", "").replace("'", "")
        parts = self.name.lower().split()
        variations = set()
        variations.add(self.ig_handle)
        variations.add(names)
        variations.add("_".join(parts))
        variations.add(".".join(parts))
        variations.add(parts[0])
        if len(parts) > 1:
            variations.add(parts[0] + parts[1])
            variations.add(parts[0] + "_" + parts[1])
            variations.add(parts[0] + "." + parts[1])
            variations.add(parts[1])
        return list(variations)

    def log(self, msg):
        print(f"[MASTER-OSINT] {msg}")

    def _fetch(self, url, params=None, timeout=15, headers=None):
        try:
            time.sleep(random.uniform(0.3, 0.8))
            h = headers if headers else self.session.headers
            response = self.session.get(url, params=params, headers=h, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Fetch error: {url} — {e}")
            return None

    # ============================================================
    # STEP 1: WEB SEARCH (Bing — working approach from debug files)
    # ============================================================
    def step_1_web_search(self):
        self.log("=" * 50)
        self.log("STEP 1: Web Search (Bing)")
        self.log("=" * 50)

        queries = [
            (self.name, "Full name"),
            (self.emails[0], "Primary email"),
            (self.emails[1], "Secondary email"),
            (self.phones[0], "Primary phone"),
            (self.phones[1], "Secondary phone"),
            (self.pan, "PAN card"),
            (self.ig_handle, "Instagram handle"),
            (f"{self.name} {self.data['addresses']['aadhaar_address'].split(',')[0]}", "Name + Village"),
            (f"{self.name} East Godavari", "Name + District"),
        ]

        for query, source in queries:
            self.log(f"Searching: {source}")
            try:
                # Bing search
                r = self.session.get(
                    "https://www.bing.com/search",
                    params={"q": query, "count": 10},
                    timeout=15
                )
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    results = []
                    for li in soup.select("li.b_algo"):
                        h2 = li.find("h2")
                        if h2:
                            a = h2.find("a")
                            if a:
                                href = a.get("href", "")
                                title = a.get_text(strip=True)
                                snippet_el = li.find("p") or li.find("div", class_="b_caption")
                                snippet = snippet_el.get_text(strip=True)[:200] if snippet_el else ""
                                if href and title:
                                    results.append({"title": title, "url": href, "snippet": snippet})

                    if results:
                        self.R["web_search_results"].append({
                            "query": query,
                            "source": source,
                            "results": results[:5]
                        })
                        self.log(f"  -> {len(results)} results")
            except Exception as e:
                self.log(f"  Error: {e}")

    # ============================================================
    # STEP 2: HaveIBeenPwned Breach Check
    # ============================================================
    def step_2_hibp_check(self):
        self.log("=" * 50)
        self.log("STEP 2: HaveIBeenPwned Breach Check")
        self.log("=" * 50)

        for email in self.emails:
            try:
                headers = {
                    "hibp-api-version": "2",
                    "User-Agent": "Master-OSINT-Agent/1.0"
                }
                r = requests.get(
                    f"https://haveibeenpwned.com/api/v2/breachedaccount/{email}",
                    headers=headers,
                    timeout=15
                )
                if r.status_code == 200:
                    breaches = r.json()
                    self.R["breach_data"].append({
                        "email": email,
                        "count": len(breaches),
                        "breaches": [{"name": b.get("Name"), "domain": b.get("Domain"),
                                      "date": b.get("BreachDate"), "description": b.get("Description","")[:100]}
                                     for b in breaches]
                    })
                    self.log(f"  {email}: {len(breaches)} breaches found!")
                    for b in breaches[:3]:
                        self.log(f"    - {b.get('Name')}")
                elif r.status_code == 404:
                    self.R["email_findings"][email] = {"status": "clean", "breach_count": 0}
                    self.log(f"  {email}: No breaches")
                else:
                    self.R["email_findings"][email] = {"status": f"HTTP {r.status_code}"}
                    self.log(f"  {email}: HTTP {r.status_code}")
            except Exception as e:
                self.R["email_findings"][email] = {"status": "error", "error": str(e)}
                self.log(f"  {email}: Error — {e}")

    # ============================================================
    # STEP 3: Phone Number Analysis
    # ============================================================
    def step_3_phone_analysis(self):
        self.log("=" * 50)
        self.log("STEP 3: Phone Number Analysis")
        self.log("=" * 50)

        for phone in self.phones:
            findings = {}
            # WhatsApp
            try:
                r = self.session.get(f"https://wa.me/+91{phone}", timeout=10, allow_redirects=True)
                findings["WhatsApp"] = {"exists": r.status_code == 200, "url": f"https://wa.me/+91{phone}"}
            except:
                findings["WhatsApp"] = {"exists": False}

            # Truecaller search page
            try:
                r = self.session.get(f"https://www.truecaller.com/search/in/{phone}", timeout=10)
                findings["Truecaller"] = {"exists": r.status_code == 200, "url": f"https://www.truecaller.com/search/in/{phone}"}
            except:
                findings["Truecaller"] = {"exists": False}

            # OSINT.industries
            try:
                r = self.session.get(f"https://osint.industries/api/phone/{phone}", timeout=10)
                if r.status_code == 200:
                    findings["OSINTIndustries"] = r.json()
            except:
                pass

            self.R["phone_findings"][phone] = findings
            self.log(f"  +91{phone}: WhatsApp={findings.get('WhatsApp',{}).get('exists')}, Truecaller={findings.get('Truecaller',{}).get('exists')}")

    # ============================================================
    # STEP 4: Username Enumeration (across platforms)
    # ============================================================
    def step_4_username_enumeration(self):
        self.log("=" * 50)
        self.log("STEP 4: Username Enumeration")
        self.log("=" * 50)

        platforms = [
            ("Instagram", f"https://instagram.com/{self.ig_handle}"),
            ("Twitter/X", f"https://twitter.com/{self.ig_handle}"),
            ("Facebook", f"https://facebook.com/{self.ig_handle}"),
            ("LinkedIn", f"https://linkedin.com/in/{self.ig_handle}"),
            ("Reddit", f"https://reddit.com/user/{self.ig_handle}"),
            ("TikTok", f"https://tiktok.com/@{self.ig_handle}"),
            ("Pinterest", f"https://pinterest.com/{self.ig_handle}"),
            ("YouTube", f"https://youtube.com/@{self.ig_handle}"),
            ("GitHub", f"https://github.com/{self.ig_handle}"),
            ("Twitch", f"https://twitch.tv/{self.ig_handle}"),
            ("Spotify", f"https://open.spotify.com/user/{self.ig_handle}"),
            ("Snapchat", f"https://snapchat.com/add/{self.ig_handle}"),
            ("Telegram", f"https://t.me/{self.ig_handle}"),
            ("Discord", f"https://discord.com/users/{self.ig_handle}"),
            ("Steam", f"https://steamcommunity.com/id/{self.ig_handle}"),
            ("Roblox", f"https://roblox.com/users/{self.ig_handle}/profile"),
            ("Tinder", f"https://tinder.com/@{self.ig_handle}"),
            ("Fansly", f"https://fansly.com/{self.ig_handle}"),
            ("Gumroad", f"https://gumroad.com/{self.ig_handle}"),
            ("Ko-fi", f"https://ko-fi.com/{self.ig_handle}"),
            ("Substack", f"https://substack.com/@{self.ig_handle}"),
            ("Medium", f"https://medium.com/@{self.ig_handle}"),
            ("DeviantArt", f"https://deviantart.com/{self.ig_handle}"),
            ("Behance", f"https://behance.net/{self.ig_handle}"),
            ("Dribbble", f"https://dribbble.com/{self.ig_handle}"),
            ("About.me", f"https://about.me/{self.ig_handle}"),
            ("Linktree", f"https://linktr.ee/{self.ig_handle}"),
            ("OnlyFinder", f"https://onlyfinder.com/{self.ig_handle}"),
        ]

        found_count = 0
        for platform, url in platforms:
            try:
                r = self.session.get(url, timeout=10, allow_redirects=True)
                exists = r.status_code == 200
                if exists:
                    found_count += 1
                    # Try to extract profile info
                    soup = BeautifulSoup(r.text, "html.parser")
                    title = soup.title.get_text(strip=True)[:80] if soup.title else ""
                    self.R["username_availability"][platform] = {
                        "url": url, "exists": True, "status_code": r.status_code,
                        "title": title
                    }
                    self.log(f"  [FOUND] {platform}: {url}")
                else:
                    self.R["username_availability"][platform] = {
                        "url": url, "exists": False, "status_code": r.status_code
                    }
            except Exception as e:
                self.R["username_availability"][platform] = {
                    "url": url, "exists": False, "error": str(e)
                }

        self.log(f"  Total profiles found: {found_count}")

    # ============================================================
    # STEP 5: Social Media Content Scraper (Instagram profile page)
    # ============================================================
    def step_5_social_media_content(self):
        self.log("=" * 50)
        self.log("STEP 5: Social Media Content Scraping")
        self.log("=" * 50)

        platforms_to_scrape = [
            ("Instagram", f"https://www.instagram.com/{self.ig_handle}/"),
            ("Reddit", f"https://www.reddit.com/user/{self.ig_handle}/about.json"),
            ("TikTok", f"https://www.tiktok.com/@{self.ig_handle}"),
        ]

        for platform, url in platforms_to_scrape:
            try:
                r = self.session.get(url, timeout=15)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    meta_desc = ""
                    og_desc = soup.find("meta", property="og:description")
                    if og_desc:
                        meta_desc = og_desc.get("content", "")[:200]
                    og_image = soup.find("meta", property="og:image")
                    profile_img = og_image.get("content", "") if og_image else ""

                    self.R["social_media_content"][platform] = {
                        "url": url,
                        "status": "found",
                        "description": meta_desc,
                        "profile_image": profile_img
                    }
                    self.log(f"  {platform}: scraped OK")
            except Exception as e:
                self.R["social_media_content"][platform] = {"url": url, "status": "error", "error": str(e)}

    # ============================================================
    # STEP 6: Google Dorking
    # ============================================================
    def step_6_google_dorking(self):
        self.log("=" * 50)
        self.log("STEP 6: Google Dorking")
        self.log("=" * 50)

        dorks = [
            (f'site:instagram.com "{self.name}"', "Instagram mentions"),
            (f'site:facebook.com "{self.name}" "{self.data["addresses"]["aadhaar_address"].split(",")[0]}"', "Facebook + address"),
            (f'intext:"{self.emails[0]}"', "Email in text"),
            (f'intext:"{self.phones[0]}"', "Phone in text"),
            (f'intext:"{self.pan}"', "PAN card in text"),
            (f'intext:"{self.data["ids"]["aadhaar_partial"].split()[0]}"', "Aadhaar partial"),
            (f'"{self.name}" "East Godavari"', "Name + district"),
            (f'"{self.name}" filetype:pdf', "PDF documents"),
            (f'"{self.name}" filetype:doc OR filetype:docx', "Word documents"),
        ]

        for dork, source in dorks:
            try:
                r = self.session.get(
                    "https://www.google.com/search",
                    params={"q": dork, "num": 5},
                    timeout=15
                )
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    results = []
                    for g in soup.select("div.g"):
                        a = g.find("a", href=True)
                        h3 = g.find("h3")
                        if a and h3:
                            href = a["href"]
                            title = h3.get_text(strip=True)
                            if href.startswith("/url?q="):
                                href = href.split("/url?q=")[1].split("&")[0]
                            results.append({"title": title, "url": href})

                    if results:
                        self.R["google_dorking"][source] = {
                            "dork": dork,
                            "results": results
                        }
                        self.log(f"  {source}: {len(results)} results")
            except Exception as e:
                self.log(f"  {source}: Error — {e}")

    # ============================================================
    # STEP 7: Domain Search
    # ============================================================
    def step_7_domain_search(self):
        self.log("=" * 50)
        self.log("STEP 7: Domain Search")
        self.log("=" * 50)

        # Name-based domains
        names = self.name.lower().replace(" ", "").split()
        for n in names[:3]:
            domain = f"{n}.com"
            try:
                r = self.session.get(f"https://{domain}", timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                title = soup.title.get_text(strip=True)[:80] if soup.title else ""
                self.R["domain_search"].append({
                    "domain": domain,
                    "status": "active" if r.status_code == 200 else f"HTTP {r.status_code}",
                    "status_code": r.status_code,
                    "title": title
                })
                self.log(f"  {domain}: {r.status_code}")
            except:
                self.R["domain_search"].append({"domain": domain, "status": "unreachable"})

    # ============================================================
    # STEP 8: Content Platforms (OnlyFans, Fansly, etc.)
    # ============================================================
    def step_8_content_platforms(self):
        self.log("=" * 50)
        self.log("STEP 8: Content Platform Check")
        self.log("=" * 50)

        platforms = [
            ("OnlyFinder", f"https://onlyfinder.com/{self.ig_handle}"),
            ("Fansly", f"https://fansly.com/{self.ig_handle}"),
            ("Gumroad", f"https://gumroad.com/{self.ig_handle}"),
            ("Ko-fi", f"https://ko-fi.com/{self.ig_handle}"),
            ("Substack", f"https://substack.com/@{self.ig_handle}"),
            ("Fanvue", f"https://fanvue.com/{self.ig_handle}"),
            ("ManyVids", f"https://manyvids.com/Profile/{self.ig_handle}"),
        ]

        for name, url in platforms:
            try:
                r = self.session.get(url, timeout=10)
                exists = r.status_code == 200
                self.R["content_platform_status"][name] = {
                    "url": url, "exists": exists, "status_code": r.status_code
                }
                if exists:
                    self.log(f"  [FOUND] {name}: {url}")
            except Exception as e:
                self.R["content_platform_status"][name] = {"url": url, "exists": False, "error": str(e)}

    # ============================================================
    # STEP 9: Dark Web / Doxbin Search
    # ============================================================
    def step_9_dark_web(self):
        self.log("=" * 50)
        self.log("STEP 9: Dark Web / Doxbin Search")
        self.log("=" * 50)

        targets = [self.name, self.pan] + self.phones
        for target in targets:
            try:
                url = f"https://www.doxbin.com/search?q={quote(target)}"
                r = self.session.get(url, timeout=15)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        title = link.get_text(strip=True)
                        if target.lower() in href.lower() or target.lower() in title.lower():
                            full_url = href if href.startswith("http") else f"https://www.doxbin.com{href}"
                            if not any(l.get("url") == full_url for l in self.R["dark_web_leaks"]):
                                self.R["dark_web_leaks"].append({
                                    "source": "Doxbin", "title": title or "Unnamed",
                                    "url": full_url, "matched_keyword": target
                                })
                                self.log(f"  Found: {full_url}")
            except Exception as e:
                self.log(f"  Doxbin error: {e}")

        # Telegram channel candidates
        candidates = [
            f"@{self.name.replace(' ', '_').lower()}_leaks",
            f"@{self.name.replace(' ', '').lower()}_nudes",
            "@indian_nudes_leaks", "@desi_leak_central",
            "@south_indian_leaks", "@telugu_leaks"
        ]
        for ch in candidates:
            self.R["telegram_candidates"].append({"channel": ch, "status": "manual check required"})

    # ============================================================
    # STEP 10: Family Search
    # ============================================================
    def step_10_family_search(self):
        self.log("=" * 50)
        self.log("STEP 10: Family Member Search")
        self.log("=" * 50)

        family = self.data["family"]
        for role, member in family.items():
            try:
                r = self.session.get(
                    "https://www.bing.com/search",
                    params={"q": f'"{member}"', "count": 5},
                    timeout=15
                )
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    results = []
                    for li in soup.select("li.b_algo"):
                        a = li.find("a")
                        h2 = li.find("h2")
                        if a and h2:
                            results.append({"title": h2.get_text(strip=True), "url": a.get("href","")})
                    if results:
                        self.R["family_search"][role] = {
                            "name": member, "results": results[:3]
                        }
                        self.log(f"  {role} ({member}): {len(results)} results")
            except Exception as e:
                self.log(f"  {role}: Error — {e}")

    # ============================================================
    # STEP 11: Address Geolocation Search
    # ============================================================
    def step_11_address_search(self):
        self.log("=" * 50)
        self.log("STEP 11: Address Geolocation")
        self.log("=" * 50)

        address = self.data["addresses"]["aadhaar_address"]
        pin = "507121"
        searches = [
            (f"\"{pin}\" {self.name}", "PIN Code"),
            (f"\"{address.split(',')[0]}\" {self.name}", "Village"),
            (f"\"{self.name}\" \"East Godavari\"", "District"),
            (f"\"{self.name}\" \"Jaggavaram\"", "Village exact"),
            (f"\"Kunavaram\" {self.name}", "Mandal"),
        ]

        for query, source in searches:
            try:
                r = self.session.get(
                    "https://www.bing.com/search",
                    params={"q": query, "count": 5},
                    timeout=15
                )
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    results = []
                    for li in soup.select("li.b_algo"):
                        a = li.find("a")
                        h2 = li.find("h2")
                        if a and h2:
                            results.append({"title": h2.get_text(strip=True), "url": a.get("href","")})
                    if results:
                        self.R["address_search"].append({
                            "query": query, "source": source, "results": results[:3]
                        })
                        self.log(f"  {source}: {len(results)} results")
            except Exception as e:
                self.log(f"  {source}: Error — {e}")

    # ============================================================
    # STEP 12: PAN / ID Checks
    # ============================================================
    def step_12_pan_check(self):
        self.log("=" * 50)
        self.log("STEP 12: PAN / ID Checks")
        self.log("=" * 50)

        try:
            r = self.session.get(
                "https://www.bing.com/search",
                params={"q": f'"{self.pan}"', "count": 5},
                timeout=15
            )
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                results = []
                for li in soup.select("li.b_algo"):
                    a = li.find("a")
                    h2 = li.find("h2")
                    if a and h2:
                        results.append({"title": h2.get_text(strip=True), "url": a.get("href","")})
                self.R["pan_findings"] = {
                    "pan": self.pan, "results": results
                }
                self.log(f"  PAN {self.pan}: {len(results)} results")
        except Exception as e:
            self.log(f"  PAN error: {e}")

    # ============================================================
    # STEP 13: Discord Server Finder
    # ============================================================
    def step_13_discord_search(self):
        self.log("=" * 50)
        self.log("STEP 13: Discord Server Search")
        self.log("=" * 50)

        try:
            r = self.session.get(
                "https://disboard.org/api/servers/search",
                params={"search": "Indian Leaks", "limit": "5", "lang": "en"},
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                for server in data.get("servers", [])[:3]:
                    self.R["discord_servers"].append({
                        "name": server.get("name"),
                        "members": server.get("memberCount"),
                        "invite": server.get("inviteUrl")
                    })
                self.log(f"  Found {len(self.R['discord_servers'])} servers")
        except Exception as e:
            self.log(f"  Discord error: {e}")

    # ============================================================
    # RUN ALL STEPS
    # ============================================================
    def run(self):
        self.log("=" * 60)
        self.log(f"  MASTER OSINT AGENT")
        self.log(f"  Target: {self.name}")
        self.log(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 60)

        self.step_1_web_search()
        self.step_2_hibp_check()
        self.step_3_phone_analysis()
        self.step_4_username_enumeration()
        self.step_5_social_media_content()
        self.step_6_google_dorking()
        self.step_7_domain_search()
        self.step_8_content_platforms()
        self.step_9_dark_web()
        self.step_10_family_search()
        self.step_11_address_search()
        self.step_12_pan_check()
        self.step_13_discord_search()

        # Build summary
        profiles_found = sum(1 for v in self.R["username_availability"].values() if v.get("exists"))
        content_platforms = sum(1 for v in self.R["content_platform_status"].values() if v.get("exists"))
        web_results = sum(len(w.get("results", [])) for w in self.R["web_search_results"])
        leaks = len(self.R["dark_web_leaks"])

        self.R["summary"] = {
            "target": self.name,
            "scan_time": self.R["scan_time"],
            "web_search_results": web_results,
            "total_breaches": sum(b.get("count", 0) for b in self.R["breach_data"]),
            "social_profiles_found": profiles_found,
            "content_platforms_found": content_platforms,
            "dark_web_leaks": leaks,
            "telegram_candidates": len(self.R["telegram_candidates"]),
            "emails_checked": len(self.emails),
            "phones_checked": len(self.phones),
            "usernames_checked": len(self.usernames),
        }

        self.log("=" * 60)
        self.log("  SCAN COMPLETE")
        for k, v in self.R["summary"].items():
            self.log(f"  {k}: {v}")
        self.log("=" * 60)

        return self.R


# ============================================================
# 3. HTML REPORT GENERATOR
# ============================================================
def generate_html_report(results):
    """Generate a beautiful, dark-themed HTML report with all findings."""

    # Color coding helpers
    status_badge = lambda ok, yes="✅ Active", no="❌ Not found": f'<span class="badge {"badge-ok" if ok else "badge-no"}">{"✅ Active" if ok else "❌ Not found"}</span>'

    # Build profile card
    p = results["profile"]
    profile_html = f"""
    <div class="profile-card">
      <div class="profile-header">
        <div class="profile-avatar">{p['name'][0]}</div>
        <div class="profile-info">
          <h2>{p['name']}</h2>
          <div class="profile-tags">
            <span class="tag">{p['gender']}</span>
            <span class="tag">{p['age']} years</span>
            <span class="tag">{p['community']}</span>
            <span class="tag">{p.get('dob', '')}</span>
          </div>
          <p class="profile-detail">Height: {p['height_cm']}cm · Weight: {p['weight_kg']}kg</p>
          <p class="profile-detail">Marks: {', '.join(p.get('distinctive_marks', []))}</p>
        </div>
      </div>
    </div>
    """

    # Contact card
    c = results["contact"]
    contact_html = f"""
    <div class="card">
      <h3><span class="card-icon">📞</span> Contact Information</h3>
      <div class="info-grid">
        <div class="info-item"><label>Phone 1</label><span class="hl">{c['primary_phone']}</span></div>
        <div class="info-item"><label>Phone 2</label><span class="hl">{c['secondary_phone']}</span></div>
        <div class="info-item"><label>Email 1</label><span class="hl">{c['email_primary']}</span></div>
        <div class="info-item"><label>Email 2</label><span class="hl">{c['email_secondary']}</span></div>
        <div class="info-item"><label>Instagram</label><span class="hl">{c['instagram_handle']}</span></div>
      </div>
    </div>
    """

    # Address card
    addr = results["addresses"]
    addr_html = f"""
    <div class="card">
      <h3><span class="card-icon">📍</span> Addresses</h3>
      <div class="info-grid">
        <div class="info-item"><label>Aadhaar Address</label><span>{addr['aadhaar_address']}</span></div>
        <div class="info-item"><label>Insurance Note</label><span>{addr.get('insurance_address_note', '')}</span></div>
      </div>
    </div>
    """

    # IDs card
    ids = results["ids"]
    ids_html = f"""
    <div class="card">
      <h3><span class="card-icon">🆔</span> Identity Documents</h3>
      <div class="info-grid">
        <div class="info-item"><label>Aadhaar</label><span class="hl">{ids['aadhaar_partial']}</span></div>
        <div class="info-item"><label>PAN</label><span class="hl">{ids['pan']}</span></div>
        <div class="info-item"><label>Caste Cert</label><span class="hl">{ids['caste_cert_no']}</span></div>
      </div>
    </div>
    """

    # Family card
    fam = results.get("family", {})
    fam_rows = ""
    for role, name in fam.items():
        fam_rows += f'<div class="info-item"><label>{role.title()}</label><span>{name}</span></div>'
    family_html = f"""
    <div class="card">
      <h3><span class="card-icon">👨‍👩‍👧‍👧</span> Family</h3>
      <div class="info-grid">{fam_rows}</div>
    </div>
    """ if fam_rows else ""

    # Insurance
    ins = results.get("insurance", {})
    ins_html = f"""
    <div class="card">
      <h3><span class="card-icon">🛡️</span> Insurance</h3>
      <div class="info-grid">
        <div class="info-item"><label>Provider</label><span>{ins.get('provider','')}</span></div>
        <div class="info-item"><label>Policy No</label><span class="hl">{ins.get('policy_no','')}</span></div>
        <div class="info-item"><label>Plan</label><span>{ins.get('plan','')}</span></div>
        <div class="info-item"><label>Nominee</label><span>{ins.get('nominee','')}</span></div>
      </div>
    </div>
    """ if ins else ""

    # === SCAN RESULTS ===

    # Summary stats
    s = results["summary"]
    stats_html = f"""
    <div class="stats-row">
      <div class="stat-card"><div class="stat-num">{s.get('social_profiles_found',0)}</div><div class="stat-label">Social Profiles</div></div>
      <div class="stat-card"><div class="stat-num">{s.get('content_platforms_found',0)}</div><div class="stat-label">Content Platforms</div></div>
      <div class="stat-card"><div class="stat-num">{s.get('total_breaches',0)}</div><div class="stat-label">Breaches Found</div></div>
      <div class="stat-card"><div class="stat-num">{s.get('dark_web_leaks',0)}</div><div class="stat-label">Dark Web Leaks</div></div>
      <div class="stat-card"><div class="stat-num">{s.get('web_search_results',0)}</div><div class="stat-label">Web Results</div></div>
      <div class="stat-card"><div class="stat-num">{s.get('telegram_candidates',0)}</div><div class="stat-label">Telegram Leads</div></div>
    </div>
    """

    # Web search results
    web_html = ""
    if results.get("web_search_results"):
        web_html = '<div class="card"><h3><span class="card-icon">🌐</span> Web Search Results</h3>'
        for w in results["web_search_results"]:
            web_html += f'<div class="section-title">{w["source"]}: <code>{w["query"][:60]}</code></div><div class="result-list">'
            for r in w.get("results", []):
                web_html += f'<div class="result-item"><a href="{r["url"]}" target="_blank">{r["title"][:80]}</a><div class="result-url">{r["url"][:80]}</div><div class="result-snippet">{r.get("snippet","")[:150]}</div></div>'
            web_html += '</div>'
        web_html += '</div>'

    # Breach data
    breach_html = ""
    if results.get("breach_data"):
        breach_html = '<div class="card"><h3><span class="card-icon">🔓</span> Breach Data</h3>'
        for b in results["breach_data"]:
            breach_html += f'<div class="section-title">{b["email"]} — {b.get("count",0)} breaches</div><div class="result-list">'
            for br in b.get("breaches", []):
                breach_html += f'<div class="result-item"><strong>{br.get("name","")}</strong> · {br.get("date","")}<br><small>{br.get("description","")[:100]}</small></div>'
            breach_html += '</div>'
        breach_html += '</div>'

    # Email findings
    email_html = ""
    if results.get("email_findings"):
        email_html = '<div class="card"><h3><span class="card-icon">📧</span> Email Check Results</h3><div class="info-grid">'
        for email, status in results["email_findings"].items():
            clean = status.get("status") == "clean"
            badge = f'<span class="badge badge-ok">✅ Clean</span>' if clean else f'<span class="badge badge-no">⚠️ {status.get("status","Unknown")}</span>'
            email_html += f'<div class="info-item"><label>{email}</label>{badge}</div>'
        email_html += '</div></div>'

    # Phone findings
    phone_html = ""
    if results.get("phone_findings"):
        phone_html = '<div class="card"><h3><span class="card-icon">📱</span> Phone Analysis</h3><div class="info-grid">'
        for phone, findings in results["phone_findings"].items():
            wa = findings.get("WhatsApp", {}).get("exists", False)
            tc = findings.get("Truecaller", {}).get("exists", False)
            phone_html += f'<div class="info-item"><label>+91 {phone}</label><span>WhatsApp: {"✅" if wa else "❌"} · Truecaller: {"✅" if tc else "❌"}</span></div>'
        phone_html += '</div></div>'

    # Username availability table
    username_html = ""
    if results.get("username_availability"):
        username_html = '<div class="card"><h3><span class="card-icon">🔍</span> Username Availability ({} profiles found)</h3><div class="table-wrap"><table><thead><tr><th>Platform</th><th>Status</th><th>URL</th></tr></thead><tbody>'.format(s.get("social_profiles_found", 0))
        for plat, info in sorted(results["username_availability"].items()):
            if info.get("exists"):
                username_html += f'<tr><td><strong>{plat}</strong></td><td><span class="badge badge-ok">✅ Found</span></td><td><a href="{info["url"]}" target="_blank">Visit →</a></td></tr>'
        username_html += '</tbody></table></div></div>'

    # Content platforms
    content_html = ""
    if results.get("content_platform_status"):
        content_html = '<div class="card"><h3><span class="card-icon">🔞</span> Content Platforms</h3><div class="table-wrap"><table><thead><tr><th>Platform</th><th>Status</th><th>URL</th></tr></thead><tbody>'
        for plat, info in results["content_platform_status"].items():
            if info.get("exists"):
                content_html += f'<tr><td><strong>{plat}</strong></td><td><span class="badge badge-ok">✅ Active</span></td><td><a href="{info["url"]}" target="_blank">Visit →</a></td></tr>'
        content_html += '</tbody></table></div></div>'

    # Dark web leaks
    dark_html = ""
    if results.get("dark_web_leaks"):
        dark_html = '<div class="card"><h3><span class="card-icon">💀</span> Dark Web / Doxbin Leaks</h3><div class="result-list">'
        for leak in results["dark_web_leaks"]:
            dark_html += f'<div class="result-item"><a href="{leak["url"]}" target="_blank">{leak.get("title","Unnamed")}</a><div class="result-url">{leak["url"]}</div><small>Matched: {leak.get("matched_keyword","")}</small></div>'
        dark_html += '</div></div>'

    # Telegram candidates
    tele_html = ""
    if results.get("telegram_candidates"):
        tele_html = '<div class="card"><h3><span class="card-icon">✈️</span> Telegram Channel Candidates</h3><div class="info-grid">'
        for ch in results["telegram_candidates"]:
            tele_html += f'<div class="info-item"><label>{ch["channel"]}</label><span class="badge badge-no">🔍 Manual check</span></div>'
        tele_html += '</div></div>'

    # Google dorking
    dork_html = ""
    if results.get("google_dorking"):
        dork_html = '<div class="card"><h3><span class="card-icon">🔎</span> Google Dork Results</h3>'
        for source, info in results["google_dorking"].items():
            dork_html += f'<div class="section-title">{source}</div><div class="result-list">'
            for r in info.get("results", []):
                dork_html += f'<div class="result-item"><a href="{r["url"]}" target="_blank">{r["title"][:80]}</a></div>'
            dork_html += '</div>'
        dork_html += '</div>'

    # Domain search
    domain_html = ""
    if results.get("domain_search"):
        domain_html = '<div class="card"><h3><span class="card-icon">🌍</span> Domain Search</h3><div class="info-grid">'
        for d in results["domain_search"]:
            status = d.get("status", "")
            badge = '<span class="badge badge-ok">Active</span>' if "active" in str(status).lower() else '<span class="badge badge-no">Inactive</span>'
            domain_html += f'<div class="info-item"><label>{d["domain"]}</label>{badge} <small>{d.get("title","")[:50]}</small></div>'
        domain_html += '</div></div>'

    # Family search
    fam_search_html = ""
    if results.get("family_search"):
        fam_search_html = '<div class="card"><h3><span class="card-icon">👨‍👩‍👧‍👧</span> Family Search Results</h3>'
        for role, info in results["family_search"].items():
            fam_search_html += f'<div class="section-title">{role.title()}: {info["name"]}</div><div class="result-list">'
            for r in info.get("results", []):
                fam_search_html += f'<div class="result-item"><a href="{r["url"]}" target="_blank">{r["title"][:80]}</a></div>'
            fam_search_html += '</div>'
        fam_search_html += '</div>'

    # Address search
    addr_search_html = ""
    if results.get("address_search"):
        addr_search_html = '<div class="card"><h3><span class="card-icon">📍</span> Address Geolocation Results</h3>'
        for a in results["address_search"]:
            addr_search_html += f'<div class="section-title">{a["source"]}</div><div class="result-list">'
            for r in a.get("results", []):
                addr_search_html += f'<div class="result-item"><a href="{r["url"]}" target="_blank">{r["title"][:80]}</a></div>'
            addr_search_html += '</div>'
        addr_search_html += '</div>'

    # PAN findings
    pan_html = ""
    if results.get("pan_findings") and results["pan_findings"].get("results"):
        pan_html = '<div class="card"><h3><span class="card-icon">🪪</span> PAN Search Results</h3><div class="result-list">'
        for r in results["pan_findings"]["results"]:
            pan_html += f'<div class="result-item"><a href="{r["url"]}" target="_blank">{r["title"][:80]}</a></div>'
        pan_html += '</div></div>'

    # Discord servers
    discord_html = ""
    if results.get("discord_servers"):
        discord_html = '<div class="card"><h3><span class="card-icon">💬</span> Discord Leak Servers</h3><div class="table-wrap"><table><thead><tr><th>Server</th><th>Members</th><th>Invite</th></tr></thead><tbody>'
        for d in results["discord_servers"]:
            discord_html += f'<tr><td>{d.get("name","")}</td><td>{d.get("members","")}</td><td><a href="{d.get("invite","")}" target="_blank">Join</a></td></tr>'
        discord_html += '</tbody></table></div></div>'

    # Social media content
    social_html = ""
    if results.get("social_media_content"):
        social_html = '<div class="card"><h3><span class="card-icon">📸</span> Social Media Profile Data</h3><div class="info-grid">'
        for plat, info in results["social_media_content"].items():
            if info.get("profile_image"):
                social_html += f'<div class="info-item"><label>{plat}</label><img src="{info["profile_image"]}" class="profile-thumb" alt="{plat} profile"><br><small>{info.get("description","")[:100]}</small></div>'
            else:
                social_html += f'<div class="info-item"><label>{plat}</label><span>{info.get("description","")[:100] or "Profile found"}</span></div>'
        social_html += '</div></div>'

    # === FULL HTML ===
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OSINT Report — {results['target']}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
  header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 30px; border-radius: 16px; margin-bottom: 30px; text-align: center; border: 1px solid #1e3a5f; }}
  header h1 {{ font-size: 2.2em; background: linear-gradient(90deg, #00d4ff, #7b2ff7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  header .subtitle {{ color: #8892b0; margin-top: 8px; font-size: 0.95em; }}
  header .target-name {{ font-size: 1.4em; color: #ccd6f6; margin-top: 5px; }}

  .profile-card {{ background: linear-gradient(135deg, #1e1e3a, #2a1a3e); border-radius: 16px; padding: 25px; margin-bottom: 20px; border: 1px solid #333366; }}
  .profile-header {{ display: flex; align-items: center; gap: 20px; }}
  .profile-avatar {{ width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #00d4ff, #7b2ff7); display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: bold; color: white; flex-shrink: 0; }}
  .profile-info h2 {{ font-size: 1.6em; color: #fff; }}
  .profile-tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }}
  .tag {{ background: #1a3a5a; color: #88ccff; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; }}
  .profile-detail {{ color: #8892b0; font-size: 0.9em; margin-top: 4px; }}
  .profile-thumb {{ width: 48px; height: 48px; border-radius: 8px; object-fit: cover; }}

  .card {{ background: #13131f; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #1e1e30; }}
  .card h3 {{ color: #ccd6f6; font-size: 1.15em; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }}
  .card-icon {{ font-size: 1.2em; }}
  .info-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
  .info-item {{ background: #1a1a2e; padding: 10px 14px; border-radius: 8px; }}
  .info-item label {{ display: block; font-size: 0.75em; color: #8892b0; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
  .info-item span {{ color: #e0e0e0; word-break: break-all; }}
  .hl {{ color: #64ffda; font-weight: 600; font-family: 'Courier New', monospace; }}

  .stats-row {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }}
  .stat-card {{ background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #1e3a5f; border-radius: 12px; padding: 18px; text-align: center; }}
  .stat-num {{ font-size: 2em; font-weight: bold; color: #64ffda; }}
  .stat-label {{ font-size: 0.75em; color: #8892b0; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}

  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #1a1a2e; color: #8892b0; padding: 10px 12px; text-align: left; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #2a2a3e; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #1a1a2e; }}
  tr:hover td {{ background: #1a1a2e; }}

  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 10px; font-size: 0.78em; font-weight: 600; }}
  .badge-ok {{ background: #0a2a1a; color: #64ffda; }}
  .badge-no {{ background: #2a0a0a; color: #ff6b6b; }}

  .section-title {{ color: #8892b0; font-size: 0.85em; margin: 10px 0 6px; }}
  .result-list {{ margin-bottom: 10px; }}
  .result-item {{ background: #1a1a2e; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; }}
  .result-item a {{ color: #64ffda; text-decoration: none; font-size: 0.9em; }}
  .result-item a:hover {{ text-decoration: underline; color: #00d4ff; }}
  .result-url {{ color: #555; font-size: 0.75em; word-break: break-all; }}
  .result-snippet {{ color: #8892b0; font-size: 0.8em; margin-top: 2px; }}

  footer {{ text-align: center; color: #555; padding: 30px 0; font-size: 0.85em; }}

  @media (max-width: 600px) {{
    .profile-header {{ flex-direction: column; text-align: center; }}
    .info-grid {{ grid-template-columns: 1fr; }}
    .stats-row {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🔍 OSINT Intelligence Report</h1>
    <div class="target-name">{results['target']}</div>
    <div class="subtitle">Scan completed: {results['scan_time']} · Master OSINT Agent v3.0</div>
  </header>

  {profile_html}
  {stats_html}

  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:20px;">
    {contact_html}
    {addr_html}
    {ids_html}
    {family_html}
    {ins_html}
  </div>

  {email_html}
  {phone_html}
  {breach_html}
  {web_html}
  {username_html}
  {content_html}
  {dark_html}
  {tele_html}
  {dork_html}
  {domain_html}
  {social_html}
  {fam_search_html}
  {addr_search_html}
  {pan_html}
  {discord_html}

  <footer>
    <p>Master OSINT Agent · Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p style="margin-top:4px;font-size:0.75em;color:#333;">Data collected from public sources. Verify before acting.</p>
  </footer>
</div>
</body>
</html>"""

    return html


# ============================================================
# 4. MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  MASTER OSINT AGENT v3.0")
    print("  Combines all working project code into one script")
    print("  Generates: HTML report + JSON data")
    print("=" * 60)

    # Run the scan
    agent = MasterOSINTAgent()
    results = agent.run()

    # Save JSON
    json_file = f"osint_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[+] JSON saved: {json_file}")

    # Generate and save HTML
    html = generate_html_report(results)
    html_file = f"osint_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] HTML report saved: {html_file}")

    # Also save as osint_report.html (latest)
    with open("osint_report.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Latest HTML: osint_report.html")

    print(f"\n{'='*60}")
    print(f"  DONE — Open osint_report.html in a browser")
    print(f"{'='*60}")