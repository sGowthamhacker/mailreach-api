import re
from config import BLACKLIST

def is_valid_format(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def is_blacklisted(email):
    prefix = email.split("@")[0].lower()
    return any(b in prefix for b in BLACKLIST)

def is_example_email(email):
    fake_domains = ["example.com", "example.org", "test.com", "fake.com"]
    domain = email.split("@")[1].lower()
    return domain in fake_domains

def is_junk(email):
    prefix = email.split("@")[0].lower()
    if len(prefix) > 30:
        return True
    if re.match(r'^[a-f0-9]{10,}$', prefix):
        return True
    if "u002" in prefix:
        return True
    if len(re.findall(r'\d', prefix)) > 5:
        return True
    return False

def clean_emails(emails):
    seen = set()
    clean = []
    for email in emails:
        email = email.lower().strip()
        if email in seen:
            continue
        if not is_valid_format(email):
            continue
        if is_blacklisted(email):
            continue
        if is_example_email(email):
            continue
        if is_junk(email):
            continue
        seen.add(email)
        clean.append(email)
    return clean

def get_root_domain(domain):
    # Remove www
    domain = domain.replace("www.", "")
    parts = domain.split(".")
    # Handle subdomains — get last 2 parts
    if len(parts) > 2:
        return ".".join(parts[-2:])
    return domain

def filter_by_domain(emails, domain):
    root = get_root_domain(domain)
    # Get base name without TLD — e.g. "vercel" from "vercel.app"
    base = root.split(".")[0]
    result = []
    for email in emails:
        email_domain = email.split("@")[1].lower()
        email_root = get_root_domain(email_domain)
        email_base = email_root.split(".")[0]
        # Match root domain exactly
        if email_root == root:
            result.append(email)
            continue
        # Match base name — catches vercel.app vs vercel.com
        if email_base == base:
            result.append(email)
            continue
        # Match subdomains
        if email_domain.endswith("." + root):
            result.append(email)
            continue

    print(f"  [filter] {len(result)}/{len(emails)} emails match domain {root} / base {base}")
    return result