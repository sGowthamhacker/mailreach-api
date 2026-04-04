import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\\Users\\gowtham\\email-tool')
from modules.crawler import crawl
from modules.email_extractor import extract_all
from modules.cleaner import clean_emails, filter_by_domain
from modules.validator import validate_emails
from modules.filter_engine import filter_best
from modules.bounty_detector import detect_bounty
import json

domain = "producthunt.com"
pages = crawl(domain)
emails = extract_all(domain, pages)
clean = clean_emails(emails)
filtered = filter_by_domain(clean, domain)
valid = validate_emails(filtered)
best = filter_best(valid)
bounty = detect_bounty(pages)
print(json.dumps({"emails": [{"email": e["email"], "score": e["score"], "domain": e["domain"], "mx_ok": e["mx_ok"]} for e in best], "bounty": bounty}))
