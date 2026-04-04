import re 
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import EMAIL_PREFIXES

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

FAKE_DOMAINS = [
    "example.com", "example.org", "test.com",
    "fake.com", "domain.com", "email.com",
    "yoursite.com", "website.com"
]

FAKE_PREFIXES = [
    "jane.doe", "john.doe", "guest",
    "you", "new.email", "user", "someone"
]

def is_fake_email(email):
    domain = email.split("@")[1].lower()
    prefix = email.split("@")[0].lower()
    if domain in FAKE_DOMAINS:
        return True
    if prefix in FAKE_PREFIXES:
        return True
    return False

def extract_emails_from_text(text):
    found = re.findall(EMAIL_REGEX, text)
    return [e for e in found if not is_fake_email(e)]

def get_js_files(domain, html):
    soup = BeautifulSoup(html, "html.parser")
    js_files = []
    for tag in soup.find_all("script", src=True):
        src = tag["src"]
        if src.startswith("http"):
            # Only get JS from same domain
            if domain in src:
                js_files.append(src)
        else:
            js_files.append(f"https://{domain}{src}")
    return js_files

def extract_from_js_files(domain, html):
    emails = set()
    js_files = get_js_files(domain, html)
    print(f"  [js] found {len(js_files)} JS files to scan")

    for js_url in js_files:
        try:
            r = requests.get(js_url, headers=HEADERS, timeout=10)
            found = extract_emails_from_text(r.text)
            if found:
                print(f"  [js] ✅ {len(found)} emails in {js_url}")
                emails.update(found)
        except:
            pass
    return list(emails)

def extract_from_html(content):
    emails = set()
    try:
        # Raw text search
        found = extract_emails_from_text(content)
        emails.update(found)

        soup = BeautifulSoup(content, "html.parser")

        # mailto links
        for tag in soup.find_all("a", href=True):
            if "mailto:" in tag["href"]:
                email = tag["href"].replace("mailto:", "").strip()
                if not is_fake_email(email):
                    emails.add(email)

        # data attributes
        for tag in soup.find_all(True):
            for attr, val in tag.attrs.items():
                if isinstance(val, str) and "@" in val:
                    found = extract_emails_from_text(val)
                    emails.update(found)
    except:
        pass
    return list(emails)

def guess_emails(domain):
    # For subdomains like vercel.app get root domain
    parts = domain.split(".")
    if len(parts) > 2:
        # htwth.vercel.app → skip guessing on vercel.app
        if any(host in domain for host in ["vercel.app", "netlify.app", "github.io"]):
            return []
    return [f"{prefix}@{domain}" for prefix in EMAIL_PREFIXES]

def extract_all(domain, pages_data):
    all_emails = set()

    for page in pages_data:
        url = page["url"]
        content = page["content"]

        # Extract from HTML
        found = extract_from_html(content)
        if found:
            print(f"  [html] {len(found)} emails at {url}")
        all_emails.update(found)

        # Extract from JS files on EVERY page
        js_emails = extract_from_js_files(domain, content)
        if js_emails:
            print(f"  [js] {len(js_emails)} emails from JS files at {url}")
        all_emails.update(js_emails)

    # Pattern guessing
    guessed = guess_emails(domain)
    if guessed:
        all_emails.update(guessed)
        print(f"  [guess] {len(guessed)} pattern emails added")

    print(f"  [total] {len(all_emails)} raw emails found")
    return list(all_emails)