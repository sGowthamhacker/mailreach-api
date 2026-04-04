import dns.resolver
import smtplib
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

def has_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX', lifetime=3)
        return [str(r.exchange).rstrip('.') for r in records]
    except:
        return []

def smtp_handshake(email, mx_host):
    for port in [25, 587, 465]:
        try:
            if port == 465:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(mx_host, port, timeout=2, context=context)
            else:
                server = smtplib.SMTP(timeout=2)
                server.connect(mx_host, port)
            server.helo('check.local')
            code, _ = server.mail('verify@check.local')
            if code != 250:
                server.quit()
                continue
            code, _ = server.rcpt(email)
            server.quit()
            return code in [250, 251]
        except:
            continue
    return False

def check_single_email(email):
    email_domain = email.split("@")[1].lower()

    mx_hosts = has_mx_record(email_domain)
    if not mx_hosts:
        print(f"  [mx] {email_domain} -> No MX")
        return {
            "email": email,
            "domain": email_domain,
            "mx_ok": False,
            "smtp_ok": False,
            "valid": False
        }

    print(f"  [mx] {email_domain} -> MX found")

    mx_host = mx_hosts[0]
    smtp_ok = smtp_handshake(email, mx_host)
    print(f"  [smtp] {email} -> {'250 OK' if smtp_ok else 'rejected'}")

    return {
        "email": email,
        "domain": email_domain,
        "mx_ok": True,
        "smtp_ok": smtp_ok,
        "valid": True  # MX exists = valid enough
    }

def validate_emails(emails, website_domain=None):
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_single_email, email): email for email in emails}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                email = futures[future]
                results.append({
                    "email": email,
                    "domain": email.split("@")[1],
                    "mx_ok": False,
                    "smtp_ok": False,
                    "valid": False
                })

    valid = [r for r in results if r["valid"]]
    print(f"  [done] {len(valid)}/{len(emails)} emails valid")
    return results