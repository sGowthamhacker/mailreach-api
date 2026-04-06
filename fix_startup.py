lines = open('modules/crawler.py', encoding='utf-8').readlines()

new_block = [
    '        HOSTING_PLATFORMS = ["vercel.app", "netlify.app", "github.io", "pages.dev"]\n',
    '        use_playwright = any(p in domain for p in HOSTING_PLATFORMS)\n',
    '        if use_playwright and len(pages_data) == 0:\n',
    '            content = fetch_with_playwright(url)\n',
    '            if content:\n',
    '                log(f"[ok] {url}")\n',
    '                pages_data.append({"url": url, "content": content})\n',
    '                continue\n',
    '            else:\n',
    '                log(f"[skip] {url}")\n',
    '                continue\n',
    '        r = safe_get(url, session)\n',
    '        if not r:\n',
    '            log(f"[skip] {url}")\n',
    '            continue\n',
    '        log(f"[ok] {url}")\n',
    '        pages_data.append({"url": url, "content": r.text})\n',
]

new_lines = lines[:385] + new_block + lines[399:]
open('modules/crawler.py', 'w', encoding='utf-8').writelines(new_lines)
print('Done!')