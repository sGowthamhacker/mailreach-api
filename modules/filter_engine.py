from config import PRIORITY, BLACKLIST

JUNK_PATTERNS = [
    "bounce", "automated", "mailer-daemon", "daemon",
    "unsubscribe", "donotreply", "noreply", "no-reply",
    "notifications", "alerts", "system", "robot",
]

def is_junk(email):
    prefix = email.split("@")[0].lower()
    return any(j in prefix for j in JUNK_PATTERNS)

def filter_best(validated_emails):
    results = []
    for item in validated_emails:
        email = item["email"]

        # Skip junk
        if is_junk(email):
            print(f"  [junk] {email}")
            continue

        results.append(item)

    # Sort by score
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    print(f"  [done] {len(results)} emails after junk filter")
    return results