import re
from config import BLACKLIST

def is_valid_format(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def is_blacklisted(email):
    prefix = email.split("@")[0].lower()
    return any(b in prefix for b in BLACKLIST)

def is_example_email(email):
    # Remove known fake domains
    fake_domains = ["example.com", "example.org", "test.com", "fake.com"]
    domain = email.split("@")[1].lower()
    return domain in fake_domains

def is_junk(email):
    prefix = email.split("@")[0].lower()
    # Remove random hash strings
    if len(prefix) > 30:
        return True
    # Remove hex/hash looking strings
    if re.match(r'^[a-f0-9]{10,}$', prefix):
        return True
    # Remove encoded strings like u002B
    if "u002" in prefix:
        return True
    # Remove strings with too many numbers
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

def filter_by_domain(emails, domain):
    result = []
    root = domain.replace('www.', '')
    parts = root.split('.')
    if len(parts) > 2:
        root = '.'.join(parts[-2:])
    
    for email in emails:
        email_domain = email.split("@")[1].lower()
        if email_domain == root or email_domain.endswith("." + root):
            result.append(email)
        elif any(host in domain for host in ["vercel.app", "netlify.app", "github.io"]):
            result.append(email)
    return result