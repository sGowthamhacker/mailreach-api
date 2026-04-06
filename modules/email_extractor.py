import re
import sys
import json
import requests
from bs4 import BeautifulSoup
from config import EMAIL_PREFIXES

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

EMAIL_PATTERNS = {
    "primary": r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    "obfuscated_at": r'([a-zA-Z0-9._\-]+)\s+at\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
    "obfuscated_bracket": r'([a-zA-Z0-9._\-]+)\s*\[\s*at\s*\]\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
    "obfuscated_space": r'([a-zA-Z0-9._\-]+)\s+\(\s*at\s*\)\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
}

def is_fake_email(email):
    if not email or "@" not in email:
        return True
    try:
        prefix, domain = email.rsplit("@", 1)
    except:
        return True
    domain = domain.lower().strip()
    prefix = prefix.lower().strip()
    FAKE_DOMAINS = {
        "example.com", "example.org", "example.net",
        "test.com", "test.org", "test.net",
        "fake.com", "fake.org", "fake.net",
        "domain.com", "email.com", "yoursite.com", "website.com",
        "sentry.io", "w3.org", "schema.org", "googleapis.com",
        "gstatic.com", "cloudflare.com", "localhost", "127.0.0.1",
        "github.com", "github.io", "gitlab.com", "bitbucket.org",
    }
    if domain in FAKE_DOMAINS:
        return True
    LIBRARY_NAMES = {
        "react", "redux", "angular", "vue", "node", "npm", "webpack",
        "babel", "eslint", "prettier", "jest", "mocha", "chai",
        "lodash", "axios", "express", "django", "flask", "spring",
        "bootstrap", "tailwind", "material", "semantic", "bulma",
        "jquery", "backbone", "ember", "svelte", "nextjs", "nuxt",
        "typescript", "javascript", "python", "java", "golang",
    }
    if prefix in LIBRARY_NAMES:
        return True
    if any(ext in prefix for ext in [".png", ".jpg", ".svg", ".gif", ".webp", ".pdf"]):
        return True
    if "://" in email or email.count("/") > 1:
        return True
    if len(prefix) < 2:
        return True
    if prefix.isdigit():
        return True
    if domain.startswith("window.") or domain.startswith("this.") or domain.startswith("self."):
        return True
    if domain.count(".") > 3:
        return True
    return False


def extract_emails_from_text(text, source="text"):
    found = set()
    if not text or len(text) < 5:
        return list(found)
    primary = re.findall(EMAIL_PATTERNS["primary"], text)
    if primary:
        found.update(primary)
    obf_at = re.findall(EMAIL_PATTERNS["obfuscated_at"], text, re.IGNORECASE)
    if obf_at:
        for name, domain in obf_at:
            found.add(f"{name}@{domain}")
    obf_bracket = re.findall(EMAIL_PATTERNS["obfuscated_bracket"], text, re.IGNORECASE)
    if obf_bracket:
        for name, domain in obf_bracket:
            found.add(f"{name}@{domain}")
    obf_space = re.findall(EMAIL_PATTERNS["obfuscated_space"], text, re.IGNORECASE)
    if obf_space:
        for name, domain in obf_space:
            found.add(f"{name}@{domain}")
    clean = set()
    for email in found:
        email = email.strip(".,;:\"'><)([]{}`|\\")
        if "@" not in email or email.count("@") > 1:
            continue
        parts = email.split("@")
        if len(parts) != 2:
            continue
        prefix, domain = parts
        if len(prefix) < 2 or len(domain) < 5:
            continue
        if "." not in domain:
            continue
        clean.add(email.lower())
    return list(clean)


