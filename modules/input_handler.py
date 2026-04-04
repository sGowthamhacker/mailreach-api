from urllib.parse import urlparse
import csv

def normalize_domain(url):
    url = url.strip()
    if not url:
        return None
    if not url.startswith("http"):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain if domain else None
    except:
        return None

def load_from_text(text):
    lines = text.strip().split("\n")
    domains = [normalize_domain(l) for l in lines]
    return list(set(d for d in domains if d))

def load_from_csv(filepath, column=0):
    domains = []
    with open(filepath, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                d = normalize_domain(row[column])
                if d:
                    domains.append(d)
    return list(set(domains))