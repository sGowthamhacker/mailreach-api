import requests
import time
from config import (
    BREVO_API_KEY, SENDER_EMAIL,
    DELAY_BETWEEN_EMAILS, MAX_PER_HOUR
)

hour_sent = 0

def send_email(to_addr, subject, body):
    global hour_sent
    try:
        if not BREVO_API_KEY:
            print("  [brevo] API key missing!")
            return {"to": to_addr, "status": "failed", "service": "none"}

        if hour_sent >= MAX_PER_HOUR:
            print("  [limit] Hour limit reached, waiting 60s")
            time.sleep(60)
            hour_sent = 0

        res = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "sender": {"email": SENDER_EMAIL},
                "to": [{"email": to_addr}],
                "subject": subject,
                "textContent": body
            },
            timeout=10
        )

        if res.status_code == 201:
            hour_sent += 1
            print(f"  [brevo] Sent to {to_addr}")
            return {"to": to_addr, "status": "sent", "service": "brevo"}
        else:
            print(f"  [brevo] Failed: {res.text}")
            return {"to": to_addr, "status": "failed", "service": "none"}

    except Exception as e:
        print(f"  [brevo] Error: {e}")
        return {"to": to_addr, "status": "failed", "service": "none"}

def send_all(targets, subject, body):
    results = []
    total = len(targets)
    for i, to_addr in enumerate(targets):
        print(f"[{i+1}/{total}] Sending to {to_addr}")
        result = send_email(to_addr, subject, body)
        results.append(result)
        if i < total - 1:
            print(f"  [wait] {DELAY_BETWEEN_EMAILS}s...")
            time.sleep(DELAY_BETWEEN_EMAILS)
    sent = len([r for r in results if r["status"] == "sent"])
    failed = len([r for r in results if r["status"] == "failed"])
    print(f"\n[done] Sent: {sent} | Failed: {failed}")
    return results