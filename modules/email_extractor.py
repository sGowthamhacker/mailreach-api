import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
from config import EMAIL_PREFIXES

EMAIL_REGEX = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

FAKE_DOMAINS = [
    "example.com", "example.org", "test.com", "fake.com",
    "domain.com", "email.com", "yoursite.com", "website.com",
    "sentry.io", "sentry.com", "w3.org", "schema.org",
    "googleapis.com", "gstatic.com", "cloudflare.com",
]

FAKE_PREFIXES = [
    "jane.doe", "john.doe", "guest", "you",
    "new.email", "user", "someone", "username",
    "name", "firstname", "lastname", "fullname",
]

def is_fake_email(email):
    domain = email.split("@")[1].lower()
    prefix = email.split("@")[0].lower()
    if domain in FAKE_DOMAINS:
        return True
    if prefix in FAKE_PREFIXES:
        return True
    # Skip image/asset emails
    if any(ext in prefix for ext in [".png", ".jpg", ".svg", ".gif", ".webp"]):
        return True
    return False

def extract_emails_from_text(text):
    found = re.findall(EMAIL_REGEX, text)
    clean = []
    for e in found:
        e = e.strip(".,;:\"'><)(][}{")
        if "@" in e and "." in e.split("@")[1]:
            if not is_fake_email(e):
                clean.append(e.lower())
    return list(set(clean))

def extract_from_html(content):
    emails = set()
    try:
        found = extract_emails_from_text(content)
        emails.update(found)

        soup = BeautifulSoup(content, "html.parser")

        # mailto links
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if "mailto:" in href:
                email = href.replace("mailto:", "").split("?")[0].strip()
                if "@" in email and not is_fake_email(email):
                    emails.add(email.lower())

        # data attributes
        for tag in soup.find_all(True):
            for attr, val in tag.attrs.items():
                if isinstance(val, str) and "@" in val:
                    found = extract_emails_from_text(val)
                    emails.update(found)

        # JSON-LD schema markup
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                found = extract_emails_from_text(tag.string or "")
                emails.update(found)
            except:
                pass

        # meta tags
        for tag in soup.find_all("meta"):
            content_val = tag.get("content", "")
            if "@" in content_val:
                found = extract_emails_from_text(content_val)
                emails.update(found)

        # plaintext inside pre/code blocks
        for tag in soup.find_all(["pre", "code"]):
            found = extract_emails_from_text(tag.get_text())
            emails.update(found)

        # Contact page specific — look for spans/divs with email text
        for tag in soup.find_all(["span", "p", "div", "li", "td"]):
            text = tag.get_text()
            if "@" in text and len(text) < 200:
                found = extract_emails_from_text(text)
                emails.update(found)

    except:
        pass
    return list(emails)

def get_all_js_files(domain, html):
    soup = BeautifulSoup(html, "html.parser")
    js_files = []
    seen = set()
    for tag in soup.find_all("script", src=True):
        src = tag["src"]
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http"):
            if domain in src and src not in seen:
                js_files.append(src)
                seen.add(src)
        else:
            full = f"https://{domain}{src}" if src.startswith("/") else f"https://{domain}/{src}"
            if full not in seen:
                js_files.append(full)
                seen.add(full)
    return js_files

