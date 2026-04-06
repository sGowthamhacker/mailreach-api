from modules.crawler import crawl
from modules.email_extractor import extract_all

print("Testing crawler...")
pages = crawl('gowthamprofile.vercel.app')
print(f'Crawler returned {len(pages)} pages')

if pages:
    print(f'Page 0 URL: {pages[0]["url"]}')
    print(f'Page 0 content length: {len(pages[0]["content"])}')

print("\nTesting extractor...")
emails = extract_all('gowthamprofile.vercel.app', pages)
print(f'Extractor found {len(emails)} emails: {emails}')