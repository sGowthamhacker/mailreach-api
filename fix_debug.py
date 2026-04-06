lines = open('main.py', encoding='utf-8').readlines()

new_func = [
    '@app.get("/debug-page")\n',
    'async def debug_page():\n',
    '    try:\n',
    '        import subprocess\n',
    '        subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)\n',
    '        from playwright.async_api import async_playwright\n',
    '        async with async_playwright() as p:\n',
    '            browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage","--disable-gpu"])\n',
    '            page = await browser.new_page()\n',
    '            await page.goto("https://gowthamprofile.vercel.app/", timeout=15000)\n',
    '            await page.wait_for_timeout(2000)\n',
    '            content = await page.content()\n',
    '            await browser.close()\n',
    '            return {"length": len(content), "gmail": "gmail" in content.lower(), "snippet": content[:500]}\n',
    '    except Exception as e:\n',
    '        return {"error": str(e)}\n',
    '\n',
]

'        result = subprocess.run(["python", "-m", "playwright", "install", "chromium"], capture_output=False, check=False)\n',
open('main.py', 'w', encoding='utf-8').writelines(new_lines)
print('Done!')