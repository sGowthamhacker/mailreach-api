from config import PRIORITY, BLACKLIST

# Extra junk patterns to remove
JUNK_PATTERNS = [
    "applications", "accommodations", "careers",
    "hiring", "bounce", "automated", "invoice"
]

def is_personal_email(email):
    prefix = email.split("@")[0].lower()
    # Personal emails have dots (firstname.lastname)
    parts = prefix.split(".")
    if len(parts) >= 2 and all(p.isalpha() for p in parts):
        return True
    return False

def is_junk_pattern(email):
    prefix = email.split("@")[0].lower()
    return any(j in prefix for j in JUNK_PATTERNS)

def get_priority_score(email):
    prefix = email.split("@")[0].lower()
    if prefix in PRIORITY:
        return len(PRIORITY) - PRIORITY.index(prefix)
    return 0

def filter_best(valid_emails):
    results = []

    for item in valid_emails:
        email = item["email"]

        # Only keep smtp verified emails
        if not item.get("smtp_ok") and not item.get("mx_ok"):
            print(f"  [skip] {email} -> not verified")
            continue

        # Skip junk patterns
        if is_junk_pattern(email):
            print(f"  [skip] {email} -> junk pattern")
            continue

        # Skip personal emails
        if is_personal_email(email):
            print(f"  [skip] {email} -> personal email")
            continue

        score = get_priority_score(email)

        # Bonus score for smtp verified
        if item.get("smtp_ok"):
            score += 2

        results.append({**item, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"  [done] {len(results)} best emails selected")
    return results

def pick_best_per_domain(filtered_emails):
    best = {}
    for item in filtered_emails:
        domain = item["domain"]
        if domain not in best:
            best[domain] = item
        else:
            if item["score"] > best[domain]["score"]:
                best[domain] = item
    return list(best.values())