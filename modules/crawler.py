import requests
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
urllib3.disable_warnings()
from config import MAX_PAGES_PER_DOMAIN, CRAWL_DELAY, REQUEST_TIMEOUT

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"},
]

PRIORITY_KEYWORDS = [
    # Contact
    "contact", "contact-us", "contactus", "reach", "reach-us",
    "get-in-touch", "getintouch", "talk-to-us", "say-hello",
    "connect", "enquiry", "inquiry", "email-us", "mail-us",
    "message", "touch", "write-us", "write-to-us", "ping",

    # About
    "about", "about-us", "aboutus", "our-story", "ourstory",
    "who-we-are", "whoweare", "mission", "vision", "overview",
    "introduction", "our-mission", "story",

    # Team
    "team", "people", "staff", "crew", "founders", "leadership",
    "our-team", "meet-the-team", "executives", "management",
    "board", "directors", "advisors", "employees",

    # Security
    "security", "disclosure", "responsible-disclosure",
    "responsibledisclosure", "vulnerability", "vulnerability-disclosure",
    "bounty", "bug-bounty", "bugbounty", "vdp", "bbp",
    "report", "cvd", "pentest", "hackerone", "bugcrowd",
    "intigriti", "yeswehack", "security-policy", "securitypolicy",
    "security-research", "report-vulnerability", "hall-of-fame",

    # Support
    "support", "help", "faq", "helpdesk", "help-center",
    "helpcenter", "helpcentre", "assistance", "customer-service",
    "customerservice", "customer-support", "customersupport",
    "ticket", "tickets",

    # Company
    "company", "corporate", "organization", "organisation",
    "business", "partners", "investors", "press", "media",
    "newsroom", "news", "blog", "updates", "announcements",
    "pr", "communications",

    # Legal
    "legal", "privacy", "terms", "policy", "compliance",
    "gdpr", "cookies", "disclaimer", "tos", "terms-of-service",
    "terms-of-use", "privacy-policy",

    # Jobs
    "careers", "jobs", "hiring", "work-with-us", "join-us",
    "join", "work", "opportunities", "openings", "vacancies",
    "positions", "recruitment",

    # Technical
    "humans", "robots", "sitemap", "well-known",
    "security.txt", "pgp", "gpg", "keys",
]

