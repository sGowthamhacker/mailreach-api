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
    # Core
    "www", "mail", "email", "webmail", "smtp", "imap", "pop", "mx",
    # Support/Help
    "help", "support", "helpdesk", "kb", "docs", "documentation",
    "faq", "helpcentre", "helpcenter", "care", "assist",
    "customer", "customerservice", "customersupport",
    "service", "services", "ticket", "tickets",
    "techsupport", "technical", "knowledgebase",
    # Blog/News/Press
    "blog", "news", "press", "media", "newsroom", "pr",
    "editorial", "content", "publish", "magazine",
    "journal", "newsletter", "updates", "releases",
    # About/Company
    "about", "team", "company", "corporate", "corp",
    "careers", "jobs", "hiring", "recruit", "recruitment",
    "talent", "people", "hr", "humanresources",
    "internship", "intern", "graduate", "apply",
    # Contact
    "contact", "info", "hello", "reach", "connect", "touch",
    "enquiry", "inquiry", "feedback", "message",
    "say-hello", "get-in-touch", "talk",
    # Security/Trust
    "security", "trust", "privacy", "legal", "compliance",
    "gdpr", "dpo", "abuse", "spam", "phishing", "fraud",
    "risk", "safety", "report", "disclosure",
    "bounty", "bugbounty", "vdp", "bbp", "psirt",
    "csirt", "cert", "vulnerability", "pentest",
    "responsible", "infosec", "cybersecurity",
    # Developer/API
    "developer", "developers", "dev", "api", "apis",
    "platform", "engineering", "tech", "technology",
    "infrastructure", "devops", "sre", "noc", "ops",
    "infra", "backend", "frontend", "mobile",
    "open", "opensource", "github", "gitlab",
    "sdk", "cli", "tools", "tool",
    # Status/Monitor
    "status", "uptime", "monitor", "health", "ping",
    "monitoring", "alert", "alerting", "metrics",
    "stats", "analytics", "data", "insights",
    # Community/Social
    "community", "forum", "forums", "discuss",
    "chat", "slack", "discord", "social",
    "network", "connect", "hub",
    # Partners/Business
    "partners", "partner", "affiliate", "affiliates",
    "reseller", "resellers", "channel", "distribution",
    "ecosystem", "marketplace", "wholesale",
    "enterprise", "business", "corp", "corporate",
    "investors", "ir", "investor", "shareholders",
    # Commerce/Shop
    "shop", "store", "checkout", "cart", "buy", "order",
    "ecommerce", "commerce", "market", "billing",
    "payments", "pay", "payment", "invoice",
    "finance", "accounting", "subscription",
    # App/Mobile
    "app", "mobile", "m", "wap", "ios", "android",
    # CDN/Static
    "cdn", "static", "assets", "img", "images",
    "files", "download", "downloads", "storage",
    "upload", "uploads", "ftp", "backup", "archive",
    # Admin/Portal
    "admin", "portal", "dashboard", "panel", "console",
    "manage", "management", "control", "cp", "cpanel",
    "account", "accounts", "profile", "user", "users",
    "login", "signin", "signup", "register", "auth",
    "sso", "id", "identity", "oauth",
    # Learning
    "learn", "learning", "training", "academy",
    "education", "courses", "course", "workshop",
    "certification", "university", "school",
    # Events
    "events", "conference", "meetup", "webinar",
    "summit", "expo", "live",
    # Marketing/Sales
    "marketing", "sales", "crm", "leads",
    "advertising", "ads", "campaigns", "brand",
    "creative", "design", "ux", "ui",
    "growth", "seo", "content", "editorial",
    # Cloud/Infrastructure
    "cloud", "aws", "azure", "gcp", "hosting",
    "saas", "paas", "iaas", "edge", "gateway",
    "proxy", "vpn", "ssl", "secure", "remote",
    "intranet", "internal", "extranet",
    "network", "net", "dns", "vpn",
    # Research/Labs
    "research", "labs", "lab", "innovation",
    "rd", "science", "explore",
    # Environment/Staging
    "staging", "stage", "uat", "qa", "test",
    "demo", "sandbox", "beta", "alpha",
    "preview", "next", "new", "old", "legacy",
    "v1", "v2", "v3", "prod", "production",
    # HR/People
    "hr", "humanresources", "people", "talent",
    "culture", "diversity", "inclusion",
    # Legal/Compliance
    "legal", "contracts", "compliance", "dpa",
    "privacy", "gdpr", "ccpa", "dmca",
    # Finance
    "finance", "billing", "payments", "invoice",
    "accounting", "payroll", "treasury",
    # CSR
    "csr", "sustainability", "green", "environment",
    "foundation", "charity", "nonprofit", "giving",
    "volunteer", "social-impact",
    # Regional - Countries
    "us", "uk", "eu", "in", "au", "ca", "de",
    "fr", "jp", "cn", "br", "mx", "es", "it",
    "nl", "se", "no", "dk", "fi", "ch", "at",
    "be", "pl", "ru", "za", "sg", "hk", "kr",
    "nz", "ie", "pt", "gr", "cz", "ro", "hu",
    # Regional - Regions
    "asia", "apac", "emea", "latam", "amer",
    "east", "west", "north", "south",
    "global", "international", "worldwide",
    # Cities
    "ny", "nyc", "la", "sf", "chicago", "boston",
    "london", "paris", "berlin", "tokyo", "sydney",
    "toronto", "dubai", "singapore", "amsterdam",
    # Executive
    "ceo", "cto", "cfo", "coo", "ciso",
    "board", "exec", "executives", "founders",
    "office", "offices", "hq", "headquarters",
    # Other useful
    "wiki", "knowledge", "base", "search",
    "find", "discover", "explore", "map", "maps",
    "location", "locations", "directory",
    "pro", "premium", "plus", "elite", "free",
    "trial", "freemium", "pricing",
    "home", "main", "index", "root",
    "ping", "pong", "test", "check",
    "verify", "validate", "confirm",
    "log", "logs", "audit", "reports",
    "webhook", "hooks", "integrations",
    "plugin", "plugins", "extension", "extensions",
    "notification", "notifications", "alerts",
    "broadcast", "announce", "announcement",
    "release", "releases", "changelog",
    "roadmap", "ideas", "vision",
    "trust", "trustcenter", "compliance",
    "onboarding", "welcome", "start",
    "success", "customer-success",
    "professional", "pro-services",
    "consulting", "implementation",
    "solution", "solutions",
]

