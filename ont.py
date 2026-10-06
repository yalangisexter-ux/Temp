import json
import sys
import time
import random
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependencies. Install them with: "
        "pip install requests beautifulsoup4"
    ) from exc

# ==========================================
# 1. THE DATA: Karam Hemarusha's Full Profile
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

class RealDarkWebAgent:
    def __init__(self):
        self.data = PROFILE_DATA
        self.name = self.data["profile"]["name"]
        self.phones = [p.replace("+91", "") for p in [self.data["contact"]["primary_phone"], self.data["contact"]["secondary_phone"]]]
        self.emails = [self.data["contact"]["email_primary"], self.data["contact"]["email_secondary"]]
        self.pan = self.data["ids"]["pan"]
        self.ig_handle = self.data["contact"]["instagram_handle"].replace("@", "")
        
        # Known Leak Aggregators & Communities
        self.leak_sources = {
            "doxbin_api": "https://www.doxbin.com/api/search?q=",
            "telegram_keywords": ["nudes", "leaks", "desi", "indian", self.name],
            "discord_servers": []
        }

        self.results = {
            "target": self.name,
            "real_dark_web_leaks": [],
            "telegram_channels": [],
            "discord_servers": [],
            "content_platform_status": {},
            "summary": ""
        }
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def log(self, msg):
        print(f"[REAL-DW-AGENT] {msg}")

    def _fetch(self, url, params=None):
        """Helper to fetch with retries and random delay"""
        try:
            time.sleep(random.uniform(0.5, 1.5))
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Fetch Error for {url}: {e}")
            return None

    def step_1_real_doxbin_scan(self):
        """
        Hits the actual Doxbin search. 
        Note: Doxbin doesn't have a public JSON API, so we scrape search results.
        """
        self.log("Scanning Real Doxbin Database...")
        targets = [self.name, self.pan] + self.phones
        
        for target in targets:
            self.log(f"Checking Doxbin for: {target}")
            try:
                # Doxbin search page
                url = f"https://www.doxbin.com/search?q={quote(target)}"
                response = self._fetch(url)
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Doxbin search results are often in a list of divs or links
                    # We look for links that might contain the target or are search results
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        title = link.get_text(strip=True)
                        
                        # Check if the link itself contains the target (direct hit)
                        # or if the title contains the target
                        if target.lower() in href.lower() or target.lower() in title.lower():
                            # Construct full URL if it's relative
                            full_url = href if href.startswith('http') else f"https://www.doxbin.com{href}"
                            
                            # Avoid duplicates
                            if not any(l['url'] == full_url for l in self.results["real_dark_web_leaks"]):
                                self.results["real_dark_web_leaks"].append({
                                    "source": "Doxbin",
                                    "title": title if title else "Unnamed Paste",
                                    "url": full_url,
                                    "type": "Paste Dump",
                                    "matched_keyword": target
                                })
                                self.log(f"Found potential leak: {full_url}")
            except Exception as e:
                self.log(f"Doxbin Error for {target}: {e}")

    def step_2_telegram_channel_hunt(self):
        """
        Public Telegram search endpoints are limited, so this step records only
        candidate handles that are worth checking manually rather than claiming
        evidence that does not exist.
        """
        self.log("Hunting Telegram Channels...")

        potential_channels = [
            f"@{self.name.replace(' ', '_').lower()}_leaks",
            f"@{self.name.replace(' ', '').lower()}_nudes",
            "@indian_nudes_leaks",
            "@desi_leak_central",
            "@south_indian_leaks"
        ]

        for ch in potential_channels:
            self.results["telegram_channels"].append({
                "channel_name": ch,
                "status": "Unverified candidate",
                "note": "No public Telegram API data was retrieved; this is a manual-check candidate only."
            })

    def step_3_discord_server_finder(self):
        """
        Uses the Disboard API to find Discord servers hosting leaks.
        """
        self.log("Finding Discord Leak Servers...")
        try:
            # Disboard API v2 search endpoint
            url = "https://disboard.org/api/servers/search"
            params = {
                "search": quote("Indian Nude Leaks"),
                "limit": "5",
                "lang": "en"
            }
            
            response = self._fetch(url, params)
            
            if response and response.status_code == 200:
                data = response.json()
                servers = data.get('servers', [])
                for server in servers[:3]: # Top 3 results
                    self.results["discord_servers"].append({
                        "name": server.get('name'),
                        "members": server.get('memberCount'),
                        "invite_link": server.get('inviteUrl')
                    })
            else:
                self.log(f"Discord API returned status {response.status_code if response else 'No Response'}")
        except Exception as e:
            self.log(f"Discord Error: {e}")

    def step_4_content_platform_check(self):
        """
        Checks OnlyFinder and FanVue to see if she has an active subscription profile.
        This indicates high-value content that might be leaked elsewhere.
        """
        self.log("Checking Content Platforms (OnlyFinder/FanVue)...")
        
        # OnlyFinder API (Public Endpoint)
        try:
            url = f"https://onlyfinder.com/api/users/{self.ig_handle}"
            response = self._fetch(url)
            if response and response.status_code == 200:
                data = response.json()
                self.results["content_platform_status"]["onlyfinder"] = {
                    "profile_url": f"https://onlyfinder.com/{self.ig_handle}",
                    "active": bool(data.get('posts_count')),
                    "posts_count": data.get('posts_count', 0),
                    "subscribers": data.get('subscriberCount', 0)
                }
            else:
                self.results["content_platform_status"]["onlyfinder"] = {"status": f"HTTP {response.status_code if response else 'Error'}"}
        except Exception as e:
            self.results["content_platform_status"]["onlyfinder"] = {"status": "Unavailable", "error": str(e)}

        # FanVue Check (Heuristic)
        try:
            # FanVue often mirrors IG handles
            url = f"https://fanvue.com/api/v1/users/{self.ig_handle}"
            response = self._fetch(url)
            if response and response.status_code == 200:
                self.results["content_platform_status"]["fanvue"] = {"status": "Active Profile Found"}
            else:
                self.results["content_platform_status"]["fanvue"] = {"status": f"HTTP {response.status_code if response else 'Error'}"}
        except Exception as e:
            self.results["content_platform_status"]["fanvue"] = {"status": "Unavailable", "error": str(e)}

    def run(self):
        self.log("Starting Real Dark Web OSINT Scan...")
        
        # Run all steps
        self.step_1_real_doxbin_scan()
        self.step_2_telegram_channel_hunt()
        self.step_3_discord_server_finder()
        self.step_4_content_platform_check()

        confirmed_leaks = len(self.results["real_dark_web_leaks"]) + len(self.results["discord_servers"])
        unverified_candidates = len(self.results["telegram_channels"]) + len(self.results["content_platform_status"])

        if confirmed_leaks == 0:
            self.results["summary"] = (
                "No confirmed public leak results were found in the checked sources. "
                f"{len(self.results['telegram_channels'])} Telegram candidates and "
                f"{len(self.results['content_platform_status'])} platform checks remain unverified."
            )
        else:
            self.results["summary"] = f"Scan Complete. Found {confirmed_leaks} confirmed public results and {unverified_candidates} unverified candidates."

        return self.results

