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
    "sendgrid.net","twilio.com","segment.com","datadog.com",
    "newrelic.com","pagerduty.com","opsgenie.com","atlassian.com",
}

FAKE_PREFIXES = {
    "react","redux","angular","vue","node","npm","webpack","babel",
    "eslint","prettier","jest","lodash","axios","express","django",
    "flask","bootstrap","tailwind","jquery","typescript","javascript",
    "python","java","golang","noreply","no-reply","donotreply",
    "notifications","alerts","automated","system","robot","auto",
    "bounce","daemon","mailer-daemon","unsubscribe",
}

IMAGE_EXTS = {".png",".jpg",".jpeg",".gif",".svg",".webp",".ico",".bmp",".css",".woff",".ttf"}

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
        if not is_fake(e): found.add(e)
    for name, dom in re.findall(r"([a-zA-Z0-9._\-]+)\s*\[at\]\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text, re.I):
        e = f"{name}@{dom}".lower()
        if not is_fake(e): found.add(e)
    for name, dom in re.findall(r"([a-zA-Z0-9._\-]+)\s*\(at\)\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text, re.I):
        e = f"{name}@{dom}".lower()
        if not is_fake(e): found.add(e)
    return found

def extract_from_html(content, target_root):
    mailto_emails = set()
    page_emails = set()
    if not content:
        return mailto_emails, page_emails
    try:
        soup = BeautifulSoup(content, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().startswith("mailto:"):
                m = re.search(EMAIL_REGEX, href)
                if m:
                    email = m.group(0).lower()
                    if not is_fake(email) and is_target_email(email, target_root):
                        mailto_emails.add(email)
        for e in extract_from_text(soup.get_text(" ")):
            if is_target_email(e, target_root):
                page_emails.add(e)
        for meta in soup.find_all("meta"):
            val = meta.get("content", "")
            if "@" in val:
                for e in extract_from_text(val):
                    if is_target_email(e, target_root):
                        page_emails.add(e)
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                for e in extract_from_text(script.string):
                    if is_target_email(e, target_root):
                        page_emails.add(e)
        for script in soup.find_all("script"):
            txt = script.string or ""
            if "@" in txt:
                for e in extract_from_text(txt):
                    if is_target_email(e, target_root):
                        page_emails.add(e)
        # All HTML attributes that might contain emails
        for tag in soup.find_all(True):
            for attr in ["data-email","data-contact","data-mailto",
                         "content","href","value","placeholder",
                         "data-value","data-address","title","alt"]:
                val = tag.get(attr, "")
                if val and "@" in val and "mailto:" not in val.lower():
                    for e in extract_from_text(val):
                        if is_target_email(e, target_root):
                            page_emails.add(e)
        # Comments in HTML source
        from bs4 import Comment
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            if "@" in comment:
                for e in extract_from_text(comment):
                    if is_target_email(e, target_root):
                        page_emails.add(e)
        # Raw HTML source scan - catches obfuscated emails in HTML comments/attributes
        for e in extract_from_text(content):
            if is_target_email(e, target_root):
                page_emails.add(e)
    except Exception as ex:
        print(f"[HTML] Error: {ex}")
    return mailto_emails, page_emails

def scan_js_file(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, verify=False)
        if r.status_code == 200 and len(r.content) < 5242880:
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
            if not any(src.endswith(e) for e in [".png",".jpg",".css",".woff"]):
                js_urls.append(src)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(scan_js_file, u) for u in js_urls[:10]]
            for f in as_completed(futures, timeout=30):
                try:
                    for e in f.result():
                        if is_target_email(e, target_root):
                            emails.add(e)
                except:
                    pass
    except Exception as ex:
        print(f"[JS] Error: {ex}")
    return emails

def fetch_wayback(domain, root):
    emails = set()
    try:
        import urllib.request
        url = f"http://web.archive.org/cdx/search/cdx?url={root}&output=text&fl=original&collapse=urlkey&limit=50"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        res = urllib.request.urlopen(req, timeout=8)
        for line in res.read().decode().splitlines():
            for e in extract_from_text(line):
                if is_target_email(e, root):
                    emails.add(e)
        print(f"[wayback] {len(emails)} emails")
    except Exception as ex:
        print(f"[wayback] Error: {ex}")
    return emails

def fetch_ssl_certs(domain, root):
    emails = set()
    try:
        r = requests.get(f"https://crt.sh/?q={root}&output=json", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            for entry in r.json()[:200]:
                for field in ["name_value", "common_name"]:
                    val = entry.get(field, "")
                    for e in extract_from_text(val):
                        if is_target_email(e, root):
                            emails.add(e)
        print(f"[ssl] {len(emails)} emails")
    except Exception as ex:
        print(f"[ssl] Error: {ex}")
    return emails

def fetch_publicwww(domain, root):
    emails = set()
    try:
        r = requests.get(f"https://hunter.io/try/v2/domain-search?domain={root}&limit=10", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            for e in data.get("emails", []):
                val = e.get("value","")
                if val and is_target_email(val, root):
                    emails.add(val.lower())
        print(f"[hunter] {len(emails)} emails")
    except Exception as ex:
        print(f"[hunter] Error: {ex}")
    return emails

def fetch_emailformat(root):
    emails = set()
    try:
        r = requests.get(f"https://www.email-format.com/d/{root}/", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            for e in re.findall(r"[a-zA-Z0-9._%+\-]+@" + re.escape(root), r.text):
                if not is_fake(e.lower()):
                    emails.add(e.lower())
        print(f"[emailformat] {len(emails)} emails")
    except Exception as ex:
        print(f"[emailformat] Error: {ex}")
    return emails

def fetch_github_org(root):
    emails = set()
    try:
        org = root.split(".")[0]
        r = requests.get(f"https://api.github.com/orgs/{org}/members?per_page=30", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            for member in r.json():
                login = member.get("login","")
                if login:
                    pr = requests.get(f"https://api.github.com/users/{login}", headers=HEADERS, timeout=5)
                    if pr.status_code == 200:
                        email = pr.json().get("email","")
                        if email and is_target_email(email, root):
                            emails.add(email.lower())
        print(f"[github] {len(emails)} emails")
    except Exception as ex:
        print(f"[github] Error: {ex}")
    return emails

def fetch_securitytxt(domain, root):
    emails = set()
    for url in [f"https://{domain}/.well-known/security.txt", f"https://{domain}/security.txt",
                f"https://security.{root}/.well-known/security.txt", f"https://security.{root}/security.txt"]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=6, verify=False)
            if r.status_code == 200:
                for e in extract_from_text(r.text):
                    if is_target_email(e, root):
                        emails.add(e)
                # Also grab mailto: links
                for m in re.findall(r"mailto:([^\s>]+)", r.text, re.I):
                    e = m.strip().lower()
                    if is_target_email(e, root) and not is_fake(e):
                        emails.add(e)
        except:
            pass
    print(f"[security.txt] {len(emails)} emails")
    return emails


def fetch_dns_txt(domain, root):
    emails = set()
    try:
        import dns.resolver
        for record in dns.resolver.resolve(domain, 'TXT', lifetime=5):
            txt = record.to_text()
            for e in re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', txt):
                if is_target_email(e.lower(), root):
                    emails.add(e.lower())
        print(f"[dns-txt] {len(emails)} emails")
    except Exception as ex:
        print(f"[dns-txt] Error: {ex}")
    return emails

def fetch_rdap(domain, root):
    emails = set()
    try:
        r = requests.get(f"https://rdap.org/domain/{root}", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            text = str(r.json())
            for e in re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text):
                e = e.lower()
                if is_target_email(e, root) and not is_fake(e):
                    emails.add(e)
        print(f"[rdap] {len(emails)} emails")
    except Exception as ex:
        print(f"[rdap] Error: {ex}")
    return emails

def fetch_bing_search(domain, root):
    emails = set()
    try:
        queries = [f'"{root}" email contact', f'site:{root} "@{root}"', f'"{root}" "@{root}"']
        for q in queries:
            r = requests.get(
                f"https://www.bing.com/search?q={requests.utils.quote(q)}&count=20",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=10
            )
            if r.status_code == 200:
                for e in re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', r.text):
                    e = e.lower()
                    if is_target_email(e, root) and not is_fake(e):
                        emails.add(e)
        print(f"[bing] {len(emails)} emails")
    except Exception as ex:
        print(f"[bing] Error: {ex}")
    return emails

def fetch_pastebin(root):
    emails = set()
    try:
        r = requests.get(
            f"https://psbdmp.ws/api/search/{root}",
            headers=HEADERS, timeout=8
        )
        if r.status_code == 200:
            data = r.json()
            for item in data.get("data", [])[:10]:
                pid = item.get("id","")
                if pid:
                    pr = requests.get(f"https://pastebin.com/raw/{pid}", headers=HEADERS, timeout=5)
                    if pr.status_code == 200:
                        for e in re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', pr.text):
                            e = e.lower()
                            if is_target_email(e, root) and not is_fake(e):
                                emails.add(e)
        print(f"[pastebin] {len(emails)} emails")
    except Exception as ex:
        print(f"[pastebin] Error: {ex}")
    return emails

def fetch_commoncrawl(root):
    emails = set()
    try:
        r = requests.get(
            f"https://index.commoncrawl.org/CC-MAIN-2024-10-index?url={root}/*&output=json&limit=20",
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            for line in r.text.splitlines()[:20]:
                try:
                    import json
                    obj = json.loads(line)
                    url = obj.get("url","")
                    if url:
                        pr = requests.get(
                            f"https://data.commoncrawl.org/{obj.get('filename','')}",
                            headers={**HEADERS, "Range": f"bytes={obj.get('offset',0)}-{int(obj.get('offset',0))+int(obj.get('length',5000))}"},
                            timeout=8
                        )
                        for e in re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', pr.text):
                            e = e.lower()
                            if is_target_email(e, root) and not is_fake(e):
                                emails.add(e)
                except:
                    pass
        print(f"[commoncrawl] {len(emails)} emails")
    except Exception as ex:
        print(f"[commoncrawl] Error: {ex}")
    return emails

def fetch_sitemap(domain, root):
    emails = set()
    urls_to_check = [
        f"https://{domain}/sitemap.xml",
        f"https://{domain}/sitemap_index.xml",
        f"https://{domain}/robots.txt",
        f"https://www.{domain}/sitemap.xml",
    ]
    contact_urls = set()
    try:
        for url in urls_to_check:
            r = requests.get(url, headers=HEADERS, timeout=6, verify=False)
            if r.status_code == 200:
                for e in re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', r.text):
                    e = e.lower()
                    if is_target_email(e, root) and not is_fake(e):
                        emails.add(e)
                # Find contact/about URLs in sitemap
                for u in re.findall(r'<loc>(.*?)</loc>', r.text):
                    if any(k in u.lower() for k in ['contact','about','team','security','support','legal','privacy']):
                        contact_urls.add(u)
        # Fetch those contact pages
        for url in list(contact_urls)[:15]:
            try:
                r = requests.get(url, headers=HEADERS, timeout=6, verify=False)
                if r.status_code == 200:
                    for e in re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', r.text):
                        e = e.lower()
                        if is_target_email(e, root) and not is_fake(e):
                            emails.add(e)
            except:
                pass
        print(f"[sitemap] {len(emails)} emails")
    except Exception as ex:
        print(f"[sitemap] Error: {ex}")
    return emails

def fetch_gravatar_verify(emails_to_check, root):
    import hashlib
    confirmed = set()
    try:
        for e in list(emails_to_check)[:20]:
            h = hashlib.md5(e.strip().lower().encode()).hexdigest()
            r = requests.get(f"https://www.gravatar.com/avatar/{h}?d=404", headers=HEADERS, timeout=4)
            if r.status_code == 200:
                confirmed.add(e)
        print(f"[gravatar] {len(confirmed)} confirmed emails")
    except Exception as ex:
        print(f"[gravatar] Error: {ex}")
    return confirmed

def fetch_emailrep(root):
    emails = set()
    try:
        common = [f"security@{root}", f"contact@{root}", f"info@{root}",
                  f"support@{root}", f"admin@{root}", f"hello@{root}",
                  f"privacy@{root}", f"legal@{root}", f"abuse@{root}",
                  f"press@{root}", f"team@{root}", f"help@{root}",
                  f"trust@{root}", f"disclosure@{root}", f"vdp@{root}",
                  f"bugbounty@{root}", f"bugs@{root}", f"ceo@{root}",
                  f"founders@{root}", f"hr@{root}", f"jobs@{root}"]
        for e in common:
            try:
                r = requests.get(f"https://emailrep.io/{e}", headers=HEADERS, timeout=4)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("reputation") in ["high","medium"] or data.get("references",0) > 0:
                        emails.add(e)
            except:
                pass
        print(f"[emailrep] {len(emails)} emails")
    except Exception as ex:
        print(f"[emailrep] Error: {ex}")
    return emails

def fetch_public_sources(domain):
    emails = set()
    root = get_root(domain)
    try:
        r = requests.get(f"https://crt.sh/?q=%40{root}&output=json", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            for entry in r.json()[:200]:
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
    emails.update(fetch_wayback(domain, root))
    emails.update(fetch_ssl_certs(domain, root))
    emails.update(fetch_publicwww(domain, root))
    emails.update(fetch_emailformat(root))
    emails.update(fetch_github_org(root))
    emails.update(fetch_securitytxt(domain, root))
    emails.update(fetch_dns_txt(domain, root))
    emails.update(fetch_rdap(domain, root))
    emails.update(fetch_bing_search(domain, root))
    emails.update(fetch_pastebin(root))
    emails.update(fetch_commoncrawl(root))
    emails.update(fetch_sitemap(domain, root))
    emails.update(fetch_emailrep(root))
    # Gravatar verify all collected so far
    emails.update(fetch_gravatar_verify(emails, root))
    return emails

def extract_all(domain, pages_data):
    root = get_root(domain)
    all_emails = set()
    print(f"\n[EXTRACT] Scanning {len(pages_data)} pages for *{root}* emails")

    pub = fetch_public_sources(domain)
    all_emails.update(pub)
    if pub:
        print(f"[public] {len(pub)} emails from crt.sh/whois")

    JS_PAGES = ["contact","about","security","support","help","press",
                "legal","privacy","disclosure","trust","team","careers",
                "leadership","investors","partners","abuse","compliance"]

    def process_page(page):
        url = page.get("url", "")
        content = page.get("content", "")
        if not content:
            return set()
        found = set()
        mailto_found, page_found = extract_from_html(content, root)
        found.update(mailto_found)
        found.update(page_found)
        if any(k in url.lower() for k in JS_PAGES):
            js = fetch_js_emails(domain, content, root)
            found.update(js)
        if found:
            print(f"[page] {url} -> {len(found)} emails")
        return found

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_page, page) for page in pages_data]
        for f in as_completed(futures, timeout=300):
            try:
                all_emails.update(f.result())
            except:
                pass

    result = [e for e in all_emails if not is_fake(e)]
    print(f"[EXTRACT] Done - {len(result)} emails found")
    return result

# Alias for backward compatibility with main.py
extract_emails_from_text = extract_from_text





