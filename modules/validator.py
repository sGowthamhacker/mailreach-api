import dns.resolver
import smtplib
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

BIG_PROVIDERS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "linkedin.com", "microsoft.com", "google.com", "apple.com",
    "facebook.com", "twitter.com", "instagram.com", "amazon.com",
    "protonmail.com", "icloud.com", "me.com", "mac.com"
]

_mx_cache = {}

def has_mx_record(domain):
    if domain in _mx_cache:
        return _mx_cache[domain]
    try:
        records = dns.resolver.resolve(domain, 'MX', lifetime=4)
        result = [str(r.exchange).rstrip('.') for r in records]
        _mx_cache[domain] = result
        return result
    except:
        _mx_cache[domain] = []
        return []

def smtp_handshake(email, mx_host):
    try:
        server = smtplib.SMTP(timeout=4)
        server.connect(mx_host, 25)
        server.ehlo()
        server.helo('verify.local')
        code, _ = server.mail('verify@verify.local')
        if code != 250:
            server.quit()
            return 'unknown'
        code, msg = server.rcpt(email)
        server.quit()
        if code in [250, 251]:
            return 'verified'
        elif code in [550, 551, 553]:
            return 'rejected'
        return 'unknown'
    except:
        return 'unknown'

def check_single_email(email):
    email_domain = email.split("@")[1].lower()
    is_big = any(p in email_domain for p in BIG_PROVIDERS)
    if is_big:
        mx_hosts = has_mx_record(email_domain)
        if mx_hosts:
            print(f"  [ok] {email} -> big provider, MX ok")
            return {"email": email, "domain": email_domain,
                    "mx_ok": True, "smtp_ok": True,
                    "smtp_status": "big_provider", "valid": True}
        return {"email": email, "domain": email_domain,
                "mx_ok": False, "smtp_ok": False,
                "smtp_status": "no_mx", "valid": False}
    mx_hosts = has_mx_record(email_domain)
    if not mx_hosts:
        return {"email": email, "domain": email_domain,
                "mx_ok": False, "smtp_ok": False,
                "smtp_status": "no_mx", "valid": False}
    smtp_status = smtp_handshake(email, mx_hosts[0])
    smtp_ok = smtp_status == 'verified'
    print(f"  [smtp] {email} -> {smtp_status}")
    return {"email": email, "domain": email_domain,
            "mx_ok": True, "smtp_ok": smtp_ok,
            "smtp_status": smtp_status, "valid": True}

def validate_emails(emails, website_domain=None):
    if not emails:
        return []
    print(f"\n[validator] Checking {len(emails)} emails with 20 workers...")
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_single_email, email): email for email in emails}
        for future in as_completed(futures, timeout=120):
            try:
                results.append(future.result())
            except Exception as e:
                email = futures[future]
                results.append({
                    "email": email,
                    "domain": email.split("@")[1] if "@" in email else "",
                    "mx_ok": False, "smtp_ok": False,
                    "smtp_status": "error", "valid": False
                })
    valid = [r for r in results if r["valid"]]
    print(f"  [done] {len(valid)}/{len(emails)} valid")
    return results


