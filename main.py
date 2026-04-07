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
from modules.email_extractor import extract_all, extract_emails_from_text
from modules.cleaner import clean_emails
from modules.validator import validate_emails
from modules.filter_engine import filter_best
from modules.bounty_detector import detect_bounty
from modules.sender import send_all

print("\n[MAIN] Loading MailReach API...")
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
executor = ThreadPoolExecutor()
print("[MAIN] API initialized\n")

class ScanRequest(BaseModel):
    domain: str
    scan_subdomains: bool = True

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
    domain = req.domain.replace("https://","").replace("http://","").replace("www.","").split("/")[0].strip()
    logs = []
    try:
        loop = asyncio.get_event_loop()
        pages = await loop.run_in_executor(executor, lambda: crawl(domain, scan_subdomains=req.scan_subdomains))
        logs.append({"msg": f"Crawled {len(pages)} pages", "type": "ok"})
        emails = extract_all(domain, pages)
        clean = clean_emails(emails)
        valid = validate_emails(clean, domain)
        bounty = detect_bounty(pages)
        return {
            "emails": [{"email": e["email"], "score": e.get("score", 1), "domain": e["domain"], "mx_ok": e["mx_ok"], "smtp_ok": e.get("smtp_ok", False)} for e in valid],
            "bounty": bounty,
            "logs": logs
        }
    except Exception as e:
        print(f"[SCAN] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"emails": [], "bounty": None, "logs": [{"msg": str(e), "type": "err"}]}

@app.post("/scan-stream")
def scan_stream(req: ScanRequest):
    domain = req.domain.replace("https://","").replace("http://","").replace("www.","").split("/")[0].strip()
    log_queue = queue.Queue()

    def send(msg, level="info"):
        log_queue.put({"type": "log", "msg": msg, "level": level})

    def run_scan():
        try:
            print(f"\n{'='*70}")
            print(f"[SCAN-STREAM] Starting scan for {domain}")
            print(f"{'='*70}\n")

            send(f"Scanning {domain}...", "info")
            send(f"Building URL queue...", "info")

            def crawl_log(msg):
                print(f"[CRAWL] {msg}")
                if "[ok]" in msg:
                    send(f"Crawled: {msg.replace('[ok]','').strip()}", "ok")
                elif "[CRAWLER]" in msg:
                    send(f"{msg}", "info")
                else:
                    send(msg, "info")

            pages = crawl(domain, log_callback=crawl_log)
            send(f"Crawled {len(pages)} pages - extracting emails...", "info")

            emails = extract_all(domain, pages)
            send(f"Found {len(emails)} raw emails", "info")

            clean = clean_emails(emails)
            send(f"Cleaned to {len(clean)} emails", "info")

            valid = validate_emails(clean, domain)
            send(f"Validated {len(valid)} emails", "ok")

            bounty = detect_bounty(pages)
            if bounty and bounty.get("has_program"):
                send(f"Bug bounty detected: {bounty['type']}", "ok")
            else:
                send(f"No bounty program found", "info")

            log_queue.put({
                "type": "done",
                "emails": [{"email": e["email"], "score": e.get("score", 1), "domain": e["domain"], "mx_ok": e["mx_ok"], "smtp_ok": e.get("smtp_ok", False)} for e in valid],
                "bounty": bounty
            })

        except Exception as e:
            print(f"\n[SCAN-STREAM] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            send(f"Error: {str(e)}", "err")
            log_queue.put({"type": "done", "emails": [], "bounty": None})

    threading.Thread(target=run_scan, daemon=True).start()

    def event_stream():
        # Send immediate heartbeat so Railway proxy does not timeout
        yield f"data: {json.dumps({'type':'log','msg':'Connected...','level':'info'})}\n\n"
        while True:
            try:
                item = log_queue.get(timeout=300)
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("type") == "done":
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type':'done','emails':[],'bounty':None})}\n\n"
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.post("/send")
async def send_emails(req: SendRequest):
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(executor, lambda: send_all(req.targets, req.subject, req.body))
        return {
            "results": results,
            "logs": [{"msg": f"{r['to']} -> {r['status']}", "type": "ok" if r["status"] == "sent" else "err"} for r in results]
        }
    except Exception as e:
        return {"results": [], "logs": [{"msg": str(e), "type": "err"}]}

@app.post("/check-mx")
async def check_mx(req: MxCheckRequest):
    import dns.resolver
    email = req.email.strip().lower()
    if "@" not in email:
        return {"email": email, "mx_ok": False, "smtp_ok": False}
    domain = email.split("@")[1]
    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=5)
        mx_hosts = sorted(mx_records, key=lambda r: r.preference)
        return {"email": email, "mx_ok": True, "smtp_ok": True, "domain": domain, "mx_hosts": [str(m.exchange).rstrip(".") for m in mx_hosts[:3]]}
    except:
        return {"email": email, "mx_ok": False, "smtp_ok": False}

@app.get("/debug")
def debug():
    import os
    return {"GMAIL_USER": os.environ.get("GMAIL_USER", "NOT SET"), "GMAIL_PASS": "SET" if os.environ.get("GMAIL_APP_PASSWORD") else "NOT SET"}
