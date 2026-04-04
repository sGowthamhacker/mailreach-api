from modules.crawler import crawl
from modules.email_extractor import extract_all
from modules.cleaner import clean_emails, filter_by_domain
from modules.validator import validate_emails
from modules.filter_engine import filter_best
from modules.composer import compose
from modules.sender import send_all

# Step 1 - Get domain
domain = input("Enter domain: ").strip()

# Step 2 - Crawl + find emails
pages = crawl(domain)
emails = extract_all(domain, pages)
clean = clean_emails(emails)
filtered = filter_by_domain(clean, domain)
valid = validate_emails(filtered)
best = filter_best(valid)

# Step 3 - Show emails
print("\n--- EMAILS FOUND ---")
for i, e in enumerate(best):
    print(f"  [{i+1}] {e['email']}  (score: {e['score']})")

if not best:
    print("No emails found!")
    exit()

# Step 4 - User picks
print("\nWhich email to send to?")
choice = input("Enter number (or 'all'): ").strip()

if choice == "all":
    targets = [e["email"] for e in best]
else:
    idx = int(choice) - 1
    targets = [best[idx]["email"]]

# Step 5 - Compose
message = compose(domain)
print("\n--- MESSAGE PREVIEW ---")
print("To:", targets)
print("Subject:", message["subject"])
print("Body:")
print(message["body"])

# Step 6 - Confirm
confirm = input("\nSend this email? (yes/no): ").strip().lower()

if confirm == "yes":
    results = send_all(targets, message["subject"], message["body"])
    print("\nResults:")
    for r in results:
        print(f"  {r['to']} → {r['status']} via {r['service']}")
else:
    print("Cancelled.")