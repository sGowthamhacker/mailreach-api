import requests
import random
import time
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from urllib.parse import urljoin, urlparse
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
urllib3.disable_warnings()
from config import MAX_PAGES_PER_DOMAIN, CRAWL_DELAY, REQUEST_TIMEOUT

print("[CRAWLER] Module loaded - v4.0 Subdomain Edition")

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"},
]

COMMON_SUBDOMAINS = [
    "www", "mail", "email", "webmail", "smtp", "imap", "pop", "mx",
    "help", "support", "helpdesk", "kb", "docs", "documentation",
    "blog", "news", "press", "media", "newsroom", "pr",
    "about", "team", "careers", "jobs", "hiring", "recruit",
    "contact", "info", "hello", "reach", "connect", "touch",
    "security", "trust", "privacy", "legal", "compliance", "gdpr",
    "developer", "developers", "dev", "api", "apis", "platform",
    "status", "uptime", "monitor", "health", "ping",
    "community", "forum", "forums", "discuss", "chat", "slack",
    "partners", "partner", "affiliate", "affiliates", "reseller",
    "investors", "ir", "investor",
    "shop", "store", "checkout", "cart", "buy", "order",
    "app", "mobile", "m", "wap",
    "cdn", "static", "assets", "img", "images", "media",
    "corp", "corporate", "business", "enterprise",
    "admin", "portal", "dashboard", "panel", "console",
    "learn", "learning", "training", "academy", "education",
    "events", "conference", "meetup", "webinar",
    "marketing", "sales", "crm", "leads",
    "engineering", "tech", "technology", "infrastructure",
    "cloud", "aws", "azure", "gcp",
    "staging", "stage", "uat", "qa", "test", "demo", "sandbox",
    "beta", "alpha", "preview", "next", "new",
    "old", "legacy", "v1", "v2", "v3",
    "secure", "ssl", "vpn", "remote", "access",
    "intranet", "internal", "extranet",
    "hr", "humanresources", "people", "talent",
    "finance", "billing", "payments", "invoice", "accounting",
    "legal", "contracts", "compliance",
    "research", "labs", "lab", "innovation", "rd",
    "design", "creative", "ux", "ui", "brand",
    "content", "editorial", "publish", "cms",
    "analytics", "data", "insights", "metrics", "stats",
    "feedback", "survey", "form", "forms",
    "abuse", "spam", "report", "phishing",
    "noc", "ops", "devops", "sre", "infra",
    "vpn", "proxy", "gateway", "edge",
    "download", "downloads", "files", "ftp",
    "upload", "uploads", "storage",
    "backup", "archive", "logs",
    "wiki", "knowledge", "base", "faq",
    "open", "opensource", "github",
    "global", "international", "worldwide",
    "us", "uk", "eu", "in", "au", "ca", "de", "fr", "jp",
    "asia", "apac", "emea", "latam", "amer",
    "east", "west", "north", "south",
    "ny", "la", "sf", "london", "paris", "berlin", "tokyo",
    "signup", "register", "login", "auth", "sso", "id",
    "account", "accounts", "profile", "user", "users",
    "customer", "customers", "client", "clients",
    "vendor", "vendors", "supplier", "suppliers",
    "network", "net", "dns", "whois",
    "tools", "tool", "utility", "utilities",
    "project", "projects", "work", "workspace",
    "org", "foundation", "charity", "nonprofit",
    "ceo", "cto", "cfo", "board", "exec", "executives",
    "office", "offices", "hq", "headquarters",
    "newsletter", "subscribe", "updates", "alerts",
    "search", "find", "discover",
    "home", "main", "index", "root",
    "public", "open", "free",
    "pro", "premium", "plus", "elite",
    "solutions", "services", "products",
    "hosting", "cloud", "saas", "paas",
    "monitor", "monitoring", "alert", "alerting",
    "ticket", "tickets", "issue", "issues", "bugs",
    "release", "releases", "changelog", "updates",
    "social", "connect", "network",
    "video", "videos", "media", "stream",
    "podcast", "audio", "radio",
    "map", "maps", "location", "locations",
    "jobs2", "careers2", "apply",
    "internship", "intern", "graduate",
    "csr", "sustainability", "green", "environment",
    "safety", "risk", "fraud", "verify",
    "id", "identity", "passport", "verify",
    "pay", "payment", "checkout", "subscribe",
    "trial", "free", "freemium",
    "partner2", "ecosystem", "marketplace",
    "white-label", "whitelabel", "oem",
    "resellers", "channel", "distribution",
]

