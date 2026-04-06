import re
import sys
import json
import requests
from bs4 import BeautifulSoup
from config import EMAIL_PREFIXES

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# CONFIGURATION & PATTERNS
# ============================================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Stronger email regex patterns
EMAIL_PATTERNS = {
    "primary": r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    "obfuscated_at": r'([a-zA-Z0-9._\-]+)\s+at\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
    "obfuscated_bracket": r'([a-zA-Z0-9._\-]+)\s*\[\s*at\s*\]\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
    "obfuscated_space": r'([a-zA-Z0-9._\-]+)\s+\(\s*at\s*\)\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
}

# ============================================================================
# FAKE EMAIL DETECTION - SMART FILTERING
# ============================================================================

def is_fake_email(email):
    """
    Smart filtering: Keep real business emails, remove only obvious fakes.
    
    KEEP: support@, info@, contact@, hello@, sales@, team@, etc.
    REMOVE: react@, redux@, example.com, test.com, placeholder patterns
    """
    if not email or "@" not in email:
        return True
    
    try:
        prefix, domain = email.rsplit("@", 1)
    except:
        return True
    
    domain = domain.lower().strip()
    prefix = prefix.lower().strip()
    
    # ===== DEFINITELY FAKE =====
    
    # Fake/test domains
    FAKE_DOMAINS = {
        "example.com", "example.org", "example.net",
        "test.com", "test.org", "test.net",
        "fake.com", "fake.org", "fake.net",
        "domain.com", "email.com", "yoursite.com", "website.com",
        "sentry.io", "w3.org", "schema.org", "googleapis.com",
        "gstatic.com", "cloudflare.com", "localhost", "127.0.0.1",
        "github.com", "github.io", "gitlab.com", "bitbucket.org",
        "user.noreply.github.com", "notification@github.com",
    }
    if domain in FAKE_DOMAINS:
        print(f"[filter] ✗ {email} - fake domain")
        return True
    
    # Library/package names (ONLY if entire prefix matches)
    LIBRARY_NAMES = {
        "react", "redux", "angular", "vue", "node", "npm", "webpack",
        "babel", "eslint", "prettier", "jest", "mocha", "chai",
        "lodash", "axios", "express", "django", "flask", "spring",
        "bootstrap", "tailwind", "material", "semantic", "bulma",
        "jquery", "backbone", "ember", "svelte", "nextjs", "nuxt",
        "typescript", "javascript", "python", "java", "golang",
    }
    if prefix in LIBRARY_NAMES:
        print(f"[filter] ✗ {email} - library name")
        return True
    
    # File extensions
    if any(ext in prefix for ext in [".png", ".jpg", ".svg", ".gif", ".webp", ".pdf", ".mp4", ".mp3"]):
        print(f"[filter] ✗ {email} - file extension")
        return True
    
    # URLs masquerading as emails
    if "://" in email or email.count("/") > 1:
        print(f"[filter] ✗ {email} - URL pattern")
        return True
    
    # Too short (less than 2 chars before @)
    if len(prefix) < 2:
        print(f"[filter] ✗ {email} - too short")
        return True
    
    # Purely numeric
    if prefix.isdigit() or domain.split(".")[0].isdigit():
        print(f"[filter] ✗ {email} - numeric only")
        return True
    
    # ===== KEEP EVERYTHING ELSE =====
    # support@, info@, contact@, hello@, sales@, team@, business-email@, etc.
    print(f"[filter] ✓ {email} - valid business email")
    return False


# ============================================================================
# EMAIL EXTRACTION - MULTIPLE METHODS
# ============================================================================

