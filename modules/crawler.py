import requests
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
urllib3.disable_warnings()
from config import MAX_PAGES_PER_DOMAIN, CRAWL_DELAY, REQUEST_TIMEOUT

print("[CRAWLER] Module loaded - v2.0 Production")

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"},
]

def fetch_with_playwright(url):
    """Fetch page with Playwright for JS-heavy sites"""
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

def crawl(domain, log_callback=None):
    """
    Smart crawler for SPAs (Vercel, Netlify) and regular sites.
    For SPAs: Fetch homepage with Playwright (serves all content via JS)
    For normal sites: Crawl multiple pages
    """
    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    log(f"[CRAWLER v2.0] Starting crawl for {domain}")
    
    session = get_session()
    pages_data = []

    # Detect SPA
    SPA_PLATFORMS = ["vercel.app", "netlify.app", "github.io", "pages.dev", "herokuapp.com"]
    is_spa = any(platform in domain for platform in SPA_PLATFORMS)
    
    log(f"[CRAWLER] Domain type: {'SPA' if is_spa else 'NORMAL'}")

    if is_spa:
        # For SPAs: Use Playwright on homepage
        log(f"[CRAWLER] Using Playwright for SPA homepage")
        homepage = f"https://{domain}/"
        
        content = fetch_with_playwright(homepage)
        if content:
            log(f"[ok] {homepage} (Playwright)")
            pages_data.append({"url": homepage, "content": content})
        else:
            # Fallback to HTTP
            r = safe_get(homepage, session)
            if r:
                log(f"[ok] {homepage} (HTTP fallback)")
                pages_data.append({"url": homepage, "content": r.text})
            else:
                log(f"[skip] {homepage} (no content)")
    else:
        # For normal sites: Crawl important pages
        important_paths = [
            "/", "/contact", "/about", "/team", "/security",
            "/support", "/help", "/careers", "/privacy", "/legal",
        ]
        
        to_visit = [f"https://{domain}{path}" for path in important_paths]
        log(f"[CRAWLER] Queued {len(to_visit)} important URLs")
        
        visited = set()
        for url in to_visit[:10]:  # Limit to 10 pages
            if url in visited:
                continue
            visited.add(url)
            
            r = safe_get(url, session)
            if r and len(r.text) > 500:
                log(f"[ok] {url}")
                pages_data.append({"url": url, "content": r.text})
            else:
                log(f"[skip] {url}")
            
            time.sleep(0.3)

    log(f"[CRAWLER] Done - {len(pages_data)} pages crawled")
    return pages_data