SEED_PATHS = [
    "/", "/contact", "/about", "/team", "/security",
    "/support", "/help", "/docs", "/blog",
    "/contact-us", "/about-us",
    "/security.txt", "/.well-known/security.txt",
    "/humans.txt", "/robots.txt",
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
    "/reach", "/reach-us", "/get-in-touch", "/getintouch",
    "/talk-to-us", "/say-hello", "/hello", "/connect",
    "/enquiry", "/enquiries", "/inquiry", "/inquiries",
    "/email", "/email-us", "/mail", "/message", "/feedback",
    "/our-story", "/ourstory", "/who-we-are", "/whoweare",
    "/mission", "/vision", "/values", "/overview",
    "/leadership", "/leaders", "/management",
    "/founders", "/executives", "/board", "/advisors",
    "/security-policy", "/responsible-disclosure",
    "/vulnerability-disclosure", "/bug-bounty", "/bugbounty",
    "/vdp", "/bbp", "/hackerone", "/bugcrowd",
    "/hall-of-fame", "/halloffame",
    "/helpdesk", "/help-center", "/helpcenter",
    "/customer-service", "/customerservice",
    "/customer-support", "/customersupport",
    "/knowledge-base", "/knowledgebase", "/docs",
    "/terms-of-service", "/termsofservice", "/tos",
    "/privacy-policy", "/privacypolicy",
    "/compliance", "/gdpr", "/dmca",
    "/hiring", "/join", "/press-kit", "/presskit",
    "/investors", "/investor-relations",
    "/partners", "/partnerships",
    "/api", "/developer", "/developers",
    "/imprint", "/impressum",
    "/trust", "/trust-center",
    "/offices", "/locations", "/headquarters",
    "/newsletter", "/subscribe",
    "/sales", "/marketing", "/billing",
    "/events", "/webinars", "/updates", "/changelog",
    "/community", "/forum",
]

PRIORITY_KEYWORDS = [
    "contact", "about", "security", "team", "help", "support",
    "reach", "hello", "connect", "email", "touch", "inquiry",
    "enquiry", "disclosure", "bounty", "vdp", "press", "legal",
    "privacy", "careers", "jobs", "people", "leadership",
]

def get_session():
    s = requests.Session()
    s.headers.update(random.choice(HEADERS_LIST))
    s.verify = False
    return s

def safe_get(url, session, timeout=5):
    try:
        r = session.get(url, timeout=timeout, verify=False)
        if r.status_code == 200:
            return r
        return None
    except:
        return None

def fetch_url_parallel(url):
    try:
        s = get_session()
        r = s.get(url, timeout=8, verify=False, allow_redirects=True)
        if r.status_code in [200, 201, 203] and len(r.text) > 100:
            return url, r.text
        return url, None
    except:
        return url, None

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
        all_links = set()
        for tag in soup.find_all("a", href=True):
            full = urljoin(base_url, tag["href"])
            parsed = urlparse(full)
            if domain in parsed.netloc:
                all_links.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
        scored = [(score_link(l), l) for l in all_links]
        scored.sort(reverse=True)
        links = [l for _, l in scored]
    except:
        pass
    return links

