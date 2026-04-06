content = open('main.py', 'r', encoding='utf-8').read()

fixes = [
    ('send(f" Scanning {domain}...", "info")', 'send(f"Scanning {domain}...", "info")'),
    ('send(f" Building URL queue...", "info")', 'send(f"Building URL queue...", "info")'),
    ('send(f" Crawled: {msg.replace(\'[ok]\',\'\').strip()}", "ok")', 'send(f"Crawled: {msg.replace(\'[ok]\',\'\').strip()}", "ok")'),
    ('send(f" Skipped: {msg.replace(\'[skip]\',\'\').strip()}", "info")', 'send(f"Skipped: {msg.replace(\'[skip]\',\'\').strip()}", "info")'),
    ('send(f" {msg.replace(\'[done]\',\'\').strip()}", "ok")', 'send(f"Done: {msg.replace(\'[done]\',\'\').strip()}", "ok")'),
    ('send(f" {msg}", "info")', 'send(f"{msg}", "info")'),
    ('send(f" Crawled {len(pages)} pages  extracting emails...", "info")', 'send(f"Crawled {len(pages)} pages - extracting emails...", "info")'),
    ('send(f" Found {len(emails)} raw emails", "info")', 'send(f"Found {len(emails)} raw emails", "info")'),
    ('send(f" Cleaned to {len(clean)} emails", "info")', 'send(f"Cleaned to {len(clean)} emails", "info")'),
    ('send(f" Validated {len(valid)} emails", "ok")', 'send(f"Validated {len(valid)} emails", "ok")'),
    ('send(f" Selected {len(best)} best emails", "ok")', 'send(f"Selected {len(best)} best emails", "ok")'),
    ('send(f" Bug bounty', 'send(f"Bug bounty'),
    ('send(f" No bounty', 'send(f"No bounty'),
    ('send(f" Error', 'send(f"Error'),
]

for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        print(f'Fixed: {old[:40]}')

open('main.py', 'w', encoding='utf-8').write(content)
print('DONE')
