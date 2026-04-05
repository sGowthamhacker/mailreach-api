from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import queue
import threading
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

class MxCheckRequest(BaseModel):
    email: str

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
        loop = asyncio.get_event_loop()
        pages = await loop.run_in_executor(executor, lambda: crawl(domain))
        logs.append({"msg": f"Crawled {len(pages)} pages", "type": "ok"})
        emails = extract_all(domain, pages)
        logs.append({"msg": f"Found {len(emails)} raw emails", "type": "info"})
        clean = clean_emails(emails)
        filtered = clean  # keep ALL emails found, not just domain-matched
        logs.append({"msg": f"Cleaned to {len(filtered)} emails", "type": "ok"})
        valid = validate_emails(filtered, domain)
        logs.append({"msg": f"Validated {len(valid)} emails", "type": "ok"})
        best = filter_best(valid)
        logs.append({"msg": f"Selected {len(best)} best emails", "type": "ok"})
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

@app.post("/scan-stream")
def scan_stream(req: ScanRequest):
    domain = req.domain \
        .replace("https://", "") \
        .replace("http://", "") \
        .replace("www.", "") \
        .split("/")[0] \
        .strip()

    log_queue = queue.Queue()

    def send(msg, level="info"):
        log_queue.put({"type": "log", "msg": msg, "level": level})

    def run_scan():
        try:
            send(f"🔍 Scanning {domain}...", "info")
            send(f"🌐 Building URL queue...", "info")

            def crawl_log(msg):
                if "[ok]" in msg:
                    send(f"✅ Crawled: {msg.replace('[ok]','').strip()}", "ok")
                elif "[skip]" in msg:
                    send(f"⏭ Skipped: {msg.replace('[skip]','').strip()}", "info")
                elif "[done]" in msg:
                    send(f"🏁 {msg.replace('[done]','').strip()}", "ok")
                elif "[crawl]" in msg:
                    send(f"🕷️ {msg.replace('[crawl]','').strip()}", "info")
                else:
                    send(msg, "info")

            pages = crawl(domain, log_callback=crawl_log)
            send(f"📄 Crawled {len(pages)} pages — extracting emails...", "info")

            emails = extract_all(domain, pages)
            send(f"📧 Found {len(emails)} raw emails", "info")

            clean = clean_emails(emails)
            filtered = filter_by_domain(clean, domain)
            send(f"🧹 Cleaned to {len(filtered)} emails", "info")

            valid = validate_emails(filtered, domain)
            send(f"✔️ Validated {len(valid)} emails", "ok")

            best = filter_best(valid)
            send(f"⭐ Selected {len(best)} best emails", "ok")

            bounty = detect_bounty(pages)
            if bounty["has_program"]:
                send(f"🎯 Bug bounty detected: {bounty['type']}", "ok")
            else:
                send(f"ℹ️ No bounty program found", "info")

            result_emails = [
                {
                    "email": e["email"],
                    "score": e["score"],
                    "domain": e["domain"],
                    "mx_ok": e["mx_ok"],
                    "smtp_ok": e.get("smtp_ok", False)
                }
                for e in best
            ]

            log_queue.put({
                "type": "done",
                "emails": result_emails,
                "bounty": bounty
            })

        except Exception as e:
            send(f"❌ Error: {str(e)}", "err")
            log_queue.put({"type": "done", "emails": [], "bounty": None})

    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()

    def event_stream():
        while True:
            try:
                item = log_queue.get(timeout=300)
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("type") == "done":
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type':'log','msg':'Timeout','level':'err'})}\n\n"
                yield f"data: {json.dumps({'type':'done','emails':[],'bounty':None})}\n\n"
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/send")
async def send(req: SendRequest):
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            executor,
            lambda: send_all(req.targets, req.subject, req.body)
        )
        logs = [
            {
                "msg": f"{r['to']} -> {r['status']} via {r['service']}",
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

@app.post("/check-mx")
async def check_mx(req: MxCheckRequest):
    import dns.resolver

    email = req.email.strip().lower()

    if "@" not in email:
        return {"email": email, "mx_ok": False, "smtp_ok": False, "error": "Invalid email format"}

    domain = email.split("@")[1]

    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=5)
        mx_hosts = sorted(mx_records, key=lambda r: r.preference)
        mx_ok = len(mx_hosts) > 0
    except Exception as e:
        return {"email": email, "mx_ok": False, "smtp_ok": False, "error": f"MX lookup failed: {str(e)}"}

    return {
        "email": email,
        "mx_ok": mx_ok,
        "smtp_ok": mx_ok,
        "domain": domain,
        "mx_hosts": [str(m.exchange).rstrip(".") for m in mx_hosts[:3]]
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