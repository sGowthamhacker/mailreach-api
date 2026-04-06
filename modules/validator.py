import dns.resolver
import smtplib
import ssl
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

def has_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX', lifetime=5)
        return [str(r.exchange).rstrip('.') for r in records]
    except:
        return []

def smtp_handshake(email, mx_host):
    """
    Try SMTP verification.
    Returns: 'verified', 'exists', 'rejected', 'unknown'
    """
    for port in [587, 465, 25]:
        try:
            if port == 465:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(mx_host, port, timeout=5, context=context)
            else:
                server = smtplib.SMTP(timeout=5)
                server.connect(mx_host, port)
                server.ehlo()
                if port == 587:
                    try:
                        server.starttls()
                        server.ehlo()
                    except:
                        pass

            server.helo('verify.local')
            
            code, _ = server.mail('verify@verify.local')
            if code != 250:
                server.quit()
                continue
            
            code, msg = server.rcpt(email)
            server.quit()
            
            if code in [250, 251]:
                return 'verified'
            elif code in [550, 551, 553]:
                return 'rejected'
            else:
                return 'unknown'
                
        except smtplib.SMTPConnectError:
            continue
        except smtplib.SMTPServerDisconnected:
            continue
        except socket.timeout:
            continue
        except Exception as e:
            continue
    
    return 'unknown'

def check_single_email(email):
    email_domain = email.split("@")[1].lower()
    
    # Step 1: MX check
    mx_hosts = has_mx_record(email_domain)
    if not mx_hosts:
        print(f"  [mx] {email_domain} -> No MX records")
        return {
            "email": email,
            "domain": email_domain,
            "mx_ok": False,
            "smtp_ok": False,
            "smtp_status": "no_mx",
            "valid": False
        }
    
    print(f"  [mx] {email_domain} -> MX: {mx_hosts[0]}")
    
    # Step 2: SMTP check
    mx_host = mx_hosts[0]
    smtp_status = smtp_handshake(email, mx_host)
    
    print(f"  [smtp] {email} -> {smtp_status}")
    
    # Big providers block SMTP verification - trust MX only
    BIG_PROVIDERS = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
        "linkedin.com", "microsoft.com", "google.com", "apple.com",
        "facebook.com", "twitter.com", "instagram.com"
    ]
    is_big_provider = any(p in email_domain for p in BIG_PROVIDERS)
    
    if is_big_provider:
        # For big providers, MX = valid (they block SMTP checks)
        smtp_ok = True
        print(f"  [smtp] {email_domain} is big provider - trusting MX")
    else:
        smtp_ok = smtp_status == 'verified'
    
    return {
        "email": email,
        "domain": email_domain,
        "mx_ok": True,
        "smtp_ok": smtp_ok,
        "smtp_status": smtp_status,
        "valid": True
    }

def validate_emails(emails, website_domain=None):
    if not emails:
        return []
    
    print(f"\n[validator] Checking {len(emails)} emails...")
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_single_email, email): email for email in emails}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                email = futures[future]
                results.append({
                    "email": email,
                    "domain": email.split("@")[1] if "@" in email else "",
                    "mx_ok": False,
                    "smtp_ok": False,
                    "smtp_status": "error",
                    "valid": False
                })
    
    valid = [r for r in results if r["valid"]]
    print(f"  [done] {len(valid)}/{len(emails)} emails valid")
    return results