SEED_PATHS = [
    # Core
    "/", "/contact", "/contact-us", "/contactus", "/contact_us",
    "/about", "/about-us", "/aboutus", "/about_us",
    "/team", "/our-team", "/ourteam", "/people", "/staff",
    "/company", "/corporate", "/organization", "/organisation",
    "/security", "/security.txt", "/.well-known/security.txt",
    "/robots.txt", "/humans.txt", "/sitemap.xml",
    "/support", "/help", "/faq", "/faqs",
    "/press", "/media", "/newsroom", "/news",
    "/legal", "/privacy", "/terms",
    "/careers", "/jobs", "/blog",

    # Contact variants
    "/reach", "/reach-us", "/reach_us", "/reachout",
    "/get-in-touch", "/getintouch", "/get_in_touch",
    "/talk-to-us", "/talktous", "/talk_to_us",
    "/say-hello", "/sayhello", "/hello",
    "/connect", "/connect-with-us", "/connectwithus",
    "/enquiry", "/enquiries", "/inquiry", "/inquiries",
    "/email", "/email-us", "/emailus", "/mail", "/mail-us",
    "/message", "/messages", "/message-us",
    "/write-to-us", "/write-us", "/writeus",
    "/ping", "/drop-us-a-line", "/drop-a-line",
    "/lets-talk", "/letstalk", "/lets_talk",
    "/get-help", "/gethelp", "/ask",
    "/feedback", "/feedbacks", "/suggestions",
    "/report", "/reports", "/submit",
    "/hire-us", "/hireus", "/hire_us",
    "/work-with-us", "/workwithus", "/work_with_us",
    "/partner-with-us", "/partnerwithus",

    # About variants
    "/our-story", "/ourstory", "/our_story",
    "/who-we-are", "/whoweare", "/who_we_are",
    "/mission", "/our-mission", "/ourmission",
    "/vision", "/our-vision", "/ourvision",
    "/values", "/our-values", "/ourvalues",
    "/overview", "/introduction", "/intro",
    "/history", "/background", "/profile",
    "/manifesto", "/philosophy", "/culture",

    # Team variants
    "/meet-the-team", "/meettheteam", "/meet_the_team",
    "/meet-us", "/meetus", "/our-people", "/ourpeople",
    "/leadership", "/leaders", "/management",
    "/founders", "/founder", "/co-founders", "/cofounders",
    "/executives", "/executive-team", "/executiveteam",
    "/board", "/board-of-directors", "/boardofdirectors",
    "/advisors", "/advisory-board", "/advisoryboard",
    "/directors", "/officers", "/c-suite", "/csuite",
    "/employees", "/members", "/contributors",

    # Security variants
    "/security-policy", "/securitypolicy", "/security_policy",
    "/security-research", "/securityresearch",
    "/security-disclosure", "/securitydisclosure",
    "/responsible-disclosure", "/responsibledisclosure",
    "/responsible_disclosure", "/coordinated-disclosure",
    "/vulnerability-disclosure", "/vulnerabilitydisclosure",
    "/vulnerability_disclosure", "/vulnerability-reporting",
    "/bug-bounty", "/bugbounty", "/bug_bounty",
    "/bounty", "/bounty-program", "/bountyprogram",
    "/vdp", "/bbp", "/cvd", "/pentest",
    "/hackerone", "/bugcrowd", "/intigriti",
    "/yeswehack", "/openbugbounty",
    "/report-vulnerability", "/reportvulnerability",
    "/report-a-bug", "/reportabug", "/report-bug",
    "/hall-of-fame", "/halloffame", "/hof",
    "/thanks", "/acknowledgements", "/acknowledgments",
    "/security-advisories", "/advisories",
    "/cve", "/cves", "/patches", "/patch-notes",
    "/pgp", "/gpg", "/publickey", "/public-key",
    "/keys", "/.well-known/pgp-key.txt",
    "/.well-known/gpg-key.txt",

    # Support variants
    "/helpdesk", "/help-desk", "/help-center",
    "/helpcenter", "/help_center", "/helpcentre",
    "/customer-service", "/customerservice",
    "/customer-support", "/customersupport",
    "/customer-care", "/customercare",
    "/tickets", "/open-ticket", "/new-ticket",
    "/submit-ticket", "/support-ticket",
    "/knowledge-base", "/knowledgebase", "/kb",
    "/documentation", "/docs", "/wiki",
    "/guides", "/tutorials", "/resources",
    "/forum", "/forums", "/community",
    "/chat", "/live-chat", "/livechat",

    # Legal variants
    "/terms-of-service", "/termsofservice", "/tos",
    "/terms-of-use", "/termsofuse", "/tou",
    "/privacy-policy", "/privacypolicy",
    "/cookie-policy", "/cookiepolicy", "/cookies",
    "/disclaimer", "/disclaimers",
    "/compliance", "/gdpr", "/ccpa",
    "/aup", "/acceptable-use", "/acceptableuse",
    "/dmca", "/copyright", "/ip-policy",
    "/data-protection", "/dataprotection",

    # Jobs variants
    "/hiring", "/we-are-hiring", "/wearehiring",
    "/join", "/join-us", "/joinus", "/join_us",
    "/join-our-team", "/joinourteam",
    "/openings", "/open-positions", "/openpositions",
    "/vacancies", "/vacancy", "/positions",
    "/recruitment", "/recruit", "/apply",
    "/internships", "/internship", "/intern",
    "/graduate", "/graduate-program",

    # Press variants
    "/press-kit", "/presskit", "/press_kit",
    "/press-releases", "/pressreleases",
    "/press-room", "/pressroom",
    "/media-kit", "/mediakit", "/media_kit",
    "/media-contact", "/mediacontact",
    "/journalists", "/editorial",
    "/brand", "/brand-assets", "/brandassets",
    "/logo", "/logos", "/assets",

    # Company variants
    "/investors", "/investor-relations", "/investorrelations",
    "/partners", "/partnerships", "/partner",
    "/affiliates", "/affiliate", "/resellers",
    "/vendors", "/suppliers",
    "/customers", "/clients", "/case-studies",
    "/testimonials", "/reviews",

    # Blog/News variants
    "/blog/contact", "/blog/about",
    "/updates", "/changelog", "/release-notes",
    "/announcements", "/announcement",
    "/events", "/event", "/webinars", "/webinar",
    "/podcast", "/podcasts", "/videos",

    # Developer
    "/api", "/api/contact", "/developer",
    "/developers", "/dev", "/open-source",
    "/opensource", "/github", "/contributing",
    "/contribute", "/contributors",

    # Misc
    "/sitemap", "/sitemap-index.xml",
    "/site-map", "/page-sitemap.xml",
    "/imprint", "/impressum",
    "/accessibility", "/a11y",
    "/trust", "/trust-center", "/trustcenter",
    "/status", "/statuspage",
    "/offices", "/office", "/locations", "/location",
    "/headquarters", "/hq",
    "/map", "/directions",
    "/social", "/social-media",
    "/newsletter", "/subscribe", "/unsubscribe",
    "/opt-in", "/opt-out",
    "/referral", "/referrals", "/refer",
    "/ambassador", "/ambassadors",
]

