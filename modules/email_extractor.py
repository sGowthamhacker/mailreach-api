import re
import sys
import json
import requests
from bs4 import BeautifulSoup
from config import EMAIL_PREFIXES

sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
}

EMAIL_REGEX = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"

FAKE_DOMAINS = {
    "example.com","example.org","example.net","test.com","test.org",
    "fake.com","domain.com","email.com","yoursite.com","website.com",
    "sentry.io","w3.org","schema.org","googleapis.com","gstatic.com",
    "cloudflare.com","localhost","github.com","github.io","gitlab.com",
    "wixpress.com","squarespace.com","shopify.com","wordpress.com",
    "jquery.com","bootstrap.com","npmjs.com","unpkg.com","cdnjs.com",
}

FAKE_PREFIXES = {
    "react","redux","angular","vue","node","npm","webpack","babel",
    "eslint","prettier","jest","lodash","axios","express","django",
    "flask","bootstrap","tailwind","jquery","typescript","javascript",
    "python","java","golang","noreply","no-reply","donotreply",
}

def is_fake_email(email):
    if not email or "@" not in email:
        return True
    try:
        prefix, domain = email.lower().rsplit("@", 1)
    except:
        return True
    if domain in FAKE_DOMAINS:
        return True
    if prefix in FAKE_PREFIXES:
        return True
    if any(ext in prefix for ext in [".png",".jpg",".svg",".gif",".pdf",".css"]):
        return True
    if "://" in email or email.count("/") > 1:
        return True
    if len(prefix) < 2 or prefix.isdigit():
        return True
    if domain.startswith(("window.","this.","self.","document.")):
        return True
    if domain.count(".") > 4:
        return True
    if len(domain) > 50:
        return True
    return False

def extract_emails_from_text(text):
    if not text:
        return set()
    found = set()
    for email in re.findall(EMAIL_REGEX, text):
        email = email.strip(".,;:\"'><)([]{}`|\\").lower()
        if not is_fake_email(email):
            found.add(email)
    # obfuscated: name at domain.com
    for name, domain in re.findall(r"([a-zA-Z0-9._\-]+)\s+at\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text, re.I):
        email = f"{name}@{domain}".lower()
        if not is_fake_email(email):
            found.add(email)
    # obfuscated: name [at] domain.com
    for name, domain in re.findall(r"([a-zA-Z0-9._\-]+)\s*\[at\]\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text, re.I):
        email = f"{name}@{domain}".lower()
        if not is_fake_email(email):
            found.add(email)
    return found

def extract_from_html(content, domain):
    emails = set()
    if not content:
        return emails
    try:
        soup = BeautifulSoup(content, "html.parser")
        # mailto links - most reliable
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().startswith("mailto:"):
                m = re.search(EMAIL_REGEX, href)
                if m:
                    email = m.group(0).lower()
                    if not is_fake_email(email):
                        emails.add(email)
        # page text
        emails.update(extract_emails_from_text(soup.get_text(" ")))
        # meta tags
        for meta in soup.find_all("meta"):
            val = meta.get("content","")
            if "@" in val:
                emails.update(extract_emails_from_text(val))
        # JSON-LD structured data
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                emails.update(extract_emails_from_text(script.string))
        # inline scripts
        for script in soup.find_all("script"):
            if script.string and "@" in (script.string or ""):
                emails.update(extract_emails_from_text(script.string))
    except Exception as e:
        print(f"[HTML] Error: {e}")
    # filter to only keep emails matching the target domain
    target_parts = domain.split(".")
    root = ".".join(target_parts[-2:]) if len(target_parts) > 1 else domain
    return {e for e in emails if root in e.split("@")[1]}

def fetch_js_emails(domain, html):
    emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        js_urls = []
        for script in soup.find_all("script", src=True):
            src = script["src"]
            if src.startswith("//"): src = "https:" + src
            elif src.startswith("/"): src = f"https://{domain}{src}"
            elif not src.startswith("http"): src = f"https://{domain}/{src}"
            js_urls.append(src)

        # only scan small JS files likely to have emails
        def scan_js(url):
            try:
                r = requests.get(url, headers=HEADERS, timeout=5, verify=False)
                if r.status_code == 200 and len(r.text) < 2000000:
                    return extract_emails_from_text(r.text)
            except:
                pass
            return set()

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(scan_js, u) for u in js_urls[:10]]
            for f in as_completed(futures, timeout=20):
                try:
                    emails.update(f.result())
                except:
                    pass
    except Exception as e:
        print(f"[JS] Error: {e}")
    target_parts = domain.split(".")
    root = ".".join(target_parts[-2:]) if len(target_parts) > 1 else domain
    return {e for e in emails if root in e.split("@")[1]}

def fetch_public_sources(domain):
    emails = set()
    target_parts = domain.split(".")
    root = ".".join(target_parts[-2:]) if len(target_parts) > 1 else domain

    # crt.sh - real emails from SSL certs
    try:
        r = requests.get(f"https://crt.sh/?q=%40{root}&output=json", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            for entry in r.json()[:50]:
                name = entry.get("name_value","")
                for e in extract_emails_from_text(name):
                    if root in e.split("@")[1]:
                        emails.add(e)
        print(f"[crt.sh] {len(emails)} emails")
    except Exception as e:
        print(f"[crt.sh] Error: {e}")

    # WHOIS - real registration emails
    try:
        import whois
        w = whois.whois(root)
        for e in extract_emails_from_text(str(w)):
            if root in e.split("@")[1]:
                emails.add(e)
        print(f"[whois] {len(emails)} emails")
    except Exception as e:
        print(f"[whois] Error: {e}")

    print(f"[public] Total real emails: {len(emails)}")
    return emails

def extract_all(domain, pages_data):
    all_emails = set()
    print(f"\n[EXTRACT] {len(pages_data)} pages to scan for {domain}")

    # Step 1: Real public sources only (no fake patterns)
    all_emails.update(fetch_public_sources(domain))

    # Step 2: Extract from each crawled page
    for page in pages_data:
        url = page.get("url","")
        content = page.get("content","")
        if not content:
            continue
        page_emails = extract_from_html(content, domain)
        if page_emails:
            print(f"[page] {url} -> {len(page_emails)} emails")
        all_emails.update(page_emails)
        # JS scan only for homepage and contact pages
        if any(k in url.lower() for k in ["contact","about","security","support",domain.split(".")[0]]):
            js_emails = fetch_js_emails(domain, content)
            if js_emails:
                print(f"[js] {url} -> {len(js_emails)} emails")
            all_emails.update(js_emails)

    real = [e for e in all_emails if not is_fake_email(e)]
    print(f"[EXTRACT] Done - {len(real)} real emails found")
    return real