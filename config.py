import os

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
MAX_PAGES_PER_DOMAIN = 200
CRAWL_DELAY = 1
REQUEST_TIMEOUT = 15
DELAY_BETWEEN_EMAILS = 2
MAX_PER_HOUR = 50

EMAIL_PREFIXES = [
    "security", "contact", "info", "support", "admin",
    "hello", "team", "sales", "help", "mail",
    "reach", "enquiry", "inquiry", "feedback",
    "connect", "message", "talk", "ping",
    "write", "email", "getintouch", "touch",
    "disclosure", "vulnerability", "bounty", "bugbounty",
    "vdp", "bbp", "report", "cvd", "pentest",
    "responsible", "halloffame", "hof", "advisories",
    "securityteam", "security-team", "bugreport",
    "helpdesk", "helpcenter", "customerservice",
    "customersupport", "customercare", "tickets",
    "service", "care", "assist", "assistance",
    "press", "media", "newsroom", "pr", "communications",
    "marketing", "brand", "partnerships", "partners",
    "investors", "ir", "legal", "compliance",
    "privacy", "dpo", "gdpr", "data",
    "careers", "jobs", "hiring", "recruitment",
    "hr", "humanresources", "people", "talent",
    "recruiting", "joinus",
    "dev", "developer", "developers", "api",
    "technical", "tech", "engineering", "devops",
    "noc", "ops", "sre", "platform",
    "billing", "payments", "accounts", "finance",
    "invoice", "accounting", "payroll",
    "office", "general", "corporate", "headquarters",
    "hq", "webmaster", "postmaster", "hostmaster",
    "abuse", "spam", "phishing", "trust",
    "community", "social", "newsletter",
    "events", "conference",
    "ceo", "cto", "cfo", "coo", "ciso",
    "founder", "cofounder", "president", "director",
    "manager", "officer", "executive",
    "cs", "customer", "onboarding", "success",
    "returns", "refunds", "warranty", "shipping",
    "logistics", "procurement", "purchasing",
    "vendor", "suppliers", "wholesale", "reseller",
    "affiliate", "referral", "rewards", "loyalty",
    "design", "creative", "ux", "ui", "product",
    "research", "analytics", "insights", "growth",
    "content", "editorial", "publishing", "blog",
    "seo", "ads", "advertising", "campaigns",
    "training", "education", "learning", "academy",
    "certification", "courses", "workshop",
    "charity", "foundation", "csr", "sustainability",
    "volunteer", "internship", "intern", "graduate",
    "alumni", "ambassador", "advocate",
    "safety", "fraud", "risk", "infosec",
    "network", "infrastructure", "sysadmin", "it",
    "cloud", "devops", "backend", "frontend",
    "mobile", "app", "software", "hardware",
    "sales-team", "salesteam", "presales", "postsales",
    "enterprise", "smb", "startup", "agency",
    "demo", "trial", "pilot", "poc",
    "quote", "pricing", "proposal", "rfp",
    "contract", "legal-team", "legalteam",
    "secretary", "reception", "front-desk",
    "booking", "reservations", "appointments",
    "emergency", "urgent", "escalation",
    "noreply", "no-reply", "donotreply",
    "mailer", "notifications", "alerts",
    "updates", "status", "system",
    "hello-team", "hi", "hey",
    "global", "international", "regional",
    "apac", "emea", "latam", "us", "eu", "uk",
    "india", "asia", "europe", "americas",
]

PRIORITY = [
    "security", "bugbounty", "bug-bounty", "vdp", "bbp",
    "disclosure", "psirt", "cert", "csirt", "abuse",
    "contact", "info", "hello", "support", "help",
    "admin", "legal", "privacy", "trust", "compliance",
    "team", "dev", "developer", "engineering",
    "sales", "marketing", "press", "media",
    "ceo", "cto", "cfo", "ciso", "founder",
    "hr", "careers", "jobs", "hiring",
    "billing", "finance", "payments",
    "feedback", "enquiry", "inquiry",
    "general", "office", "corporate",
]

BLACKLIST = ["automated", "donotreply", "bounce", "mailer-daemon", "daemon"]

