with open('modules/crawler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_func = '''def fetch_with_playwright(url):
    try:
        import asyncio
        from playwright.async_api import async_playwright
        async def _fetch():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage","--disable-gpu"])
                page = await browser.new_page()
                await page.goto(url, timeout=15000, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                content = await page.content()
                await browser.close()
                return content
        return asyncio.run(_fetch())
    except Exception as e:
        print(f"[playwright] error: {e}")
        return None
'''

# Replace lines 227-246 (0-indexed)
new_lines = lines[:227] + [new_func] + lines[246:]

with open('modules/crawler.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Done!')