def extract_from_js_files(domain, html):
    emails = set()
    js_files = get_all_js_files(domain, html)
    print(f"  [js] found {len(js_files)} JS files to scan")

    for js_url in js_files:
        try:
            r = requests.get(js_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                found = extract_emails_from_text(r.text)
                if found:
                    print(f"  [js] {len(found)} emails in {js_url}")
                    emails.update(found)
        except:
            pass
    return list(emails)

def fetch_extra_sources(domain):
    """Fetch non-HTML sources that often contain emails"""
    emails = set()
    session = requests.Session()
    session.headers.update(HEADERS)

    extra_urls = [
        # Security & Disclosure
        f"https://{domain}/security.txt",
        f"https://{domain}/.well-known/security.txt",
        f"https://{domain}/security",
        f"https://{domain}/security-policy",
        f"https://{domain}/security/disclosure",
        f"https://{domain}/security/contact",
        f"https://{domain}/security/reporting",
        f"https://{domain}/security/vulnerabilities",
        f"https://{domain}/security/advisories",
        f"https://{domain}/security/pgp",
        f"https://{domain}/security/pgp-key",
        f"https://{domain}/security/pgp-key.txt",
        f"https://{domain}/security/gpg-key",
        f"https://{domain}/security/gpg-key.txt",
        f"https://{domain}/security/hall-of-fame",
        f"https://{domain}/security/acknowledgements",
        f"https://{domain}/security/thanks",
        f"https://{domain}/security/bug-bounty",
        f"https://{domain}/security/responsible-disclosure",
        f"https://{domain}/security/report",
        f"https://{domain}/security/report-a-bug",
        f"https://{domain}/security/report-vulnerability",
        f"https://{domain}/responsible-disclosure",
        f"https://{domain}/responsible_disclosure",
        f"https://{domain}/vulnerability-disclosure",
        f"https://{domain}/vulnerability-disclosure-policy",
        f"https://{domain}/coordinated-disclosure",
        f"https://{domain}/bug-bounty",
        f"https://{domain}/bugbounty",
        f"https://{domain}/bug_bounty",
        f"https://{domain}/bounty",
        f"https://{domain}/bounty-program",
        f"https://{domain}/vdp",
        f"https://{domain}/bbp",
        f"https://{domain}/cvd",
        f"https://{domain}/psirt",
        f"https://{domain}/cert",
        f"https://{domain}/csirt",
        f"https://{domain}/pentest",
        f"https://{domain}/hall-of-fame",
        f"https://{domain}/halloffame",
        f"https://{domain}/hof",
        f"https://{domain}/acknowledgements",
        f"https://{domain}/acknowledgments",
        f"https://{domain}/thanks",
        f"https://{domain}/thank-you",
        f"https://{domain}/researchers",
        f"https://{domain}/report",
        f"https://{domain}/report-bug",
        f"https://{domain}/report-a-bug",
        f"https://{domain}/report-vulnerability",
        f"https://{domain}/report-issue",
        f"https://{domain}/disclose",
        f"https://{domain}/disclosure",
        f"https://{domain}/advisories",
        f"https://{domain}/security-advisories",
        f"https://{domain}/cve",
        f"https://{domain}/cves",
        f"https://{domain}/patches",
        f"https://{domain}/patch-notes",
        f"https://{domain}/pgp",
        f"https://{domain}/pgp-key",
        f"https://{domain}/pgp-key.txt",
        f"https://{domain}/gpg",
        f"https://{domain}/gpg-key",
        f"https://{domain}/gpg-key.txt",
        f"https://{domain}/publickey",
        f"https://{domain}/public-key",
        f"https://{domain}/keys",
        f"https://{domain}/.well-known/pgp-key.txt",
        f"https://{domain}/.well-known/gpg-key.txt",
        f"https://{domain}/.well-known/security-contact",
        f"https://{domain}/.well-known/csaf",

        # Contact
        f"https://{domain}/contact",
        f"https://{domain}/contact-us",
        f"https://{domain}/contactus",
        f"https://{domain}/contact_us",
        f"https://{domain}/contact.html",
        f"https://{domain}/contact.php",
        f"https://{domain}/contact.json",
        f"https://{domain}/contact.xml",
        f"https://{domain}/contacts",
        f"https://{domain}/get-in-touch",
        f"https://{domain}/getintouch",
        f"https://{domain}/get_in_touch",
        f"https://{domain}/reach",
        f"https://{domain}/reach-us",
        f"https://{domain}/reach_us",
        f"https://{domain}/reachout",
        f"https://{domain}/reach-out",
        f"https://{domain}/talk-to-us",
        f"https://{domain}/talktous",
        f"https://{domain}/talk_to_us",
        f"https://{domain}/say-hello",
        f"https://{domain}/sayhello",
        f"https://{domain}/hello",
        f"https://{domain}/connect",
        f"https://{domain}/connect-with-us",
        f"https://{domain}/connectwithus",
        f"https://{domain}/enquiry",
        f"https://{domain}/enquiries",
        f"https://{domain}/inquiry",
        f"https://{domain}/inquiries",
        f"https://{domain}/email",
        f"https://{domain}/email-us",
        f"https://{domain}/emailus",
        f"https://{domain}/mail",
        f"https://{domain}/mail-us",
        f"https://{domain}/message",
        f"https://{domain}/messages",
        f"https://{domain}/message-us",
        f"https://{domain}/write-to-us",
        f"https://{domain}/write-us",
        f"https://{domain}/writeus",
        f"https://{domain}/ping",
        f"https://{domain}/drop-us-a-line",
        f"https://{domain}/drop-a-line",
        f"https://{domain}/lets-talk",
        f"https://{domain}/letstalk",
        f"https://{domain}/get-help",
        f"https://{domain}/gethelp",
        f"https://{domain}/ask",
        f"https://{domain}/feedback",
        f"https://{domain}/feedbacks",
        f"https://{domain}/suggestions",
        f"https://{domain}/hire-us",
        f"https://{domain}/hireus",
        f"https://{domain}/work-with-us",
        f"https://{domain}/workwithus",
        f"https://{domain}/partner-with-us",
        f"https://{domain}/partnerwithus",
        f"https://{domain}/info",
        f"https://{domain}/information",
        f"https://{domain}/general-enquiry",
        f"https://{domain}/general-inquiry",
        f"https://{domain}/speak-to-us",
        f"https://{domain}/chat-with-us",
        f"https://{domain}/start-a-conversation",
        f"https://{domain}/send-message",
        f"https://{domain}/send-email",
        f"https://{domain}/offices",
        f"https://{domain}/office",
        f"https://{domain}/locations",
        f"https://{domain}/location",
        f"https://{domain}/headquarters",
        f"https://{domain}/hq",
        f"https://{domain}/directions",
        f"https://{domain}/map",

        # About
        f"https://{domain}/about",
        f"https://{domain}/about-us",
        f"https://{domain}/aboutus",
        f"https://{domain}/about_us",
        f"https://{domain}/about.html",
        f"https://{domain}/our-story",
        f"https://{domain}/ourstory",
        f"https://{domain}/our_story",
        f"https://{domain}/who-we-are",
        f"https://{domain}/whoweare",
        f"https://{domain}/mission",
        f"https://{domain}/our-mission",
        f"https://{domain}/vision",
        f"https://{domain}/values",
        f"https://{domain}/overview",
        f"https://{domain}/introduction",
        f"https://{domain}/history",
        f"https://{domain}/background",
        f"https://{domain}/profile",
        f"https://{domain}/manifesto",
        f"https://{domain}/philosophy",
        f"https://{domain}/culture",
        f"https://{domain}/company",
        f"https://{domain}/company/about",
        f"https://{domain}/company/contact",
        f"https://{domain}/company/team",
        f"https://{domain}/company/security",
        f"https://{domain}/corporate",
        f"https://{domain}/organization",
        f"https://{domain}/organisation",
        f"https://{domain}/imprint",
        f"https://{domain}/impressum",

        # Team
        f"https://{domain}/team",
        f"https://{domain}/our-team",
        f"https://{domain}/ourteam",
        f"https://{domain}/people",
        f"https://{domain}/staff",
        f"https://{domain}/crew",
        f"https://{domain}/founders",
        f"https://{domain}/founder",
        f"https://{domain}/co-founders",
        f"https://{domain}/cofounders",
        f"https://{domain}/leadership",
        f"https://{domain}/leaders",
        f"https://{domain}/management",
        f"https://{domain}/executives",
        f"https://{domain}/executive-team",
        f"https://{domain}/board",
        f"https://{domain}/board-of-directors",
        f"https://{domain}/directors",
        f"https://{domain}/advisors",
        f"https://{domain}/advisory-board",
        f"https://{domain}/officers",
        f"https://{domain}/c-suite",
        f"https://{domain}/employees",
        f"https://{domain}/members",
        f"https://{domain}/meet-the-team",
        f"https://{domain}/meet-us",
        f"https://{domain}/our-people",
        f"https://{domain}/contributors",

        # Support & Help
        f"https://{domain}/support",
        f"https://{domain}/help",
        f"https://{domain}/faq",
        f"https://{domain}/faqs",
        f"https://{domain}/helpdesk",
        f"https://{domain}/help-desk",
        f"https://{domain}/help-center",
        f"https://{domain}/helpcenter",
        f"https://{domain}/helpcentre",
        f"https://{domain}/customer-service",
        f"https://{domain}/customerservice",
        f"https://{domain}/customer-support",
        f"https://{domain}/customersupport",
        f"https://{domain}/customer-care",
        f"https://{domain}/tickets",
        f"https://{domain}/open-ticket",
        f"https://{domain}/new-ticket",
        f"https://{domain}/submit-ticket",
        f"https://{domain}/knowledge-base",
        f"https://{domain}/knowledgebase",
        f"https://{domain}/kb",
        f"https://{domain}/documentation",
        f"https://{domain}/docs",
        f"https://{domain}/wiki",
        f"https://{domain}/guides",
        f"https://{domain}/tutorials",
        f"https://{domain}/resources",
        f"https://{domain}/forum",
        f"https://{domain}/forums",
        f"https://{domain}/community",
        f"https://{domain}/chat",
        f"https://{domain}/live-chat",

        # Legal & Privacy
        f"https://{domain}/legal",
        f"https://{domain}/privacy",
        f"https://{domain}/terms",
        f"https://{domain}/policy",
        f"https://{domain}/compliance",
        f"https://{domain}/gdpr",
        f"https://{domain}/cookies",
        f"https://{domain}/disclaimer",
        f"https://{domain}/tos",
        f"https://{domain}/terms-of-service",
        f"https://{domain}/terms-of-use",
        f"https://{domain}/privacy-policy",
        f"https://{domain}/cookie-policy",
        f"https://{domain}/data-protection",
        f"https://{domain}/dpa",
        f"https://{domain}/aup",
        f"https://{domain}/acceptable-use",
        f"https://{domain}/dmca",
        f"https://{domain}/copyright",
        f"https://{domain}/ccpa",
        f"https://{domain}/dpo",

        # Press & Media
        f"https://{domain}/press",
        f"https://{domain}/media",
        f"https://{domain}/newsroom",
        f"https://{domain}/news",
        f"https://{domain}/press-kit",
        f"https://{domain}/presskit",
        f"https://{domain}/press-releases",
        f"https://{domain}/press-room",
        f"https://{domain}/pressroom",
        f"https://{domain}/media-kit",
        f"https://{domain}/mediakit",
        f"https://{domain}/media-contact",
        f"https://{domain}/journalists",
        f"https://{domain}/editorial",
        f"https://{domain}/brand",
        f"https://{domain}/brand-assets",
        f"https://{domain}/logo",
        f"https://{domain}/logos",
        f"https://{domain}/assets",
        f"https://{domain}/pr",
        f"https://{domain}/communications",

        # Careers & Jobs
        f"https://{domain}/careers",
        f"https://{domain}/jobs",
        f"https://{domain}/hiring",
        f"https://{domain}/work-with-us",
        f"https://{domain}/join-us",
        f"https://{domain}/join",
        f"https://{domain}/join-our-team",
        f"https://{domain}/openings",
        f"https://{domain}/open-positions",
        f"https://{domain}/vacancies",
        f"https://{domain}/positions",
        f"https://{domain}/recruitment",
        f"https://{domain}/apply",
        f"https://{domain}/internships",
        f"https://{domain}/internship",
        f"https://{domain}/graduate",
        f"https://{domain}/opportunities",
        f"https://{domain}/we-are-hiring",
        f"https://{domain}/work-here",

        # Developer & API
        f"https://{domain}/api",
        f"https://{domain}/api/contact",
        f"https://{domain}/api/info",
        f"https://{domain}/api/v1/contact",
        f"https://{domain}/api/v2/contact",
        f"https://{domain}/api/v1/info",
        f"https://{domain}/api/v2/info",
        f"https://{domain}/api/about",
        f"https://{domain}/api/team",
        f"https://{domain}/api/security",
        f"https://{domain}/api/users",
        f"https://{domain}/api/profile",
        f"https://{domain}/api/company",
        f"https://{domain}/developer",
        f"https://{domain}/developers",
        f"https://{domain}/dev",
        f"https://{domain}/open-source",
        f"https://{domain}/opensource",
        f"https://{domain}/contributing",
        f"https://{domain}/contribute",
        f"https://{domain}/github",
        f"https://{domain}/openapi.json",
        f"https://{domain}/swagger.json",
        f"https://{domain}/api-docs",
        f"https://{domain}/api/docs",
        f"https://{domain}/graphql",
        f"https://{domain}/v1",
        f"https://{domain}/v2",
        f"https://{domain}/v3",

        # Technical files
        f"https://{domain}/robots.txt",
        f"https://{domain}/humans.txt",
        f"https://{domain}/sitemap.xml",
        f"https://{domain}/sitemap_index.xml",
        f"https://{domain}/sitemap-index.xml",
        f"https://{domain}/sitemaps.xml",
        f"https://{domain}/feed.xml",
        f"https://{domain}/feed",
        f"https://{domain}/rss",
        f"https://{domain}/rss.xml",
        f"https://{domain}/atom.xml",
        f"https://{domain}/manifest.json",
        f"https://{domain}/app.json",
        f"https://{domain}/package.json",
        f"https://{domain}/composer.json",
        f"https://{domain}/info.json",
        f"https://{domain}/config.json",
        f"https://{domain}/settings.json",
        f"https://{domain}/data.json",
        f"https://{domain}/team.json",
        f"https://{domain}/authors.json",
        f"https://{domain}/CHANGELOG.md",
        f"https://{domain}/CHANGELOG",
        f"https://{domain}/AUTHORS",
        f"https://{domain}/AUTHORS.md",
        f"https://{domain}/CONTRIBUTING.md",
        f"https://{domain}/CONTRIBUTING",
        f"https://{domain}/README.md",
        f"https://{domain}/README",
        f"https://{domain}/LICENSE",
        f"https://{domain}/LICENSE.md",
        f"https://{domain}/SECURITY.md",
        f"https://{domain}/SECURITY",
        f"https://{domain}/CODE_OF_CONDUCT.md",
        f"https://{domain}/.well-known/security.txt",
        f"https://{domain}/.well-known/pgp-key.txt",
        f"https://{domain}/.well-known/gpg-key.txt",
        f"https://{domain}/.well-known/change-password",
        f"https://{domain}/.well-known/openid-configuration",
        f"https://www.{domain}/security.txt",
        f"https://www.{domain}/.well-known/security.txt",
        f"https://www.{domain}/contact",
        f"https://www.{domain}/about",

        # Blog & Content
        f"https://{domain}/blog",
        f"https://{domain}/blog/contact",
        f"https://{domain}/blog/about",
        f"https://{domain}/blog/team",
        f"https://{domain}/updates",
        f"https://{domain}/changelog",
        f"https://{domain}/release-notes",
        f"https://{domain}/announcements",
        f"https://{domain}/events",
        f"https://{domain}/webinars",
        f"https://{domain}/podcast",
        f"https://{domain}/videos",
        f"https://{domain}/newsletter",
        f"https://{domain}/subscribe",

        # Company & Investors
        f"https://{domain}/investors",
        f"https://{domain}/investor-relations",
        f"https://{domain}/investorrelations",
        f"https://{domain}/ir",
        f"https://{domain}/partners",
        f"https://{domain}/partnerships",
        f"https://{domain}/partner",
        f"https://{domain}/affiliates",
        f"https://{domain}/affiliate",
        f"https://{domain}/resellers",
        f"https://{domain}/vendors",
        f"https://{domain}/suppliers",
        f"https://{domain}/customers",
        f"https://{domain}/clients",
        f"https://{domain}/case-studies",
        f"https://{domain}/testimonials",
        f"https://{domain}/trust",
        f"https://{domain}/trust-center",
        f"https://{domain}/trustcenter",
        f"https://{domain}/status",
        f"https://{domain}/statuspage",
        f"https://{domain}/social",
        f"https://{domain}/referral",
        f"https://{domain}/ambassador",
        f"https://{domain}/accessibility",

        # Common subpaths with contact info
        f"https://{domain}/en/contact",
        f"https://{domain}/en/about",
        f"https://{domain}/en/security",
        f"https://{domain}/en/team",
        f"https://{domain}/en/support",
        f"https://{domain}/en-us/contact",
        f"https://{domain}/en-gb/contact",
        f"https://{domain}/us/contact",
        f"https://{domain}/uk/contact",
        f"https://{domain}/global/contact",
        f"https://{domain}/int/contact",
        f"https://{domain}/de/contact",
        f"https://{domain}/fr/contact",
        f"https://{domain}/es/contact",
        f"https://{domain}/pages/contact",
        f"https://{domain}/pages/about",
        f"https://{domain}/pages/team",
        f"https://{domain}/pages/security",
        f"https://{domain}/pages/legal",
        f"https://{domain}/page/contact",
        f"https://{domain}/page/about",
        f"https://{domain}/info/contact",
        f"https://{domain}/info/about",
        f"https://{domain}/site/contact",
        f"https://{domain}/site/about",
        f"https://{domain}/web/contact",
        f"https://{domain}/home/contact",
        f"https://{domain}/main/contact",
        f"https://{domain}/public/contact",
        f"https://{domain}/static/contact",

        # Common subdomains as URLs
        f"https://security.{domain}",
        f"https://contact.{domain}",
        f"https://support.{domain}",
        f"https://help.{domain}",
        f"https://about.{domain}",
        f"https://team.{domain}",
        f"https://press.{domain}",
        f"https://media.{domain}",
        f"https://blog.{domain}",
        f"https://careers.{domain}",
        f"https://jobs.{domain}",
        f"https://legal.{domain}",
        f"https://privacy.{domain}",
        f"https://trust.{domain}",
        f"https://status.{domain}",
        f"https://api.{domain}/contact",
        f"https://api.{domain}/info",
        f"https://api.{domain}/about",
        f"https://developer.{domain}",
        f"https://developers.{domain}",
        f"https://dev.{domain}",
        f"https://docs.{domain}",
        f"https://wiki.{domain}",
        f"https://community.{domain}",
        f"https://forum.{domain}",
        f"https://news.{domain}",
        f"https://info.{domain}",
        f"https://mail.{domain}",
        f"https://www.{domain}/security",
        f"https://www.{domain}/privacy",
        f"https://www.{domain}/legal",
        f"https://www.{domain}/team",
        f"https://www.{domain}/press",
        f"https://www.{domain}/careers",
        f"https://www.{domain}/support",
        f"https://www.{domain}/help",
        f"https://www.{domain}/blog",
        f"https://www.{domain}/investors",
        f"https://www.{domain}/about",
        f"https://www.{domain}/about-us",
    ]

    for url in extra_urls:
        try:
            r = session.get(url, timeout=8, verify=False)
            if r.status_code == 200:
                found = extract_emails_from_text(r.text)
                if found:
                    print(f"  [extra] {len(found)} emails from {url}")
                    emails.update(found)
        except:
            pass

    return list(emails)

def guess_emails(domain):
    parts = domain.split(".")
    # Get root domain only
    if len(parts) > 2:
        root = ".".join(parts[-2:])
    else:
        root = domain
    return [f"{prefix}@{root}" for prefix in EMAIL_PREFIXES]

def extract_all(domain, pages_data):
    all_emails = set()

    for page in pages_data:
        url = page["url"]
        content = page["content"]

        # HTML extraction
        found = extract_from_html(content)
        if found:
            print(f"  [html] {len(found)} emails at {url}")
        all_emails.update(found)

        # JS file extraction
        js_emails = extract_from_js_files(domain, content)
        if js_emails:
            print(f"  [js] {len(js_emails)} emails from JS at {url}")
        all_emails.update(js_emails)

    # Extra sources: security.txt, humans.txt, robots.txt etc
    extra = fetch_extra_sources(domain)
    all_emails.update(extra)

    # Pattern guessing — always run regardless of crawl results
    guessed = guess_emails(domain)
    if guessed:
        all_emails.update(guessed)
        print(f"  [guess] {len(guessed)} pattern emails added")

    # If crawl got nothing, log it clearly
    if not pages_data:
        print(f"  [warn] 0 pages crawled — domain may block crawlers, using guessed emails only")

    print(f"  [total] {len(all_emails)} raw emails found")
    return list(all_emails)