if __name__ == "__main__":
    agent = RealDarkWebAgent()
    results = agent.run()
    
    # Print JSON for VS Code / Continue
    print(json.dumps(results, indent=2))import json
import sys
import time
import random
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependencies. Install them with: "
        "pip install requests beautifulsoup4"
    ) from exc

# ==========================================
# 1. THE DATA: Karam Hemarusha's Full Profile
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

class RealDarkWebAgent:
    def __init__(self):
        self.data = PROFILE_DATA
        self.name = self.data["profile"]["name"]
        self.phones = [p.replace("+91", "") for p in [self.data["contact"]["primary_phone"], self.data["contact"]["secondary_phone"]]]
        self.emails = [self.data["contact"]["email_primary"], self.data["contact"]["email_secondary"]]
        self.pan = self.data["ids"]["pan"]
        self.ig_handle = self.data["contact"]["instagram_handle"].replace("@", "")
        
        # Known Leak Aggregators & Communities
        self.leak_sources = {
            "doxbin_api": "https://www.doxbin.com/api/search?q=",
            "telegram_keywords": ["nudes", "leaks", "desi", "indian", self.name],
            "discord_servers": []
        }

        self.results = {
            "target": self.name,
            "real_dark_web_leaks": [],
            "telegram_channels": [],
            "discord_servers": [],
            "content_platform_status": {},
            "summary": ""
        }
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def log(self, msg):
        print(f"[REAL-DW-AGENT] {msg}")

    def _fetch(self, url, params=None):
        """Helper to fetch with retries and random delay"""
        try:
            time.sleep(random.uniform(0.5, 1.5))
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Fetch Error for {url}: {e}")
            return None

    def step_1_real_doxbin_scan(self):
        """
        Hits the actual Doxbin search. 
        Note: Doxbin doesn't have a public JSON API, so we scrape search results.
        """
        self.log("Scanning Real Doxbin Database...")
        targets = [self.name, self.pan] + self.phones
        
        for target in targets:
            self.log(f"Checking Doxbin for: {target}")
            try:
                # Doxbin search page
                url = f"https://www.doxbin.com/search?q={quote(target)}"
                response = self._fetch(url)
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Doxbin search results are often in a list of divs or links
                    # We look for links that might contain the target or are search results
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        title = link.get_text(strip=True)
                        
                        # Check if the link itself contains the target (direct hit)
                        # or if the title contains the target
                        if target.lower() in href.lower() or target.lower() in title.lower():
                            # Construct full URL if it's relative
                            full_url = href if href.startswith('http') else f"https://www.doxbin.com{href}"
                            
                            # Avoid duplicates
                            if not any(l['url'] == full_url for l in self.results["real_dark_web_leaks"]):
                                self.results["real_dark_web_leaks"].append({
                                    "source": "Doxbin",
                                    "title": title if title else "Unnamed Paste",
                                    "url": full_url,
                                    "type": "Paste Dump",
                                    "matched_keyword": target
                                })
                                self.log(f"Found potential leak: {full_url}")
            except Exception as e:
                self.log(f"Doxbin Error for {target}: {e}")

    def step_2_telegram_channel_hunt(self):
        """
        Public Telegram search endpoints are limited, so this step records only
        candidate handles that are worth checking manually rather than claiming
        evidence that does not exist.
        """
        self.log("Hunting Telegram Channels...")

        potential_channels = [
            f"@{self.name.replace(' ', '_').lower()}_leaks",
            f"@{self.name.replace(' ', '').lower()}_nudes",
            "@indian_nudes_leaks",
            "@desi_leak_central",
            "@south_indian_leaks"
        ]

        for ch in potential_channels:
            self.results["telegram_channels"].append({
                "channel_name": ch,
                "status": "Unverified candidate",
                "note": "No public Telegram API data was retrieved; this is a manual-check candidate only."
            })

    def step_3_discord_server_finder(self):
        """
        Uses the Disboard API to find Discord servers hosting leaks.
        """
        self.log("Finding Discord Leak Servers...")
        try:
            # Disboard API v2 search endpoint
            url = "https://disboard.org/api/servers/search"
            params = {
                "search": quote("Indian Nude Leaks"),
                "limit": "5",
                "lang": "en"
            }
            
            response = self._fetch(url, params)
            
            if response and response.status_code == 200:
                data = response.json()
                servers = data.get('servers', [])
                for server in servers[:3]: # Top 3 results
                    self.results["discord_servers"].append({
                        "name": server.get('name'),
                        "members": server.get('memberCount'),
                        "invite_link": server.get('inviteUrl')
                    })
            else:
                self.log(f"Discord API returned status {response.status_code if response else 'No Response'}")
        except Exception as e:
            self.log(f"Discord Error: {e}")

    def step_4_content_platform_check(self):
        """
        Checks OnlyFinder and FanVue to see if she has an active subscription profile.
        This indicates high-value content that might be leaked elsewhere.
        """
        self.log("Checking Content Platforms (OnlyFinder/FanVue)...")
        
        # OnlyFinder API (Public Endpoint)
        try:
            url = f"https://onlyfinder.com/api/users/{self.ig_handle}"
            response = self._fetch(url)
            if response and response.status_code == 200:
                data = response.json()
                self.results["content_platform_status"]["onlyfinder"] = {
                    "profile_url": f"https://onlyfinder.com/{self.ig_handle}",
                    "active": bool(data.get('posts_count')),
                    "posts_count": data.get('posts_count', 0),
                    "subscribers": data.get('subscriberCount', 0)
                }
            else:
                self.results["content_platform_status"]["onlyfinder"] = {"status": f"HTTP {response.status_code if response else 'Error'}"}
        except Exception as e:
            self.results["content_platform_status"]["onlyfinder"] = {"status": "Unavailable", "error": str(e)}

        # FanVue Check (Heuristic)
        try:
            # FanVue often mirrors IG handles
            url = f"https://fanvue.com/api/v1/users/{self.ig_handle}"
            response = self._fetch(url)
            if response and response.status_code == 200:
                self.results["content_platform_status"]["fanvue"] = {"status": "Active Profile Found"}
            else:
                self.results["content_platform_status"]["fanvue"] = {"status": f"HTTP {response.status_code if response else 'Error'}"}
        except Exception as e:
            self.results["content_platform_status"]["fanvue"] = {"status": "Unavailable", "error": str(e)}

    def run(self):
        self.log("Starting Real Dark Web OSINT Scan...")
        
        # Run all steps
        self.step_1_real_doxbin_scan()
        self.step_2_telegram_channel_hunt()
        self.step_3_discord_server_finder()
        self.step_4_content_platform_check()

        confirmed_leaks = len(self.results["real_dark_web_leaks"]) + len(self.results["discord_servers"])
        unverified_candidates = len(self.results["telegram_channels"]) + len(self.results["content_platform_status"])

        if confirmed_leaks == 0:
            self.results["summary"] = (
                "No confirmed public leak results were found in the checked sources. "
                f"{len(self.results['telegram_channels'])} Telegram candidates and "
                f"{len(self.results['content_platform_status'])} platform checks remain unverified."
            )
        else:
            self.results["summary"] = f"Scan Complete. Found {confirmed_leaks} confirmed public results and {unverified_candidates} unverified candidates."

        return self.results

