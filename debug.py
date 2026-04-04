import requests
from bs4 import BeautifulSoup
import re

domain = "htwth.vercel.app"
url = f"https://{domain}"
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

# Step 1 - Get main page
r = requests.get(url, headers=headers, timeout=10)
print("Main page size:", len(r.text))

# Step 2 - Find all JS file links
soup = BeautifulSoup(r.text, "html.parser")
js_files = []

for tag in soup.find_all("script", src=True):
    src = tag["src"]
    if src.startswith("http"):
        js_files.append(src)
    else:
        js_files.append(f"https://{domain}{src}")

print(f"\nFound {len(js_files)} JS files:")
for js in js_files:
    print(f"  {js}")

# Step 3 - Search emails in each JS file
print("\n--- SEARCHING JS FILES FOR EMAILS ---")
all_emails = set()

for js_url in js_files:
    try:
        jr = requests.get(js_url, headers=headers, timeout=10)
        found = re.findall(EMAIL_REGEX, jr.text)
        if found:
            print(f"\n✅ Found in {js_url}:")
            for e in found:
                print(f"   {e}")
                all_emails.add(e)
        else:
            print(f"  ❌ Nothing in {js_url}")
    except Exception as e:
        print(f"  [error] {js_url} → {e}")

print(f"\n--- ALL EMAILS FOUND ---")
print(list(all_emails) if all_emails else "NONE FOUND")