def discover_subdomains(domain, session):
    subdomains = []
    parts = domain.split(".")
    root = ".".join(parts[-2:]) if len(parts) > 2 else domain

    def check_subdomain(sub):
        url = f"https://{sub}.{root}/"
        try:
            s = get_session()
            r = s.get(url, timeout=4, verify=False, allow_redirects=True)
            if r.status_code in [200, 301, 302, 403]:
                parsed = urlparse(r.url)
                if root in parsed.netloc:
                    return f"{parsed.scheme}://{parsed.netloc}/"
            return None
        except:
            return None

    print(f"[SUBDOMAIN] Checking {len(COMMON_SUBDOMAINS)} subdomains for {root}...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_subdomain, sub): sub for sub in COMMON_SUBDOMAINS}
        for future in as_completed(futures, timeout=25):
            try:
                result = future.result()
                if result:
                    subdomains.append(result)
                    print(f"[SUBDOMAIN] Found: {result}")
            except:
                pass

    unique = list(set(subdomains))
    print(f"[SUBDOMAIN] Total found: {len(unique)}")
    return unique

def get_sitemap_urls(domain, session):
    urls = set()
    sitemaps = [
        f"https://{domain}/sitemap.xml",
        f"https://{domain}/sitemap_index.xml",
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
    return list(urls)[:20]

def get_robots_paths(domain, session):
    paths = []
    try:
        r = safe_get(f"https://{domain}/robots.txt", session)
        if r:
            for line in r.text.split("\n"):
                line = line.strip()
                if line.lower().startswith("sitemap:"):
                    paths.append(line.split(":", 1)[1].strip())
                elif line.lower().startswith("allow:") or line.lower().startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path and path != "/" and "*" not in path:
                        paths.append(f"https://{domain}{path}")
    except:
        pass
    return paths

def crawl_batch(to_visit, domain, max_pages, log):
    pages_data = []
    visited = set()
    crawled = 0
    i = 0

    while i < len(to_visit) and crawled < max_pages:
        batch = []
        while len(batch) < 5 and i < len(to_visit):
            url = to_visit[i]
            i += 1
            if url not in visited:
                visited.add(url)
                batch.append(url)

        if not batch:
            break

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_url_parallel, url): url for url in batch}
            for future in as_completed(futures, timeout=15):
                try:
                    url, content = future.result()
                    if content:
                        log(f"[ok] {url}")
                        pages_data.append({"url": url, "content": content})
                        crawled += 1
                        new_links = get_links(url, content, domain)
                        # Sort by priority score so contact/support pages crawled first
                        scored_new = sorted(new_links, key=score_link, reverse=True)
                        for link in scored_new[:20]:  # max 20 new links per page
                            if link not in visited and link not in to_visit:
                                to_visit.insert(crawled + 1, link)  # insert at front
                    else:
                        log(f"[skip] {url}")
                except:
                    pass

        if crawled >= max_pages:
            break

    return pages_data

def crawl(domain, log_callback=None, scan_subdomains=True):
    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    log(f"[CRAWLER v4.0] Starting crawl for {domain}")
    session = get_session()

    SPA_PLATFORMS = ["vercel.app", "netlify.app", "github.io", "pages.dev", "herokuapp.com"]
    is_spa = any(p in domain for p in SPA_PLATFORMS)
    log(f"[CRAWLER] Domain type: {'SPA' if is_spa else 'NORMAL'}")

    pages_data = []

    if is_spa:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox","--disable-gpu"])
                page = browser.new_page()
                page.goto(f"https://{domain}/", timeout=10000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                content = page.content()
                browser.close()
                pages_data.append({"url": f"https://{domain}/", "content": content})
        except:
            r = safe_get(f"https://{domain}/", session)
            if r:
                pages_data.append({"url": f"https://{domain}/", "content": r.text})
    else:
        # Step 1: Discover subdomains
        if scan_subdomains:
            subdomains = discover_subdomains(domain, session)
        else:
            subdomains = []
            log('[CRAWLER] Subdomain scan skipped - main domain only')

        # Step 2: Build URL list — main domain + all subdomains
        to_visit = []
        parts = domain.split(".")
        root = ".".join(parts[-2:]) if len(parts) > 2 else domain
        all_bases = [f"https://{domain}", f"https://www.{domain}"] + [s.rstrip("/") for s in subdomains]
        # Remove duplicates
        seen_bases = set()
        unique_bases = []
        for b in all_bases:
            if b not in seen_bases:
                seen_bases.add(b)
                unique_bases.append(b)

        # Only apply seed paths to main domain, not every subdomain
        for path in SEED_PATHS:
            to_visit.append(f"https://{domain}{path}")
        # For subdomains just add root URL
        for base in subdomains:
            to_visit.append(base.rstrip("/") + "/")

        # Step 3: Sitemap + robots
        sitemap_urls = get_sitemap_urls(domain, session)
        to_visit.extend(sitemap_urls)
        robots_paths = get_robots_paths(domain, session)
        to_visit.extend(robots_paths)

        # Deduplicate
        seen = set()
        deduped = []
        for url in to_visit:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        to_visit = deduped

        log(f"[CRAWLER] Queued {len(to_visit)} URLs across {len(unique_bases)} domains/subdomains")

        # Step 4: Crawl with 30 parallel workers
        pages_data = crawl_batch(to_visit, root, MAX_PAGES_PER_DOMAIN, log)

    log(f"[CRAWLER] Done - {len(pages_data)} pages crawled")
    return pages_data