def extract_mailto_links(html):
    emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        mailto_links = soup.find_all("a", href=re.compile(r'^mailto:', re.IGNORECASE))
        for link in mailto_links:
            href = link.get("href", "").lower()
            email_match = re.search(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', href)
            if email_match:
                email = email_match.group(1).lower().strip()
                if not is_fake_email(email):
                    emails.add(email)
    except Exception as e:
        print(f"[mailto] Error: {e}")
    return list(emails)


def extract_from_html(content):
    all_emails = set()
    try:
        mailto_emails = extract_mailto_links(content)
        all_emails.update(mailto_emails)
        text_emails = extract_emails_from_text(content, source="html-text")
        all_emails.update(text_emails)
        soup = BeautifulSoup(content, "html.parser")
        for meta in soup.find_all("meta"):
            content_val = meta.get("content", "")
            if content_val and "@" in content_val:
                found = extract_emails_from_text(content_val, source="html-meta")
                all_emails.update(found)
        for tag in soup.find_all(True):
            for attr, val in tag.attrs.items():
                if isinstance(val, str) and "@" in val and len(val) < 200:
                    found = extract_emails_from_text(val, source="html-attr")
                    all_emails.update(found)
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                try:
                    json_str = json.dumps(json.loads(script.string))
                    found = extract_emails_from_text(json_str, source="html-jsonld")
                    all_emails.update(found)
                except:
                    pass
    except Exception as e:
        print(f"[HTML] Error: {e}")
    return [e for e in all_emails if not is_fake_email(e)]


def extract_from_js_files(domain, html):
    all_emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script")

        # Inline scripts
        for script in scripts:
            if script.string and len(script.string) > 50:
                found = extract_emails_from_text(script.string, source="js-inline")
                all_emails.update(found)

        # External JS URLs
        js_urls = set()
        for script in scripts:
            src = script.get("src")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("http"):
                pass
            elif src.startswith("/"):
                src = f"https://{domain}{src}"
            else:
                src = f"https://{domain}/{src}"
            js_urls.add(src)

        # Priority scoring
        def priority_score(url):
            url_lower = url.lower()
            if "_next/static" in url_lower or "/_next/" in url_lower:
                return 100000
            elif any(x in url_lower for x in ["app.", "main.", "bundle.", "index."]):
                return 10000
            elif "vendor" not in url_lower:
                return 1000
            return -1000

        js_list = sorted(list(js_urls), key=priority_score, reverse=True)
        print(f"[JS] Scanning {len(js_list)} JS files in parallel...")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        def fetch_and_scan(js_url):
            try:
                r = requests.get(js_url, headers=HEADERS, timeout=8, verify=False)
                if r.status_code != 200:
                    return []
                if len(r.text) > 5000000:
                    return []
                return extract_emails_from_text(r.text, source="js-file")
            except:
                return []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_and_scan, url): url for url in js_list}
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    all_emails.update(result)
                except:
                    pass

    except Exception as e:
        print(f"[JS] Error: {e}")
    return list(all_emails)


