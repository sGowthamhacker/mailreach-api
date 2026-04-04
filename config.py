import os

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_DAILY_LIMIT = 500

BREVO_SMTP_SERVER = "smtp-relay.brevo.com"
BREVO_PORT = 587
BREVO_USER = os.environ.get("BREVO_USER", "")
BREVO_SMTP_KEY = os.environ.get("BREVO_SMTP_KEY", "")
BREVO_DAILY_LIMIT = 300
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")

MAX_PAGES_PER_DOMAIN = 20
CRAWL_DELAY = 2
REQUEST_TIMEOUT = 10

# === Email Patterns ===
EMAIL_PREFIXES = [
    # High priority
    "security", "contact", "info", "support", "admin",
    "hello", "team", "sales", "help", "mail",

    # Contact
    "reach", "enquiry", "inquiry", "feedback",
    "connect", "message", "talk", "ping",
    "write", "email", "getintouch", "touch",

    # Security
    "disclosure", "vulnerability", "bounty", "bugbounty",
    "vdp", "bbp", "report", "cvd", "pentest",
    "responsible", "halloffame", "hof", "advisories",
    "securityteam", "security-team", "bugreport",

    # Support
    "helpdesk", "helpcenter", "customerservice",
    "customersupport", "customercare", "tickets",
    "service", "care", "assist", "assistance",

    # Company
    "press", "media", "newsroom", "pr", "communications",
    "marketing", "brand", "partnerships", "partners",
    "investors", "ir", "legal", "compliance",
    "privacy", "dpo", "gdpr", "data",

    # Jobs
    "careers", "jobs", "hiring", "recruitment",
    "hr", "humanresources", "people", "talent",
    "recruiting", "joinus",

    # Tech
    "dev", "developer", "developers", "api",
    "technical", "tech", "engineering", "devops",
    "noc", "ops", "sre", "platform",

    # Finance
    "billing", "payments", "accounts", "finance",
    "invoice", "accounting", "payroll",

    # General
    "office", "general", "corporate", "headquarters",
    "hq", "webmaster", "postmaster", "hostmaster",
    "abuse", "spam", "phishing", "trust",
    "community", "social", "newsletter",
    "events", "conference", "partnerships",
]


PRIORITY = [
    "security", "bugbounty", "bug-bounty", "vdp",
    "disclosure", "psirt", "cert", "abuse",
    "contact", "info", "hello", "support", "help",
    "admin", "legal", "privacy", "trust", "compliance",
    "team", "dev", "developer", "engineering",
    "sales", "marketing", "press", "media"
]

BLACKLIST = ["noreply", "no-reply", "automated", "donotreply", "bounce"]

MAX_PAGES_PER_DOMAIN = 60   # was 20
CRAWL_DELAY = 1             # was 2
REQUEST_TIMEOUT = 15        # was 10
DELAY_BETWEEN_EMAILS = 2