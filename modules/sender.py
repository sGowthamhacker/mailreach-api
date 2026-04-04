import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import (
    GMAIL_USER, GMAIL_APP_PASSWORD, GMAIL_DAILY_LIMIT,
    BREVO_USER, BREVO_SMTP_KEY, BREVO_SMTP_SERVER,
    BREVO_PORT, BREVO_DAILY_LIMIT,
    DELAY_BETWEEN_EMAILS, MAX_PER_HOUR
)

# Counters
gmail_sent = 0
brevo_sent = 0
hour_sent = 0

def build_email(from_addr, to_addr, subject, body):
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    return msg

def send_via_gmail(to_addr, subject, body):
    global gmail_sent
    try:
        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            print(f"  [gmail] ❌ Credentials missing!")
            print(f"  [gmail] USER: {GMAIL_USER}")
            print(f"  [gmail] PASS: {'set' if GMAIL_APP_PASSWORD else 'NOT SET'}")
            return False
        msg = build_email(GMAIL_USER, to_addr, subject, body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_addr, msg.as_string())
        gmail_sent += 1
        print(f"  [gmail] ✅ Sent to {to_addr} (total: {gmail_sent})")
        return True
    except Exception as e:
        print(f"  [gmail] ❌ Failed → {e}")
        return False

def send_via_brevo(to_addr, subject, body):
    global brevo_sent
    try:
        msg = build_email(BREVO_USER, to_addr, subject, body)
        # timeout=10 prevents hanging
        with smtplib.SMTP(BREVO_SMTP_SERVER, BREVO_PORT, timeout=10) as server:
            server.starttls()
            server.login(BREVO_USER, BREVO_SMTP_KEY)
            server.sendmail(BREVO_USER, to_addr, msg.as_string())
        brevo_sent += 1
        print(f"  [brevo] ✅ Sent to {to_addr} (total: {brevo_sent})")
        return True
    except Exception as e:
        print(f"  [brevo] ❌ Failed → {e}")
        return False

def send_email(to_addr, subject, body):
    global gmail_sent, brevo_sent, hour_sent

    # Check hour limit
    if hour_sent >= MAX_PER_HOUR:
        print(f"  [limit] ⚠️ Hour limit reached — waiting 60s")
        time.sleep(60)
        hour_sent = 0

    # Try Gmail first
    if gmail_sent < GMAIL_DAILY_LIMIT:
        success = send_via_gmail(to_addr, subject, body)
        if success:
            hour_sent += 1
            return {"to": to_addr, "status": "sent", "service": "gmail"}
        else:
            print("  [switch] Gmail failed → trying Brevo")

    # Auto switch to Brevo
    if brevo_sent < BREVO_DAILY_LIMIT:
        success = send_via_brevo(to_addr, subject, body)
        if success:
            hour_sent += 1
            return {"to": to_addr, "status": "sent", "service": "brevo"}

    # Both failed
    print(f"  [error] ❌ Both failed for {to_addr}")
    return {"to": to_addr, "status": "failed", "service": "none"}

def send_all(targets, subject, body):
    results = []
    total = len(targets)

    print(f"\n[sender] Starting — {total} emails")
    print(f"[sender] Gmail: {GMAIL_DAILY_LIMIT}/day | Brevo: {BREVO_DAILY_LIMIT}/day")
    print(f"[sender] Delay: {DELAY_BETWEEN_EMAILS}s | Max/hour: {MAX_PER_HOUR}\n")

    for i, to_addr in enumerate(targets):
        print(f"[{i+1}/{total}] Sending to {to_addr}")
        result = send_email(to_addr, subject, body)
        results.append(result)

        # Delay between emails
        if i < total - 1:
            print(f"  [wait] {DELAY_BETWEEN_EMAILS}s...")
            time.sleep(DELAY_BETWEEN_EMAILS)

    sent = len([r for r in results if r["status"] == "sent"])
    failed = len([r for r in results if r["status"] == "failed"])
    print(f"\n[done] Sent: {sent} | Failed: {failed}")
    return results