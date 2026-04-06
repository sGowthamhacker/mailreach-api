import requests
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
urllib3.disable_warnings()
from config import MAX_PAGES_PER_DOMAIN, CRAWL_DELAY, REQUEST_TIMEOUT
from modules.email_extractor import extract_from_html, extract_from_js_files

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"},
]

PRIORITY_KEYWORDS = [
    "contact", "contact-us", "contactus", "reach", "reach-us",
    "get-in-touch", "getintouch", "talk-to-us", "say-hello",
    "connect", "enquiry", "inquiry", "email-us", "mail-us",
    "message", "touch", "write-us", "write-to-us", "ping",
    "about", "about-us", "aboutus", "our-story", "ourstory",
    "who-we-are", "whoweare", "mission", "vision", "overview",
    "introduction", "our-mission", "story",
    "team", "people", "staff", "crew", "founders", "leadership",
    "our-team", "meet-the-team", "executives", "management",
    "board", "directors", "advisors", "employees",
    "security", "disclosure", "responsible-disclosure",
    "responsibledisclosure", "vulnerability", "vulnerability-disclosure",
    "bounty", "bug-bounty", "bugbounty", "vdp", "bbp",
    "report", "cvd", "pentest", "hackerone", "bugcrowd",
    "intigriti", "yeswehack", "security-policy", "securitypolicy",
    "security-research", "report-vulnerability", "hall-of-fame",
    "support", "help", "faq", "helpdesk", "help-center",
    "helpcenter", "helpcentre", "assistance", "customer-service",
    "customerservice", "customer-support", "customersupport",
    "ticket", "tickets",
    "company", "corporate", "organization", "organisation",
    "business", "partners", "investors", "press", "media",
    "newsroom", "news", "blog", "updates", "announcements",
    "pr", "communications",
    "legal", "privacy", "terms", "policy", "compliance",
    "gdpr", "cookies", "disclaimer", "tos", "terms-of-service",
    "terms-of-use", "privacy-policy",
    "careers", "jobs", "hiring", "work-with-us", "join-us",
    "join", "work", "opportunities", "openings", "vacancies",
    "positions", "recruitment",
    "humans", "robots", "sitemap", "well-known",
    "security.txt", "pgp", "gpg", "keys",
]

SEED_PATHS = [
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
        print(f"[fetch_with_playwright] ERROR: {str(e)}")
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
        priority_links = set()
        for tag in soup.find_all(['nav', 'footer', 'header']):
            for a in tag.find_all("a", href=True):
                full = urljoin(base_url, a["href"])
                parsed = urlparse(full)
                if domain in parsed.netloc:
                    priority_links.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
        all_links = set()
        for tag in soup.find_all("a", href=True):
            full = urljoin(base_url, tag["href"])
            parsed = urlparse(full)
            if domain in parsed.netloc:
                all_links.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
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

    SKIP_EXTENSIONS = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', 
                       '.ico', '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip', '.tar', 
                       '.gz', '.mp4', '.mp3', '.wav', '.mov']

    while to_visit and len(visited) < 50:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        is_static = any(url.lower().endswith(ext) for ext in SKIP_EXTENSIONS)
        if is_static:
            log(f"[skip] {url} (static file)")
            continue

        content = None
        HOSTING_PLATFORMS = ["vercel.app", "netlify.app", "github.io", "pages.dev"]
        is_hosting = any(p in domain for p in HOSTING_PLATFORMS)
        is_homepage = url.rstrip('/') == f"https://{domain}".rstrip('/')
        
        if is_hosting and is_homepage:
            content = fetch_with_playwright(url)
        
        if not content:
            r = safe_get(url, session)
            if r:
                content = r.text
            else:
                log(f"[skip] {url}")
                continue
        
        log(f"[ok] {url}")
        pages_data.append({"url": url, "content": content})

        if len(visited) < 50:
            new_links = get_links(url, content, domain)
            for link in new_links:
                if link not in visited and link not in to_visit:
                    to_visit.insert(0, link)

        time.sleep(0.5)

    log(f"[done] {len(pages_data)} pages crawled")
    return pages_data