def extract_emails_from_text(text, source="text"):
    """
    Extract emails using multiple regex patterns.
    Handles: standard emails, obfuscated formats, etc.
    """
    found = set()
    
    if not text or len(text) < 5:
        return list(found)
    
    print(f"[extract-{source}] Scanning {len(text)} chars")
    
    # 1. Primary regex (standard emails)
    primary = re.findall(EMAIL_PATTERNS["primary"], text)
    if primary:
        print(f"[extract-{source}] Primary regex: {len(primary)} found")
        found.update(primary)
    
    # 2. Obfuscated "name at domain" format
    obf_at = re.findall(EMAIL_PATTERNS["obfuscated_at"], text, re.IGNORECASE)
    if obf_at:
        print(f"[extract-{source}] Obfuscated 'at': {len(obf_at)} found")
        for name, domain in obf_at:
            found.add(f"{name}@{domain}")
    
    # 3. Obfuscated with brackets [at]
    obf_bracket = re.findall(EMAIL_PATTERNS["obfuscated_bracket"], text, re.IGNORECASE)
    if obf_bracket:
        print(f"[extract-{source}] Obfuscated [at]: {len(obf_bracket)} found")
        for name, domain in obf_bracket:
            found.add(f"{name}@{domain}")
    
    # 4. Obfuscated with parentheses (at)
    obf_space = re.findall(EMAIL_PATTERNS["obfuscated_space"], text, re.IGNORECASE)
    if obf_space:
        print(f"[extract-{source}] Obfuscated (at): {len(obf_space)} found")
        for name, domain in obf_space:
            found.add(f"{name}@{domain}")
    
    # Clean and normalize
    clean = set()
    for email in found:
        email = email.strip(".,;:\"'><)([]{}`|\\")
        
        # Validate format
        if "@" not in email or email.count("@") > 1:
            continue
        
        parts = email.split("@")
        if len(parts) != 2:
            continue
        
        prefix, domain = parts
        
        # Validate parts
        if len(prefix) < 2 or len(domain) < 5:
            continue
        
        if "." not in domain:
            continue
        
        # Normalize case
        email = email.lower()
        clean.add(email)
    
    print(f"[extract-{source}] After cleanup: {len(clean)} valid emails")
    return list(clean)


