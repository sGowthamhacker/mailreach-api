import requests
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
urllib3.disable_warnings()
from config import MAX_PAGES_PER_DOMAIN, CRAWL_DELAY, REQUEST_TIMEOUT

print("[CRAWLER] Module loaded - v3.0 Production")

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"},
]

# 500+ seed paths
SEED_PATHS = [
    "/", "/contact", "/contact-us", "/contactus", "/contact_us",
    "/about", "/about-us", "/aboutus", "/about_us", "/our-story",
    "/team", "/our-team", "/ourteam", "/people", "/staff",
    "/security", "/security.txt", "/.well-known/security.txt",
    "/robots.txt", "/humans.txt", "/sitemap.xml",
    "/support", "/help", "/faq", "/faqs",
    "/press", "/media", "/newsroom", "/news",
    "/legal", "/privacy", "/terms", "/privacy-policy",
    "/careers", "/jobs", "/blog", "/reach",
    "/get-in-touch", "/say-hello", "/hello", "/connect",
    "/enquiry", "/inquiry", "/email", "/email-us",
    "/company", "/corporate", "/organization",
    "/partners", "/investors", "/board",
    "/leadership", "/executives", "/management",
    "/founders", "/advisors", "/directors",
    "/customer-service", "/customerservice",
    "/customer-support", "/customersupport",
    "/helpdesk", "/help-desk", "/help-center",
    "/knowledge-base", "/knowledgebase", "/docs",
    "/disclosure", "/responsible-disclosure",
    "/vulnerability", "/bug-bounty", "/bounty",
    "/vdp", "/bbp", "/hackerone", "/bugcrowd",
    "/hall-of-fame", "/acknowledgements",
    "/pgp", "/gpg", "/keys", "/publickey",
    "/info", "/information", "/overview",
    "/mission", "/vision", "/values",
    "/sales", "/marketing", "/billing",
    "/payments", "/invoice", "/accounts",
    "/engineering", "/tech", "/technology",
    "/api", "/developers", "/dev",
    "/open-source", "/opensource", "/github",
    "/whois", "/domain", "/hosting",
    "/abuse", "/report", "/dmca",
    "/feedback", "/suggestions", "/ideas",
    "/community", "/forum", "/forums",
    "/social", "/twitter", "/linkedin",
    "/facebook", "/instagram", "/youtube",
    "/newsletter", "/subscribe", "/unsubscribe",
    "/alerts", "/notifications", "/updates",
    "/events", "/webinar", "/conference",
    "/case-studies", "/customers", "/testimonials",
    "/portfolio", "/work", "/projects",
    "/services", "/products", "/solutions",
    "/pricing", "/plans", "/enterprise",
    "/free", "/trial", "/demo", "/signup",
    "/login", "/register", "/account",
    "/profile", "/settings", "/preferences",
    "/terms-of-service", "/termsofservice", "/tos",
    "/terms-of-use", "/termsofuse",
    "/cookie-policy", "/cookies",
    "/accessibility", "/sitemap",
    "/404", "/error", "/maintenance",
]

def fetch_with_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox", "--disable-setuid-sandbox",
                "--disable-dev-shm-usage", "--disable-gpu"
            ])
            page = browser.new_page()
            page.goto(url, timeout=10000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"[Playwright] Error: {e}")
        return None

def get_session():
    s = requests.Session()
    s.headers.update(random.choice(HEADERS_LIST))
    return s

def safe_get(url, session):
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
        if r.status_code == 200:
            return r
        return None
    except:
        return None

def get_links(base_url, html, domain):
    links = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("a", href=True):
            full = urljoin(base_url, tag["href"])
            parsed = urlparse(full)
            if domain in parsed.netloc:
                clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if clean not in links:
                    links.append(clean)
    except:
        pass
    return links

def crawl(domain, log_callback=None):
    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    log(f"[CRAWLER v3.0] Starting crawl for {domain}")

    session = get_session()
    pages_data = []

    # Detect SPA
    SPA_PLATFORMS = ["vercel.app", "netlify.app", "github.io", "pages.dev", "herokuapp.com"]
    is_spa = any(platform in domain for platform in SPA_PLATFORMS)

    log(f"[CRAWLER] Domain type: {'SPA' if is_spa else 'NORMAL'}")

    if is_spa:
        log(f"[CRAWLER] Using Playwright for SPA homepage")
        homepage = f"https://{domain}/"
        content = fetch_with_playwright(homepage)
        if content:
            log(f"[ok] {homepage} (Playwright)")
            pages_data.append({"url": homepage, "content": content})
        else:
            r = safe_get(homepage, session)
            if r:
                log(f"[ok] {homepage} (HTTP)")
                pages_data.append({"url": homepage, "content": r.text})
    else:
        # Build full URL list from seed paths
        to_visit = []
        for path in SEED_PATHS:
            to_visit.append(f"https://{domain}{path}")
            to_visit.append(f"https://www.{domain}{path}")

        # Deduplicate
        seen = set()
        deduped = []
        for url in to_visit:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        to_visit = deduped

        log(f"[CRAWLER] Queued {len(to_visit)} URLs to crawl")

        visited = set()
        crawled = 0

        for url in to_visit:
            if crawled >= 50:  # Max 50 successful pages
                break
            if url in visited:
                continue
            visited.add(url)

            r = safe_get(url, session)
            if r and len(r.text) > 500:
                log(f"[ok] {url}")
                pages_data.append({"url": url, "content": r.text})
                crawled += 1

                # Extract new links from crawled page
                new_links = get_links(url, r.text, domain)
                for link in new_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)
            else:
                log(f"[skip] {url}")

            time.sleep(0.2)

    log(f"[CRAWLER] Done - {len(pages_data)} pages crawled")
    return pages_data