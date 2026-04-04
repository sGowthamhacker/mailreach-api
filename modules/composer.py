def load_template(filepath="templates/message.txt"):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def compose(domain, template=None):
    if not template:
        template = load_template()

    # Extract company name from domain
    company = domain.split(".")[0].capitalize()

    # Replace placeholders
    message = template.replace("{domain}", domain)
    message = message.replace("{company}", company)

    # Split subject and body
    lines = message.strip().split("\n")
    subject = ""
    body_lines = []

    for i, line in enumerate(lines):
        if line.startswith("Subject:"):
            subject = line.replace("Subject:", "").strip()
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    return {
        "subject": subject,
        "body": body,
        "domain": domain,
        "company": company
    }