import dns.resolver
import smtplib
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

_mx_cache = {}

BIG_PROVIDERS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "linkedin.com", "microsoft.com", "google.com", "apple.com",
    "facebook.com", "twitter.com", "amazon.com", "protonmail.com",
    "icloud.com", "me.com", "mac.com"
]

PRIORITY_PREFIXES = [
    "security", "contact", "info", "support", "admin", "hello",
    "team", "sales", "help", "disclosure", "vdp", "bbp", "bounty",
    "privacy", "legal", "trust", "abuse", "press", "media",
    "ceo", "cto", "cfo", "founder", "hr", "careers", "billing",
]

def has_mx_record(domain):
    if domain in _mx_cache:
        return _mx_cache[domain]
    try:
        records = dns.resolver.resolve(domain, "MX", lifetime=3)
        result = [str(r.exchange).rstrip(".") for r in records]
        _mx_cache[domain] = result
        return result
    except:
        _mx_cache[domain] = []
        return []

def smtp_check(email, mx_host):
    try:
        server = smtplib.SMTP(timeout=5)
        server.connect(mx_host, 25)
        server.ehlo("verify.local")
        code, _ = server.mail("verify@verify.local")
        if code != 250:
            server.quit()
            return False
        code, _ = server.rcpt(email)
        server.quit()
        return code in [250, 251]
    except:
        return False

def get_score(email, mx_ok, smtp_ok):
    score = 0
    prefix = email.split("@")[0].lower()
    # MX score
    if mx_ok:
        score += 3
    # SMTP score
    if smtp_ok:
        score += 5
    # Priority prefix score
    if prefix in PRIORITY_PREFIXES:
        score += 3
    elif any(p in prefix for p in PRIORITY_PREFIXES):
        score += 1
    return score

def check_single_email(email):
    try:
        email = email.strip().lower()
        if "@" not in email:
            return None
        email_domain = email.split("@")[1]

        # Big providers - always valid
        if any(p in email_domain for p in BIG_PROVIDERS):
            score = get_score(email, True, True)
            return {
                "email": email, "domain": email_domain,
                "mx_ok": True, "smtp_ok": True,
                "status": "big_provider", "score": score, "valid": True
            }

        # MX check
        mx_hosts = has_mx_record(email_domain)
        mx_ok = len(mx_hosts) > 0

        if not mx_ok:
            return {
                "email": email, "domain": email_domain,
                "mx_ok": False, "smtp_ok": False,
                "status": "no_mx", "score": 0, "valid": False
            }

        # SMTP check
        smtp_ok = smtp_check(email, mx_hosts[0])
        status = "smtp_verified" if smtp_ok else "mx_only"
        score = get_score(email, mx_ok, smtp_ok)

        print(f"  [{status}] {email} score={score}")
        return {
            "email": email, "domain": email_domain,
            "mx_ok": mx_ok, "smtp_ok": smtp_ok,
            "status": status, "score": score, "valid": True
        }
    except Exception as e:
        print(f"  [error] {email}: {e}")
        return None

def validate_emails(emails, website_domain=None):
    if not emails:
        return []

    # Deduplicate
    unique = list(set(e.strip().lower() for e in emails if "@" in e))
    print(f"\n[validator] Checking {len(unique)} unique emails...")

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_single_email, email): email for email in unique}
        for future in as_completed(futures, timeout=120):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"[validator] Error: {e}")

    # Sort by score descending
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    valid = [r for r in results if r.get("mx_ok")]
    invalid = [r for r in results if not r.get("mx_ok")]

    print(f"[validator] MX valid: {len(valid)} | No MX: {len(invalid)}")
    print(f"[validator] SMTP verified: {len([r for r in valid if r.get('smtp_ok')])}")

    # Return ALL - valid first then invalid
    return valid + invalid