def fetch_public_sources(domain):
    emails = set()

    # 1. crt.sh
    try:
        r = requests.get(
            f"https://crt.sh/?q=%40{domain}&output=json",
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            for entry in data[:100]:
                name = entry.get("name_value", "")
                found = extract_emails_from_text(name, source="crt.sh")
                emails.update(found)
            print(f"[crt.sh] Found {len(emails)} emails")
    except Exception as e:
        print(f"[crt.sh] Error: {e}")

    # 2. WHOIS
    try:
        import whois
        w = whois.whois(domain)
        found = extract_emails_from_text(str(w), source="whois")
        emails.update(found)
        print(f"[whois] Found {len(found)} emails")
    except Exception as e:
        print(f"[whois] Error: {e}")

    # 3. Wayback Machine
    try:
        r = requests.get(
            f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&limit=20",
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            urls = r.json()
            for item in urls[1:10]:
                try:
                    page = requests.get(item[0], headers=HEADERS, timeout=5, verify=False)
                    if page.status_code == 200:
                        found = extract_emails_from_text(page.text, source="wayback")
                        emails.update(found)
                except:
                    pass
        print(f"[wayback] Total: {len(emails)} emails")
    except Exception as e:
        print(f"[wayback] Error: {e}")

    # 4. Common patterns (200+)
    COMMON_PREFIXES = [
        "support", "info", "contact", "hello", "help",
        "security", "legal", "privacy", "admin", "cs",
        "helpdesk", "customerservice", "customer_service",
        "mobile_support", "sales", "billing", "abuse",
        "webmaster", "team", "noreply", "no-reply",
        "press", "media", "pr", "marketing", "hr",
        "jobs", "careers", "recruiting", "talent",
        "finance", "accounting", "payments", "invoice",
        "partners", "partnerships", "business", "corp",
        "enterprise", "wholesale", "reseller",
        "api", "developer", "developers", "dev",
        "feedback", "suggestions", "ideas",
        "community", "forum", "social",
        "newsletter", "alerts", "notifications",
        "compliance", "gdpr", "dpo", "data",
        "trust", "safety", "fraud", "risk",
        "operations", "ops", "engineering",
        "it", "sysadmin", "network", "infra",
        "ceo", "cto", "cfo", "coo", "founder",
        "office", "headquarters", "hq",
        "general", "enquiries", "enquiry",
        "service", "services", "solutions",
        "technical", "tech", "helpline",
        "reception", "secretary", "assistant",
        "booking", "reservations", "appointments",
        "emergency", "urgent", "priority",
        "report", "reports", "reporting",
        "audit", "compliance", "legal",
        "procurement", "purchasing", "supply",
        "logistics", "shipping", "delivery",
        "returns", "refunds", "warranty",
        "training", "education", "learning",
        "research", "analytics", "data",
        "design", "creative", "brand",
        "content", "editorial", "publishing",
        "events", "conference", "webinar",
        "sponsorship", "advertising", "ads",
        "affiliate", "referral", "rewards",
        "investor", "investors", "ir",
        "board", "directors", "governance",
        "charity", "foundation", "giving",
        "volunteer", "internship", "intern",
    ]

    root_domain = domain
    parts = domain.split(".")
    if len(parts) > 2:
        root_domain = ".".join(parts[-2:])

    for prefix in COMMON_PREFIXES:
        emails.add(f"{prefix}@{domain}")
        if root_domain != domain:
            emails.add(f"{prefix}@{root_domain}")

    print(f"[patterns] Added pattern emails for {domain}")
    print(f"[public] Total: {len(emails)} emails")
    return list(emails)


def extract_all(domain, pages_data):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    all_emails = set()

    print(f"\n[EXTRACT] Starting extraction from {len(pages_data)} pages")

    # Step 1: Public sources ONCE
    print(f"[EXTRACT] Fetching public sources...")
    public_emails = fetch_public_sources(domain)
    all_emails.update(public_emails)
    print(f"[EXTRACT] Public: {len(public_emails)} emails")

    # Step 2: Identify priority pages
    PRIORITY_KEYWORDS = ["contact", "about", "security", "team", "help", "support"]
    priority_pages = []
    normal_pages = []
    for page in pages_data:
        url = page.get("url", "").lower()
        if any(k in url for k in PRIORITY_KEYWORDS):
            priority_pages.append(page)
        else:
            normal_pages.append(page)

    homepage = [p for p in pages_data if p.get("url", "").rstrip("/").endswith(domain)]
    deep_scan_pages = homepage[:1] + priority_pages[:4]
    quick_scan_pages = [p for p in pages_data if p not in deep_scan_pages]

    print(f"[EXTRACT] Deep scan: {len(deep_scan_pages)} pages (HTML+JS)")
    print(f"[EXTRACT] Quick scan: {len(quick_scan_pages)} pages (HTML only)")

    # Step 3: Deep scan (HTML + JS)
    def deep_process(page):
        content = page.get("content", "")
        if not content:
            return []
        result = set()
        result.update(extract_from_html(content))
        if "<script" in content:
            result.update(extract_from_js_files(domain, content))
        return list(result)

    # Step 4: Quick scan (HTML only)
    def quick_process(page):
        content = page.get("content", "")
        if not content:
            return []
        return extract_from_html(content)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(deep_process, page): page for page in deep_scan_pages}
        for future in as_completed(futures, timeout=60):
            try:
                all_emails.update(future.result())
            except Exception as e:
                print(f"[EXTRACT] Deep error: {e}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(quick_process, page): page for page in quick_scan_pages}
        for future in as_completed(futures, timeout=30):
            try:
                all_emails.update(future.result())
            except Exception as e:
                print(f"[EXTRACT] Quick error: {e}")

    # Step 5: Filter
    real_emails = [e for e in sorted(all_emails) if not is_fake_email(e)]
    print(f"[FINAL] Total: {len(all_emails)} | Real: {len(real_emails)}")
    return real_emails