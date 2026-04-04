import re

BOUNTY_KEYWORDS = [
    "bug bounty", "vulnerability disclosure", "responsible disclosure",
    "security disclosure", "vdp", "bbp", "hackerone", "bugcrowd",
    "intigriti", "yeswehack", "report a vulnerability", "security.txt",
    "coordinated disclosure", "cvd", "hall of fame", "security researcher",
    "pentest", "penetration test", "report security", "security report"
]

BOUNTY_PLATFORMS = {
    "hackerone.com": "HackerOne",
    "bugcrowd.com": "Bugcrowd",
    "intigriti.com": "Intigriti",
    "yeswehack.com": "YesWeHack",
    "openbugbounty.org": "OpenBugBounty",
    "federacy.com": "Federacy"
}

def detect_bounty(pages_data):
    result = {
        "has_program": False,
        "type": None,
        "platform": None,
        "platform_url": None,
        "mentions": [],
        "security_txt": None,
        "confidence": 0
    }

    for page in pages_data:
        url = page["url"]
        content = page["content"].lower()

        # Check security.txt
        if "security.txt" in url:
            result["security_txt"] = page["content"][:500]
            result["confidence"] += 20

        # Check for platform links
        for platform_domain, platform_name in BOUNTY_PLATFORMS.items():
            if platform_domain in content:
                result["has_program"] = True
                result["platform"] = platform_name
                result["platform_url"] = platform_domain
                result["confidence"] += 40
                break

        # Check for keywords
        for keyword in BOUNTY_KEYWORDS:
            if keyword in content:
                if keyword not in result["mentions"]:
                    result["mentions"].append(keyword)
                result["confidence"] += 5

    # Determine type
    if result["confidence"] >= 40:
        result["has_program"] = True
        if result["platform"]:
            result["type"] = "BBP"
        elif "vdp" in result["mentions"] or "vulnerability disclosure" in result["mentions"]:
            result["type"] = "VDP"
        else:
            result["type"] = "Possible Program"

    # Cap confidence at 100
    result["confidence"] = min(result["confidence"], 100)

    return result