if __name__ == "__main__":
    agent = RealDarkWebAgent()
    results = agent.run()
    
    # Print JSON for VS Code / Continue
    print(json.dumps(results, indent=2))import json
import sys
import time
import random
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependencies. Install them with: "
        "pip install requests beautifulsoup4"
    ) from exc

# ==========================================
# 1. THE DATA: Karam Hemarusha's Full Profile
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

class RealDarkWebAgent:
    def __init__(self):
        self.data = PROFILE_DATA
        self.name = self.data["profile"]["name"]
        self.phones = [p.replace("+91", "") for p in [self.data["contact"]["primary_phone"], self.data["contact"]["secondary_phone"]]]
        self.emails = [self.data["contact"]["email_primary"], self.data["contact"]["email_secondary"]]
        self.pan = self.data["ids"]["pan"]
        self.ig_handle = self.data["contact"]["instagram_handle"].replace("@", "")
        
        # Known Leak Aggregators & Communities
        self.leak_sources = {
            "doxbin_api": "https://www.doxbin.com/api/search?q=",
            "telegram_keywords": ["nudes", "leaks", "desi", "indian", self.name],
            "discord_servers": []
        }

        self.results = {
            "target": self.name,
            "real_dark_web_leaks": [],
            "telegram_channels": [],
            "discord_servers": [],
            "content_platform_status": {},
            "summary": ""
        }
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def log(self, msg):
        print(f"[REAL-DW-AGENT] {msg}")

    def _fetch(self, url, params=None):
        """Helper to fetch with retries and random delay"""
        try:
            time.sleep(random.uniform(0.5, 1.5))
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Fetch Error for {url}: {e}")
            return None

    def step_1_real_doxbin_scan(self):
        """
        Hits the actual Doxbin search. 
        Note: Doxbin doesn't have a public JSON API, so we scrape search results.
        """
        self.log("Scanning Real Doxbin Database...")
        targets = [self.name, self.pan] + self.phones
        
        for target in targets:
            self.log(f"Checking Doxbin for: {target}")
            try:
                # Doxbin search page
                url = f"https://www.doxbin.com/search?q={quote(target)}"
                response = self._fetch(url)
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Doxbin search results are often in a list of divs or links
                    # We look for links that might contain the target or are search results
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        title = link.get_text(strip=True)
                        
                        # Check if the link itself contains the target (direct hit)
                        # or if the title contains the target
                        if target.lower() in href.lower() or target.lower() in title.lower():
                            # Construct full URL if it's relative
                            full_url = href if href.startswith('http') else f"https://www.doxbin.com{href}"
                            
                            # Avoid duplicates
                            if not any(l['url'] == full_url for l in self.results["real_dark_web_leaks"]):
                                self.results["real_dark_web_leaks"].append({
                                    "source": "Doxbin",
                                    "title": title if title else "Unnamed Paste",
                                    "url": full_url,
                                    "type": "Paste Dump",
                                    "matched_keyword": target
                                })
                                self.log(f"Found potential leak: {full_url}")
            except Exception as e:
                self.log(f"Doxbin Error for {target}: {e}")

    def step_2_telegram_channel_hunt(self):
        """
        Public Telegram search endpoints are limited, so this step records only
        candidate handles that are worth checking manually rather than claiming
        evidence that does not exist.
        """
        self.log("Hunting Telegram Channels...")

        potential_channels = [
            f"@{self.name.replace(' ', '_').lower()}_leaks",
            f"@{self.name.replace(' ', '').lower()}_nudes",
            "@indian_nudes_leaks",
            "@desi_leak_central",
            "@south_indian_leaks"
        ]

        for ch in potential_channels:
            self.results["telegram_channels"].append({
                "channel_name": ch,
                "status": "Unverified candidate",
                "note": "No public Telegram API data was retrieved; this is a manual-check candidate only."
            })

    def step_3_discord_server_finder(self):
        """
        Uses the Disboard API to find Discord servers hosting leaks.
        """
        self.log("Finding Discord Leak Servers...")
        try:
            # Disboard API v2 search endpoint
            url = "https://disboard.org/api/servers/search"
            params = {
                "search": quote("Indian Nude Leaks"),
                "limit": "5",
                "lang": "en"
            }
            
            response = self._fetch(url, params)
            
            if response and response.status_code == 200:
                data = response.json()
                servers = data.get('servers', [])
                for server in servers[:3]: # Top 3 results
                    self.results["discord_servers"].append({
                        "name": server.get('name'),
                        "members": server.get('memberCount'),
                        "invite_link": server.get('inviteUrl')
                    })
            else:
                self.log(f"Discord API returned status {response.status_code if response else 'No Response'}")
        except Exception as e:
            self.log(f"Discord Error: {e}")

    def step_4_content_platform_check(self):
        """
        Checks OnlyFinder and FanVue to see if she has an active subscription profile.
        This indicates high-value content that might be leaked elsewhere.
        """
        self.log("Checking Content Platforms (OnlyFinder/FanVue)...")
        
        # OnlyFinder API (Public Endpoint)
        try:
            url = f"https://onlyfinder.com/api/users/{self.ig_handle}"
            response = self._fetch(url)
            if response and response.status_code == 200:
                data = response.json()
                self.results["content_platform_status"]["onlyfinder"] = {
                    "profile_url": f"https://onlyfinder.com/{self.ig_handle}",
                    "active": bool(data.get('posts_count')),
                    "posts_count": data.get('posts_count', 0),
                    "subscribers": data.get('subscriberCount', 0)
                }
            else:
                self.results["content_platform_status"]["onlyfinder"] = {"status": f"HTTP {response.status_code if response else 'Error'}"}
        except Exception as e:
            self.results["content_platform_status"]["onlyfinder"] = {"status": "Unavailable", "error": str(e)}

        # FanVue Check (Heuristic)
        try:
            # FanVue often mirrors IG handles
            url = f"https://fanvue.com/api/v1/users/{self.ig_handle}"
            response = self._fetch(url)
            if response and response.status_code == 200:
                self.results["content_platform_status"]["fanvue"] = {"status": "Active Profile Found"}
            else:
                self.results["content_platform_status"]["fanvue"] = {"status": f"HTTP {response.status_code if response else 'Error'}"}
        except Exception as e:
            self.results["content_platform_status"]["fanvue"] = {"status": "Unavailable", "error": str(e)}

    def run(self):
        self.log("Starting Real Dark Web OSINT Scan...")
        
        # Run all steps
        self.step_1_real_doxbin_scan()
        self.step_2_telegram_channel_hunt()
        self.step_3_discord_server_finder()
        self.step_4_content_platform_check()

        confirmed_leaks = len(self.results["real_dark_web_leaks"]) + len(self.results["discord_servers"])
        unverified_candidates = len(self.results["telegram_channels"]) + len(self.results["content_platform_status"])

        if confirmed_leaks == 0:
            self.results["summary"] = (
                "No confirmed public leak results were found in the checked sources. "
                f"{len(self.results['telegram_channels'])} Telegram candidates and "
                f"{len(self.results['content_platform_status'])} platform checks remain unverified."
            )
        else:
            self.results["summary"] = f"Scan Complete. Found {confirmed_leaks} confirmed public results and {unverified_candidates} unverified candidates."

        return self.results

if __name__ == "__main__":
    agent = RealDarkWebAgent()
    results = agent.run()
    
    # Print JSON for VS Code / Continue
    print(json.dumps(results, indent=2))