import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cache MX results per domain to avoid duplicate lookups
_mx_cache = {}

BIG_PROVIDERS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "linkedin.com", "microsoft.com", "google.com", "apple.com",
    "facebook.com", "twitter.com", "amazon.com", "protonmail.com",
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

def check_single_email(email):
    try:
        email = email.strip().lower()
        if "@" not in email:
            return None
        email_domain = email.split("@")[1]

        # Big providers always have MX
        if any(p in email_domain for p in BIG_PROVIDERS):
            return {"email": email, "domain": email_domain,
                    "mx_ok": True, "smtp_ok": False,
                    "score": 2, "valid": True}

        mx_hosts = has_mx_record(email_domain)
        mx_ok = len(mx_hosts) > 0

        return {"email": email, "domain": email_domain,
                "mx_ok": mx_ok, "smtp_ok": False,
                "score": 3 if mx_ok else 1, "valid": True}
    except:
        return None

def validate_emails(emails, website_domain=None):
    if not emails:
        return []

    print(f"\n[validator] Checking {len(emails)} emails (MX only, no SMTP)...")

    # Deduplicate
    unique = list(set(e.strip().lower() for e in emails if "@" in e))
    print(f"[validator] {len(unique)} unique emails after dedup")

    results = []
    # Use ThreadPoolExecutor with small worker count
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_single_email, email): email for email in unique}
        for future in as_completed(futures, timeout=60):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                pass

    valid = [r for r in results if r.get("mx_ok")]
    invalid = [r for r in results if not r.get("mx_ok")]

    print(f"[validator] MX ok: {len(valid)} | No MX: {len(invalid)}")

    # Return ALL emails, sorted by mx_ok first
    all_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    print(f"[validator] Done - returning {len(all_results)} emails")
    return all_results