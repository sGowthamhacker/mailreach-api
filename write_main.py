content = open("main.py").read()

if "/check-mx" in content:
    print("Already has check-mx!")
else:
    if "class MxCheckRequest" not in content:
        content = content.replace(
            "class SendRequest(BaseModel):",
            "class MxCheckRequest(BaseModel):\n    email: str\n\nclass SendRequest(BaseModel):"
        )

    addon = """
@app.post("/check-mx")
async def check_mx(req: MxCheckRequest):
    import dns.resolver, smtplib
    email = req.email.strip().lower()
    if "@" not in email:
        return {"email": email, "mx_ok": False, "smtp_ok": False, "error": "Invalid format"}
    domain = email.split("@")[1]
    mx_ok = False
    smtp_ok = False
    mx_hosts = []
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_hosts = sorted(mx_records, key=lambda r: r.preference)
        mx_ok = len(mx_hosts) > 0
    except Exception as e:
        return {"email": email, "mx_ok": False, "smtp_ok": False, "error": f"MX lookup failed: {str(e)}"}
    if mx_ok and mx_hosts:
        try:
            mx_host = str(mx_hosts[0].exchange).rstrip(".")
            with smtplib.SMTP(timeout=8) as smtp:
                smtp.connect(mx_host, 25)
                smtp.helo("mail.example.com")
                smtp.mail("probe@example.com")
                code, _ = smtp.rcpt(email)
                smtp_ok = code == 250
        except Exception:
            smtp_ok = False
    return {
        "email": email,
        "mx_ok": mx_ok,
        "smtp_ok": smtp_ok,
        "domain": domain,
        "mx_hosts": [str(m.exchange).rstrip(".") for m in mx_hosts[:3]] if mx_ok else []
    }
"""
    content += addon
    with open("main.py", "w") as f:
        f.write(content)
    print("Done! check-mx added successfully.")