from config import PRIORITY, BLACKLIST

JUNK_PATTERNS = [
    "bounce", "automated", "mailer-daemon",
    "daemon", "unsubscribe", "donotreply"
]

def is_junk_pattern(email):
    prefix = email.split("@")[0].lower()
    return any(j in prefix for j in JUNK_PATTERNS)

def get_priority_score(email):
    prefix = email.split("@")[0].lower()
    if prefix in PRIORITY:
        return len(PRIORITY) - PRIORITY.index(prefix)
    return 1  # still keep it, just low score

def filter_best(valid_emails):
    results = []

    for item in valid_emails:
        email = item["email"]

        # Only need MX to be valid — smtp_ok is bonus
        if not item.get("mx_ok"):
            print(f"  [skip] {email} -> no MX")
            continue

        # Skip junk
        if is_junk_pattern(email):
            print(f"  [skip] {email} -> junk")
            continue

        score = get_priority_score(email)

        if item.get("smtp_ok"):
            score += 3

        results.append({**item, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"  [done] {len(results)} best emails selected")
    return results