SEED_PATHS = [
    # Core pages
    "/", "/contact", "/about", "/team", "/security",
    "/support", "/help", "/contact-us", "/about-us",
    "/robots.txt", "/humans.txt", "/sitemap.xml",
    "/security.txt", "/.well-known/security.txt",
    "/.well-known/pgp-key.txt",
    # Contact variations
    "/contact_us", "/contactus", "/contact-form",
    "/get-in-touch", "/getintouch", "/reach-us", "/reach",
    "/connect", "/hello", "/say-hello", "/talk-to-us",
    "/message", "/email", "/email-us", "/mail",
    "/inquiry", "/inquiries", "/enquiry", "/enquiries",
    "/feedback", "/write-to-us", "/get-help", "/ask",
    "/request", "/touch", "/ping",
    # About variations
    "/about_us", "/aboutus", "/our-story", "/ourstory",
    "/who-we-are", "/whoweare", "/overview", "/mission",
    "/vision", "/values", "/culture", "/story",
    # Team/People
    "/our-team", "/ourteam", "/people", "/staff",
    "/crew", "/members", "/leadership", "/leaders",
    "/management", "/executives", "/exec",
    "/founders", "/founder", "/board", "/advisors",
    "/directors", "/officers", "/president",
    "/ceo", "/cto", "/cfo", "/ciso", "/coo",
    # Company
    "/company", "/corporate", "/organization",
    "/organisation", "/hq", "/headquarters",
    "/offices", "/locations", "/office", "/global",
    # Security/Disclosure
    "/security-policy", "/security-team",
    "/responsible-disclosure", "/vulnerability-disclosure",
    "/coordinated-disclosure", "/disclosure",
    "/bug-bounty", "/bugbounty", "/bug_bounty",
    "/vdp", "/bbp", "/cvd", "/psirt", "/csirt",
    "/cert", "/hackerone", "/bugcrowd", "/intigriti",
    "/hall-of-fame", "/halloffame", "/hof",
    "/pentest", "/penetration-testing",
    "/report-vulnerability", "/report-a-bug",
    "/security/contact", "/security/report",
    "/security/disclosure", "/security/vulnerabilities",
    "/security/advisories", "/security/pgp",
    "/trust", "/trust-center", "/trustcenter",
    "/safety", "/abuse", "/fraud", "/risk",
    "/phishing", "/spam", "/report",
    "/pgp", "/pgp-key", "/gpg", "/keybase", "/keys",
    # Legal/Privacy
    "/legal", "/privacy", "/privacy-policy",
    "/privacypolicy", "/terms", "/terms-of-service",
    "/termsofservice", "/tos", "/eula", "/dmca",
    "/impressum", "/imprint", "/disclaimer",
    "/cookie-policy", "/cookies", "/data-protection",
    "/compliance", "/gdpr", "/dpa", "/ccpa",
    "/subprocessors", "/data-processing",
    # Press/Media
    "/press", "/media", "/newsroom", "/news",
    "/press-kit", "/presskit", "/press-room",
    "/press-releases", "/media-kit", "/media-room",
    "/journalists", "/reporters", "/pr",
    "/communications", "/brand",
    # Careers/Jobs
    "/careers", "/jobs", "/hiring", "/join",
    "/join-us", "/work-with-us", "/work-for-us",
    "/opportunities", "/openings", "/positions",
    "/recruiting", "/recruitment", "/talent",
    "/hr", "/human-resources", "/people-team",
    "/internship", "/intern", "/graduate", "/apply",
    # Support/Help
    "/helpdesk", "/help-center", "/helpcenter",
    "/knowledge-base", "/knowledgebase",
    "/faq", "/faqs", "/documentation",
    "/customer-support", "/customersupport",
    "/customer-service", "/customerservice",
    "/customer-care", "/customercare",
    "/technical-support", "/tickets", "/issues",
    # Sales/Business
    "/sales", "/business", "/enterprise",
    "/contact/sales", "/partnerships", "/partners",
    "/partner", "/affiliates", "/affiliate",
    "/resellers", "/reseller", "/wholesale",
    "/vendors", "/vendor", "/suppliers",
    # Finance/Billing
    "/billing", "/payments", "/invoice",
    "/accounting", "/finance", "/subscriptions",
    # Investors
    "/investors", "/investor-relations", "/ir",
    "/investor", "/shareholders", "/governance",
    # Developer/API
    "/developer", "/developers", "/dev",
    "/api", "/api-support", "/developer-support",
    "/platform", "/engineering", "/tech",
    "/open-source", "/opensource",
    # Community
    "/community", "/forum", "/forums",
    "/newsletter", "/subscribe", "/updates",
    "/events", "/webinars", "/social",
    # Marketing
    "/marketing", "/advertising", "/ads",
    "/sponsorship", "/design", "/creative",
    # CSR/Other
    "/csr", "/sustainability", "/foundation",
    "/charity", "/giving", "/volunteer",
    "/accessibility", "/diversity",
    # Regional
    "/en/contact", "/en/about", "/en/security",
    "/us/contact", "/uk/contact", "/eu/contact",
    # Extra
    "/status", "/feedback", "/ideas", "/demo",
    "/onboarding", "/getting-started",
    "/abuse-report", "/report-abuse",
    "/data-request", "/data-deletion",
    "/warranty", "/returns", "/refunds",
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

SKIP_PATTERNS = [
    "/templates/", "/template/", "/blog/", "/changelog/",
    "/docs/", "/pricing", "/workflows", "/startups",
    "/solutions/", "/new/", "/try-", "/enterprise",
]

def fetch_url_parallel(url):
    try:
        # Skip pages unlikely to have emails
        url_lower = url.lower()
        if any(p in url_lower for p in SKIP_PATTERNS):
            return url, None
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
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(check_subdomain, sub): sub for sub in COMMON_SUBDOMAINS}
        for future in as_completed(futures, timeout=60):
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
    return list(urls)[:100]

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
        while len(batch) < 10 and i < len(to_visit):
            url = to_visit[i]
            i += 1
            if url not in visited:
                visited.add(url)
                batch.append(url)

        if not batch:
            break

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(fetch_url_parallel, url): url for url in batch}
            for future in as_completed(futures, timeout=60):
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

        # Apply seed paths to main domain
        for path in SEED_PATHS:
            to_visit.append(f"https://{domain}{path}")
        # For subdomains apply key seed paths too
        KEY_PATHS = [
            "/", "/contact", "/about", "/security", "/support",
            "/help", "/team", "/press", "/legal", "/privacy",
            "/disclosure", "/bug-bounty", "/vdp", "/trust",
            "/abuse", "/compliance", "/careers", "/investors",
            "/security.txt", "/.well-known/security.txt",
            "/humans.txt", "/robots.txt",
        ]
        for base in subdomains:
            base = base.rstrip("/")
            for path in KEY_PATHS:
                to_visit.append(f"{base}{path}")

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

        if not scan_subdomains:
            to_visit = [u for u in to_visit if u.split("/")[2].replace("www.","") == domain]
            log("[CRAWLER] Subdomain URLs filtered - main domain only")
        log(f"[CRAWLER] Queued {len(to_visit)} URLs across {len(unique_bases)} domains/subdomains")

        # Step 4: Crawl with 30 parallel workers
        max_pages = MAX_PAGES_PER_DOMAIN * 2 if scan_subdomains else MAX_PAGES_PER_DOMAIN
        log(f"[CRAWLER] Max pages: {max_pages} (subdomain={scan_subdomains})")
        pages_data = crawl_batch(to_visit, root, max_pages, log)

    log(f"[CRAWLER] Done - {len(pages_data)} pages crawled")
    return pages_data






























