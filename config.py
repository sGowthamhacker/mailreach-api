import os

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
MAX_PAGES_PER_DOMAIN = 200
CRAWL_DELAY = 0
REQUEST_TIMEOUT = 10
DELAY_BETWEEN_EMAILS = 2
MAX_PER_HOUR = 50

EMAIL_PREFIXES = [
    "security", "contact", "info", "support", "admin",
    "hello", "team", "sales", "help", "mail",
    "reach", "enquiry", "inquiry", "feedback",
    "connect", "message", "talk", "ping",
    "disclosure", "vulnerability", "bounty", "bugbounty",
    "vdp", "bbp", "report", "responsible",
    "press", "media", "legal", "compliance",
    "privacy", "dpo", "gdpr", "careers", "jobs",
    "hr", "billing", "payments", "abuse", "trust",
    "security-team", "securityteam", "psirt", "cert", "csirt",
    "bugreport", "bug-report", "pentest", "redteam",
    "helpdesk", "helpcenter", "customerservice", "customersupport",
    "customercare", "service", "care", "assist",
    "newsroom", "pr", "communications", "marketing", "brand",
    "partnerships", "partners", "investors", "ir",
    "data", "dpo", "gdpr", "compliance", "legal",
    "recruiting", "talent", "people", "joinus",
    "dev", "developer", "developers", "api", "engineering",
    "devops", "noc", "ops", "sre", "platform",
    "billing", "payments", "accounts", "finance", "invoice",
    "office", "general", "corporate", "hq", "headquarters",
    "webmaster", "postmaster", "hostmaster",
    "spam", "phishing", "fraud", "risk", "safety",
    "community", "social", "newsletter", "events",
    "ceo", "cto", "cfo", "coo", "ciso",
    "founder", "cofounder", "president", "director",
    "manager", "officer", "executive",
    "onboarding", "success", "returns", "refunds",
    "vendor", "suppliers", "wholesale", "reseller",
    "affiliate", "referral", "rewards",
    "design", "creative", "ux", "product",
    "research", "analytics", "growth", "content",
    "seo", "ads", "advertising", "campaigns",
    "training", "education", "learning", "academy",
    "charity", "foundation", "csr", "sustainability",
    "emergency", "urgent", "escalation",
    "global", "international", "regional",
    "apac", "emea", "latam", "us", "eu", "uk",
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
    "partnerships", "partners", "investors",
    "customerservice", "customersupport", "helpdesk",
    "newsroom", "pr", "communications",
    "data", "dpo", "gdpr", "risk", "fraud",
    "community", "social", "newsletter",
    "onboarding", "success", "service",
    "webmaster", "postmaster", "hostmaster",
    "research", "analytics", "growth",
    "design", "creative", "product",
    "training", "education", "learning",
    "emergency", "urgent", "escalation",
    "global", "international", "apac", "emea",
]

BLACKLIST = [
    "automated", "donotreply", "bounce", "mailer-daemon",
    "daemon", "noreply", "no-reply", "notifications",
    "alerts", "system", "robot", "auto",
]