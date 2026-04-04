from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor

from modules.crawler import crawl
from modules.email_extractor import extract_all
from modules.cleaner import clean_emails, filter_by_domain
from modules.validator import validate_emails
from modules.filter_engine import filter_best
from modules.bounty_detector import detect_bounty
from modules.sender import send_all

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor()

class ScanRequest(BaseModel):
    domain: str

class SendRequest(BaseModel):
    targets: list
    subject: str
    body: str

@app.get("/")
def root():
    return {"status": "MailReach API running!"}

@app.post("/scan")
async def scan(req: ScanRequest):
    domain = req.domain \
        .replace("https://", "") \
        .replace("http://", "") \
        .replace("www.", "") \
        .split("/")[0] \
        .strip()

    logs = []
    try:
        logs.append({"msg": f"Crawling {domain}...", "type": "info"})

        # Run crawl in thread so it doesnt block
        loop = asyncio.get_event_loop()
        pages = await loop.run_in_executor(executor, lambda: crawl(domain))
        logs.append({"msg": f"Crawled {len(pages)} pages", "type": "ok"})

        emails = extract_all(domain, pages)
        logs.append({"msg": f"Found {len(emails)} raw emails", "type": "info"})

        clean = clean_emails(emails)
        filtered = filter_by_domain(clean, domain)
        logs.append({"msg": f"Cleaned to {len(filtered)} emails", "type": "ok"})

        valid = validate_emails(filtered, domain)
        logs.append({"msg": f"Validated {len(valid)} emails", "type": "ok"})

        best = filter_best(valid)
        logs.append({"msg": f"Selected {len(best)} best emails", "type": "ok"})

        # Detect bounty
        bounty = detect_bounty(pages)
        if bounty["has_program"]:
            logs.append({"msg": f"Bug bounty detected: {bounty['type']}", "type": "ok"})
        else:
            logs.append({"msg": "No bounty program found", "type": "info"})

        return {
            "emails": [
                {
                    "email": e["email"],
                    "score": e["score"],
                    "domain": e["domain"],
                    "mx_ok": e["mx_ok"],
                    "smtp_ok": e.get("smtp_ok", False)
                }
                for e in best
            ],
            "bounty": bounty,
            "logs": logs
        }

    except Exception as e:
        logs.append({"msg": f"Error: {str(e)}", "type": "err"})
        return {"emails": [], "bounty": None, "logs": logs}

@app.post("/send")
async def send(req: SendRequest):
    try:
        # Run send in background thread
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            executor,
            lambda: send_all(req.targets, req.subject, req.body)
        )

        logs = [
            {
                "msg": f"{r['to']} → {r['status']} via {r['service']}",
                "type": "ok" if r["status"] == "sent" else "err"
            }
            for r in results
        ]
        return {"results": results, "logs": logs}

    except Exception as e:
        return {
            "results": [],
            "logs": [{"msg": str(e), "type": "err"}]
        }
    

@app.get("/debug")
def debug():
    import os
    return {
        "GMAIL_USER": os.environ.get("GMAIL_USER", "NOT SET"),
        "GMAIL_PASS": "SET" if os.environ.get("GMAIL_APP_PASSWORD") else "NOT SET",
        "BREVO_USER": os.environ.get("BREVO_USER", "NOT SET"),
        "BREVO_KEY": "SET" if os.environ.get("BREVO_SMTP_KEY") else "NOT SET"
    }