def fetch_with_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage","--disable-gpu"])
            page = browser.new_page()
            page.goto(url, timeout=10000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"[playwright] error: {e}")
        return None

def get_session():
    s = requests.Session()
    s.headers.update(random.choice(HEADERS_LIST))
    return s

def safe_get(url, session):
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT, verify=True)
        if r.status_code == 200:
            return r
        return None
    except requests.exceptions.SSLError:
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            if r.status_code == 200:
                return r
            return None
        except:
            return None
    except:
        return None

def score_link(url):
    url_lower = url.lower()
    for i, keyword in enumerate(PRIORITY_KEYWORDS):
        if keyword in url_lower:
            return len(PRIORITY_KEYWORDS) - i
    return 0

def get_links(base_url, html, domain):
    links = []
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Priority: nav + footer + header links
        priority_links = set()
        for tag in soup.find_all(['nav', 'footer', 'header']):
            for a in tag.find_all("a", href=True):
                full = urljoin(base_url, a["href"])
                parsed = urlparse(full)
                if domain in parsed.netloc:
                    priority_links.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")

        # All links
        all_links = set()
        for tag in soup.find_all("a", href=True):
            full = urljoin(base_url, tag["href"])
            parsed = urlparse(full)
            if domain in parsed.netloc:
                all_links.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")

        # Score and sort
        scored = []
        for link in all_links:
            score = score_link(link)
            if link in priority_links:
                score += 10
            scored.append((score, link))

        scored.sort(reverse=True)
        links = [l for _, l in scored]

    except:
        pass
    return links

def get_sitemap_urls(domain, session):
    urls = set()
    sitemaps = [
        f"https://{domain}/sitemap.xml",
        f"https://{domain}/sitemap_index.xml",
        f"https://{domain}/sitemap-index.xml",
        f"https://{domain}/sitemaps.xml",
        f"https://www.{domain}/sitemap.xml",
    ]
    for sitemap_url in sitemaps:
        try:
            r = safe_get(sitemap_url, session)
            if r:
                soup = BeautifulSoup(r.text, "xml")
                for loc in soup.find_all("loc"):
                    urls.add(loc.text.strip())
                if urls:
                    break
        except:
            pass
    return list(urls)[:MAX_PAGES_PER_DOMAIN]

def get_robots_paths(domain, session):
    paths = []
    try:
        r = safe_get(f"https://{domain}/robots.txt", session)
        if r:
            for line in r.text.split('\n'):
                line = line.strip()
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    paths.append(sitemap_url)
                elif line.lower().startswith('allow:') or line.lower().startswith('disallow:'):
                    path = line.split(':', 1)[1].strip()
                    if path and path != '/':
                        paths.append(f"https://{domain}{path}")
    except:
        pass
    return paths

def crawl(domain, log_callback=None):
    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    session = get_session()
    visited = set()

    to_visit = [f"https://{domain}{path}" for path in SEED_PATHS]
    sitemap_urls = get_sitemap_urls(domain, session)
    to_visit.extend(sitemap_urls)
    robots_paths = get_robots_paths(domain, session)
    to_visit.extend(robots_paths)

    seen = set()
    deduped = []
    for url in to_visit:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    to_visit = deduped

    pages_data = []
    log(f"[crawl] Starting {domain} — {len(to_visit)} URLs queued")

    while to_visit and len(visited) < MAX_PAGES_PER_DOMAIN:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        HOSTING_PLATFORMS = ["vercel.app", "netlify.app", "github.io", "pages.dev"]
        use_playwright = any(p in domain for p in HOSTING_PLATFORMS) and url == f"https://{domain}/"
        if use_playwright:
            content = fetch_with_playwright(url)
            if content:
                log(f"[ok] {url}")
                pages_data.append({"url": url, "content": content})
                continue
        r = safe_get(url, session)
        if not r:
            log(f"[skip] {url}")
            continue
        log(f"[ok] {url}")
        pages_data.append({"url": url, "content": r.text})

        new_links = get_links(url, r.text, domain)
        for link in new_links:
            if link not in visited and link not in to_visit:
                to_visit.insert(0, link)

        time.sleep(CRAWL_DELAY)

    log(f"[done] {len(pages_data)} pages crawled")
    return pages_data