def extract_mailto_links(html):
    """
    Extract emails from mailto: links in HTML.
    These are HIGH confidence (directly linked contact info).
    """
    emails = set()
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Find all <a> tags with mailto:
        mailto_links = soup.find_all("a", href=re.compile(r'^mailto:', re.IGNORECASE))
        
        print(f"[mailto] Found {len(mailto_links)} mailto links")
        
        for link in mailto_links:
            href = link.get("href", "").lower()
            
            # Extract email from mailto:email@domain.com?subject=...
            email_match = re.search(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', href)
            
            if email_match:
                email = email_match.group(1).lower().strip()
                
                if not is_fake_email(email):
                    emails.add(email)
                    print(f"[mailto] ✓ {email}")
    
    except Exception as e:
        print(f"[mailto] Error: {e}")
    
    return list(emails)


def extract_from_html(content):
    """
    Extract emails from HTML content using multiple methods:
    1. Mailto links (highest confidence)
    2. Raw text extraction
    3. Meta tags and attributes
    4. JSON-LD structured data
    5. HTML comments
    """
    all_emails = set()
    
    print(f"\n{'='*70}")
    print(f"[HTML] === HTML EXTRACTION PIPELINE ===")
    print(f"[HTML] Content size: {len(content)} bytes")
    print(f"{'='*70}")
    
    try:
        # 1. MAILTO LINKS (highest confidence)
        print(f"\n[HTML] Step 1: Extracting mailto: links...")
        mailto_emails = extract_mailto_links(content)
        print(f"[HTML] Mailto found: {len(mailto_emails)}")
        all_emails.update(mailto_emails)
        
        # 2. TEXT EXTRACTION
        print(f"\n[HTML] Step 2: Extracting from text content...")
        text_emails = extract_emails_from_text(content, source="html-text")
        print(f"[HTML] Text found: {len(text_emails)}")
        all_emails.update(text_emails)
        
        # 3. SOUP PARSING (attributes, meta tags, etc.)
        print(f"\n[HTML] Step 3: Parsing HTML structure...")
        soup = BeautifulSoup(content, "html.parser")
        
        # Meta tags
        for meta in soup.find_all("meta"):
            content_val = meta.get("content", "")
            name_val = meta.get("name", "")
            
            if content_val and "@" in content_val:
                found = extract_emails_from_text(content_val, source="html-meta")
                all_emails.update(found)
        
        # All tag attributes
        for tag in soup.find_all(True):
            for attr, val in tag.attrs.items():
                if isinstance(val, str) and "@" in val and len(val) < 200:
                    found = extract_emails_from_text(val, source="html-attr")
                    all_emails.update(found)
        
        # 4. JSON-LD STRUCTURED DATA
        print(f"\n[HTML] Step 4: Scanning JSON-LD scripts...")
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        print(f"[HTML] Found {len(json_ld_scripts)} JSON-LD scripts")
        
        for script in json_ld_scripts:
            if script.string:
                try:
                    json_data = json.loads(script.string)
                    json_str = json.dumps(json_data)
                    found = extract_emails_from_text(json_str, source="html-jsonld")
                    all_emails.update(found)
                except:
                    pass
        
        # 5. HTML COMMENTS
        print(f"\n[HTML] Step 5: Scanning HTML comments...")
        for comment in soup.find_all(string=lambda text: isinstance(text, str)):
            if isinstance(comment, str) and "@" in comment and len(comment) < 300:
                found = extract_emails_from_text(comment, source="html-comment")
                all_emails.update(found)
    
    except Exception as e:
        print(f"[HTML] Error during parsing: {e}")
    
    # Final filtering
    clean_emails = [e for e in all_emails if not is_fake_email(e)]
    
    print(f"\n[HTML] === SUMMARY ===")
    print(f"[HTML] Found: {len(all_emails)} emails")
    print(f"[HTML] Filtered: {len(all_emails) - len(clean_emails)} fakes")
    print(f"[HTML] Result: {len(clean_emails)} real emails")
    print(f"{'='*70}\n")
    
    return clean_emails


def extract_from_js_files(domain, html):
    """
    Extract JavaScript files and scan for emails.
    
    STRATEGY:
    1. Find all <script> tags (inline + external URLs)
    2. Scan inline scripts first (critical)
    3. Extract external JS URLs
    4. Deduplicate
    5. Prioritize: _next/static, bundles, app files
    6. Skip huge vendors (>2MB)
    7. Scan ALL files (no limit)
    """
    all_emails = set()
    
    print(f"\n{'='*70}")
    print(f"[JS] === JAVASCRIPT EXTRACTION PIPELINE ===")
    print(f"{'='*70}")
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script")
        
        print(f"\n[JS] Found {len(scripts)} script tags")
        
        # ===== STEP 1: INLINE SCRIPTS =====
        print(f"\n[JS] Step 1: Scanning inline scripts...")
        inline_count = 0
        
        for i, script in enumerate(scripts):
            if script.string:
                text = script.string
                if len(text) > 50:  # Skip tiny scripts
                    inline_count += 1
                    print(f"[JS-inline] Script #{i}: {len(text)} bytes")
                    
                    found = extract_emails_from_text(text, source="js-inline")
                    if found:
                        print(f"[JS-inline] ✓ Found: {found}")
                        all_emails.update(found)
        
        print(f"[JS] Scanned {inline_count} inline scripts")
        
        # ===== STEP 2: EXTERNAL JS FILES =====
        print(f"\n[JS] Step 2: Extracting external JS URLs...")
        js_urls = set()
        
        for script in scripts:
            src = script.get("src")
            if not src:
                continue
            
            # Normalize URL
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("http"):
                pass
            elif src.startswith("/"):
                src = f"https://{domain}{src}"
            else:
                src = f"https://{domain}/{src}"
            
            # Deduplicate
            js_urls.add(src)
        
        print(f"[JS] Found {len(js_urls)} unique external JS URLs")
        
        # ===== STEP 3: PRIORITIZE URLs =====
        print(f"\n[JS] Step 3: Prioritizing URLs...")
        
        def priority_score(url):
            """Score URLs for scanning priority"""
            score = 0
            url_lower = url.lower()
            
            # HIGHEST: Next.js chunks
            if "_next/static" in url_lower or "/_next/" in url_lower:
                score += 100000
                print(f"[JS-priority] ★★★ {url.split('/')[-1]} (Next.js)")
            
            # HIGH: app/main/bundle files
            elif any(x in url_lower for x in ["app.", "main.", "bundle.", "index."]):
                score += 10000
                print(f"[JS-priority] ★★ {url.split('/')[-1]} (bundle)")
            
            # MEDIUM: not vendors
            elif "vendor" not in url_lower and "libs" not in url_lower:
                score += 1000
                print(f"[JS-priority] ★ {url.split('/')[-1]} (normal)")
            
            # LOW: vendors
            else:
                score -= 1000
                print(f"[JS-priority] ○ {url.split('/')[-1]} (vendor)")
            
            return score
        
        js_list = sorted(list(js_urls), key=priority_score, reverse=True)
        
        # ===== STEP 4: SCAN ALL FILES IN PARALLEL =====
        print(f"\n[JS] Step 4: Scanning all JavaScript files in parallel...")
        scanned = 0
        skipped = 0
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def fetch_and_scan(js_url):
            try:
                filename = js_url.split('/')[-1]
                r = requests.get(js_url, headers=HEADERS, timeout=8, verify=False)
                if r.status_code != 200:
                    return []
                if len(r.text) > 5000000:
                    print(f"[JS-fetch] Skipping {filename} - too large")
                    return []
                print(f"[JS-fetch] Scanning {filename} ({len(r.text)} bytes)")
                found = extract_emails_from_text(r.text, source=f"js-file")
                if found:
                    print(f"[JS-fetch] Found {len(found)}: {found}")
                return found
            except:
                return []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_and_scan, url): url for url in js_list}
            for future in as_completed(futures):
                result = future.result()
                all_emails.update(result)
                scanned += 1
        
        for js_url in []:  # dummy to keep structure
            pass
            try:
                filename = js_url.split('/')[-1]
                print(f"\n[JS-fetch] Fetching: {filename}...")
                
                r = requests.get(js_url, headers=HEADERS, timeout=10, verify=False)
                
                if r.status_code != 200:
                    print(f"[JS-fetch] ✗ HTTP {r.status_code}")
                    continue
                
                js_text = r.text
                js_size = len(js_text)
                
                # Skip huge files (>2MB likely unimportant vendors)
                if js_size > 5000000:
                    print(f"[JS-fetch] ⊘ Skipped (too large: {js_size} bytes)")
                    skipped += 1
                    continue
                
                scanned += 1
                print(f"[JS-fetch] ✓ Scanning {js_size} bytes")
                
                found = extract_emails_from_text(js_text, source=f"js-file:{filename}")
                
                if found:
                    print(f"[JS-fetch] ✓✓ Found {len(found)}: {found}")
                    all_emails.update(found)
                else:
                    print(f"[JS-fetch] No emails found")
            
            except requests.Timeout:
                print(f"[JS-fetch] ✗ Timeout")
            except Exception as e:
                print(f"[JS-fetch] ✗ Error: {str(e)[:100]}")
        
        print(f"\n[JS] === SUMMARY ===")
        print(f"[JS] Scanned: {scanned} files")
        print(f"[JS] Skipped: {skipped} files (too large)")
        print(f"[JS] Emails found: {len(all_emails)}")
        print(f"{'='*70}\n")
    
    except Exception as e:
        print(f"[JS] Fatal error: {e}")
    
    return list(all_emails)


