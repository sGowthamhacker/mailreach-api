import re
import sys
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
EMAIL_REGEX = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"

FAKE_DOMAINS = {
    "example.com","example.org","example.net","test.com","test.org",
    "fake.com","domain.com","email.com","yoursite.com","website.com",
    "sentry.io","w3.org","schema.org","googleapis.com","gstatic.com",
    "cloudflare.com","localhost","github.com","github.io","gitlab.com",
    "wixpress.com","squarespace.com","shopify.com","wordpress.com",
    "jquery.com","npmjs.com","unpkg.com","cdnjs.com","amazonaws.com",
    "intercom.io","zendesk.com","hubspot.com","mailchimp.com",
    "sendgrid.net","twilio.com","stripe.com","segment.com",
    "datadog.com","newrelic.com","pagerduty.com","opsgenie.com",
}

FAKE_PREFIXES = {
    "react","redux","angular","vue","node","npm","webpack","babel",
    "eslint","prettier","jest","lodash","axios","express","django",
    "flask","bootstrap","tailwind","jquery","typescript","javascript",
    "python","java","golang","noreply","no-reply","donotreply",
    "notifications","alerts","automated","system","robot","auto",
    "bounce","daemon","mailer-daemon","unsubscribe",
}

IMAGE_EXTS = {".png",".jpg",".jpeg",".gif",".svg",".webp",".ico",".bmp",".css",".js",".woff"}

def get_root(domain):
    parts = domain.split(".")
    return ".".join(parts[-2:]) if len(parts) > 1 else domain

def is_fake(email):
    if not email or "@" not in email:
        return True
    try:
        prefix, dom = email.lower().rsplit("@", 1)
    except:
        return True
    if dom in FAKE_DOMAINS:
        return True
    if prefix in FAKE_PREFIXES:
        return True
    if any(ext in prefix for ext in IMAGE_EXTS):
        return True
    if any(dom.endswith(ext) for ext in IMAGE_EXTS):
        return True
    if "://" in email or email.count("/") > 1:
        return True
    if len(prefix) < 2 or prefix.isdigit():
        return True
    if dom.startswith(("window.","this.","self.","document.","location.")):
        return True
    if dom.count(".") > 4 or len(dom) > 50:
        return True
    if re.match(r'^[a-f0-9]{10,}$', prefix):
        return True
    return False

def is_target_email(email, root):
    dom = email.split("@")[1].lower()
    dom_root = get_root(dom)
    return dom_root == root or dom.endswith("." + root)

def extract_from_text(text):
    if not text:
        return set()
    found = set()
    for email in re.findall(EMAIL_REGEX, text):
        email = email.strip(".,;:\"'><)([]{}`|\\").lower()
        if not is_fake(email):
            found.add(email)
    for name, dom in re.findall(r"([a-zA-Z0-9._\-]+)\s+at\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text, re.I):
        e = f"{name}@{dom}".lower()
        if not is_fake(e):
            found.add(e)
    for name, dom in re.findall(r"([a-zA-Z0-9._\-]+)\s*\[at\]\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text, re.I):
        e = f"{name}@{dom}".lower()
        if not is_fake(e):
            found.add(e)
    for name, dom in re.findall(r"([a-zA-Z0-9._\-]+)\s*\(at\)\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text, re.I):
        e = f"{name}@{dom}".lower()
        if not is_fake(e):
            found.add(e)
    return found

def extract_from_html(content, target_root):
    mailto_emails = set()
    page_emails = set()
    if not content:
        return mailto_emails, page_emails
    try:
        soup = BeautifulSoup(content, "html.parser")
        # mailto: links — highest confidence, keep regardless of domain
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().startswith("mailto:"):
                m = re.search(EMAIL_REGEX, href)
                if m:
                    email = m.group(0).lower()
                    if not is_fake(email):
                        mailto_emails.add(email)
        # page text — only keep target domain emails
        text_emails = extract_from_text(soup.get_text(" "))
        for e in text_emails:
            if is_target_email(e, target_root):
                page_emails.add(e)
        # meta tags
        for meta in soup.find_all("meta"):
            val = meta.get("content", "")
            if "@" in val:
                for e in extract_from_text(val):
                    if is_target_email(e, target_root):
                        page_emails.add(e)
        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                for e in extract_from_text(script.string):
                    if is_target_email(e, target_root):
                        page_emails.add(e)
        # inline scripts — only target domain
        for script in soup.find_all("script"):
            txt = script.string or ""
            if "@" in txt:
                for e in extract_from_text(txt):
                    if is_target_email(e, target_root):
                        page_emails.add(e)
    except Exception as ex:
        print(f"[HTML] Error: {ex}")
    return mailto_emails, page_emails

def scan_js_file(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=5, verify=False)
        if r.status_code == 200 and len(r.text) < 500000:
            return extract_from_text(r.text)
    except:
        pass
    return set()

def fetch_js_emails(domain, html, target_root):
    emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        js_urls = []
        for script in soup.find_all("script", src=True):
            src = script["src"]
            if src.startswith("//"): src = "https:" + src
            elif src.startswith("/"): src = f"https://{domain}{src}"
            elif not src.startswith("http"): src = f"https://{domain}/{src}"
            if not any(src.endswith(e) for e in [".png",".jpg",".css"]):
                js_urls.append(src)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scan_js_file, u) for u in js_urls[:15]]
            for f in as_completed(futures, timeout=15):
                try:
                    for e in f.result():
                        if is_target_email(e, target_root):
                            emails.add(e)
                except:
                    pass
    except Exception as ex:
        print(f"[JS] Error: {ex}")
    return emails

def fetch_public_sources(domain):
    emails = set()
    root = get_root(domain)
    try:
        r = requests.get(f"https://crt.sh/?q=%40{root}&output=json", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for entry in data[:100]:
                name = entry.get("name_value", "")
                for e in extract_from_text(name):
                    if is_target_email(e, root):
                        emails.add(e)
        print(f"[crt.sh] {len(emails)} emails")
    except Exception as ex:
        print(f"[crt.sh] Error: {ex}")
    try:
        import whois
        w = whois.whois(root)
        for e in extract_from_text(str(w)):
            if is_target_email(e, root):
                emails.add(e)
        print(f"[whois] {len(emails)} emails")
    except Exception as ex:
        print(f"[whois] Error: {ex}")
    return emails

def extract_all(domain, pages_data):
    root = get_root(domain)
    all_emails = set()
    print(f"\n[EXTRACT] Scanning {len(pages_data)} pages for *{root}* emails")

    # Public sources
    pub = fetch_public_sources(domain)
    all_emails.update(pub)
    if pub:
        print(f"[public] {len(pub)} emails from crt.sh/whois")

    # Each crawled page
    for page in pages_data:
        url = page.get("url", "")
        content = page.get("content", "")
        if not content:
            continue
        mailto_found, page_found = extract_from_html(content, root)
        found = mailto_found | page_found
        if found:
            print(f"[page] {url} -> {len(found)} emails")
        all_emails.update(found)

        # JS scan for key pages only
        if any(k in url.lower() for k in ["contact","about","security","support","help","press","legal","privacy","disclosure","trust"]):
            js = fetch_js_emails(domain, content, root)
            if js:
                print(f"[js] {url} -> {len(js)} emails")
            all_emails.update(js)

    result = [e for e in all_emails if not is_fake(e)]
    print(f"[EXTRACT] Done - {len(result)} emails found")
    return result