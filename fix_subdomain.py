content = open('modules/crawler.py', 'r', encoding='utf-8').read()
old = '        # Step 1: Discover subdomains\n        subdomains = discover_subdomains(domain, session)'
new = '        # Step 1: Discover subdomains\n        if scan_subdomains:\n            subdomains = discover_subdomains(domain, session)\n        else:\n            subdomains = []\n            log("[CRAWLER] Subdomain scan skipped")'
if old in content:
    print('FOUND')
    content = content.replace(old, new)
    open('modules/crawler.py', 'w', encoding='utf-8').write(content)
    print('DONE')
else:
    idx = content.find('# Step 1: Discover subdomains')
    print('NOT FOUND - context:')
    print(repr(content[idx:idx+100]))