# ============================================================================
# MAIN EXTRACTION PIPELINE
# ============================================================================

def extract_all(domain, pages_data):

    
    """
    Complete production-grade email extraction pipeline.
    
    For each page:
    1. Extract from HTML (mailto, text, meta, JSON-LD, comments)
    2. Extract from JavaScript (inline + external files)
    3. Merge results
    4. Filter fakes
    5. Return real emails
    """
    all_emails = set()
    
    print(f"\n\n")
    print(f"╔{'═'*68}╗")
    print(f"║ {'EMAIL EXTRACTION PIPELINE - PRODUCTION GRADE':^66} ║")
    print(f"╚{'═'*68}╝")
    print(f"\nDomain: {domain}")
    print(f"Pages to scan: {len(pages_data)}")
    print(f"\n{'='*70}\n")
    
    # Process each page
    for page_num, page in enumerate(pages_data, 1):
        url = page.get("url", "unknown")
        content = page.get("content", "")
        
        print(f"\n┌─ PAGE {page_num}/{len(pages_data)} ─────────────────────────────────────┐")
        print(f"│ URL: {url[:60]}")
        print(f"│ Size: {len(content)} bytes")
        print(f"└──────────────────────────────────────────────────────────────┘\n")
        
        # HTML extraction
        html_emails = extract_from_html(content)
        all_emails.update(html_emails)
        
        # JavaScript extraction
        js_emails = extract_from_js_files(domain, content)
        all_emails.update(js_emails)
        
        # Public sources (crt.sh + common patterns)
        print(f"\n[PAGE {page_num}] === Public Sources ===")
        public_emails = fetch_public_sources(domain)
        all_emails.update(public_emails)
        
        print(f"\n[PAGE {page_num}] Emails found this page: {len(html_emails) + len(js_emails)}")
        print(f"[PAGE {page_num}] Running total: {len(all_emails)}\n")
    
    # Final filtering and reporting
    print(f"\n{'='*70}")
    print(f"║ FINAL RESULTS")
    print(f"{'='*70}\n")
    
    real_emails = []
    fake_emails = []
    
    for email in sorted(all_emails):
        if is_fake_email(email):
            fake_emails.append(email)
        else:
            real_emails.append(email)
    
    print(f"\n✓ REAL EMAILS ({len(real_emails)}):")
    for email in real_emails:
        print(f"  • {email}")
    
    if fake_emails:
        print(f"\n✗ FILTERED EMAILS ({len(fake_emails)}):")
        for email in fake_emails[:10]:  # Show first 10
            print(f"  • {email}")
        if len(fake_emails) > 10:
            print(f"  ... and {len(fake_emails) - 10} more")
    
    print(f"\n{'='*70}")
    print(f"[FINAL] Total found: {len(all_emails)}")
    print(f"[FINAL] Real emails: {len(real_emails)}")
    print(f"[FINAL] Fake emails filtered: {len(fake_emails)}")
    print(f"{'='*70}\n")
    
    return real_emails



def fetch_public_sources(domain):
    """
    Find emails from public sources:
    1. crt.sh (SSL certificates)
    2. Hunter.io pattern guessing
    3. Common email patterns for domain
    """
    emails = set()
    
    # 1. Check crt.sh for SSL certificate emails
    try:
        r = requests.get(
            f"https://crt.sh/?q=%40{domain}&output=json",
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            for entry in data[:50]:
                name = entry.get("name_value", "")
                found = extract_emails_from_text(name, source="crt.sh")
                emails.update(found)
            print(f"[crt.sh] Found {len(emails)} emails")
    except Exception as e:
        print(f"[crt.sh] Error: {e}")
    
    # 2. Try common email patterns
    COMMON_PREFIXES = [
        "support", "info", "contact", "hello", "help",
        "security", "legal", "privacy", "admin", "cs",
        "helpdesk", "customerservice", "customer_service",
        "mobile_support", "noreply", "no-reply", "sales",
        "billing", "abuse", "webmaster", "team",
    ]
    for prefix in COMMON_PREFIXES:
        emails.add(f"{prefix}@{domain}")
    
    print(f"[public] Total from public sources: {len(emails)}")
    return list(emails)

