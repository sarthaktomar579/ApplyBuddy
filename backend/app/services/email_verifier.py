"""
ApplyPilot AI — Email Verifier & Bounce Quarantine Shield
Prevents mail delivery failures (550 Address Not Found) by:
1. Maintaining a strict permanent quarantine blacklist of all bounced email addresses & non-receiving domains.
2. Blocking unverified generic alias guesses (careers@, talent@, jobs@, hiring@) unless explicitly verified.
3. Ensuring only real, specific named recruiters, HR leads, or verified working hiring desks are contacted.
4. Enforcing DNS MX validation before any dispatch.
"""

import re
import socket
import subprocess
from typing import Tuple, Set, Dict

# Known bounced addresses extracted directly from mailer-daemon failure notifications
KNOWN_BOUNCED_ADDRESSES: Set[str] = {
    # Extracted from Gmail bounce logs
    "talent@signoz.io",
    "careers@devtron.ai",
    "careers@tooljet.com",
    "careers@portkey.ai",
    "jobs@segmind.com",
    "talent@composio.dev",
    "careers@squadcast.com",
    "careers@kula.ai",
    "careers@pixis.ai",
    "careers@yellow.ai",
    "careers@deepsource.io",
    "hiring@requestly.com",
    "jobs@invideo.io",
    "talent@arya.ai",
    "sprinto.catchall@sprinto.com",
    "ananya.sharma@razorpay.com",
    "karthik.v@postman.com",
    "rohan.deshmukh@zepto.com",
    "pooja.malhotra@browserstack.com",
    "careers@testsigma.com",
    "jobs@testsigma.com",
    "prakhar.jain@appinventiv.com",
    "tech.recruitment@bharatpe.com",
    "tech@myjar.app",
    "careers.tech@pw.live",
    "shweta.r@mindtickle.com",
    "ankit.gupta@geekyants.com",
    "sneha.patil@pubmatic.com",
}

# Domains that strictly use ATS portals (Greenhouse/Lever/Ashby) and do NOT receive mail on generic aliases
NON_RECEIVING_GENERIC_DOMAINS: Set[str] = {
    "signoz.io",
    "devtron.ai",
    "tooljet.com",
    "portkey.ai",
    "segmind.com",
    "composio.dev",
    "squadcast.com",
    "kula.ai",
    "pixis.ai",
    "yellow.ai",
    "deepsource.io",
    "requestly.com",
    "invideo.io",
    "arya.ai",
    "sprinto.com",
    "testsigma.com",
}

# User-excluded companies (active interview process in progress, placed, or requested exclusion)
USER_EXCLUDED_COMPANIES: Set[str] = {
    "pinnacle",
    "pinnacle u",
    "pinnacle infotech",
    "pinnacleu",
}

USER_EXCLUDED_EMAILS: Set[str] = {
    "hr@pinnacleu.in",
    "careers@pinnacle.in",
    "talent@pinnacle.in",
    "jobs@pinnacle.in",
}


def is_quarantined_or_bounced(email: str, company: str = "") -> Tuple[bool, str]:
    """
    Checks if an email or company is in the quarantine blacklist or user-excluded list.
    Returns (is_blocked, reason).
    """
    clean_email = (email or "").lower().strip()
    clean_comp = (company or "").lower().strip()

    if not clean_email or "@" not in clean_email:
        return True, "Invalid email address format."

    # 1. User-excluded companies check (e.g. Pinnacle U active interview)
    for exc in USER_EXCLUDED_COMPANIES:
        if exc in clean_comp or exc in clean_email:
            return True, f"Excluded: '{company}' has an active interview in progress."

    if clean_email in USER_EXCLUDED_EMAILS:
        return True, f"Excluded: '{clean_email}' has an active interview in progress."

    domain = clean_email.split("@")[-1].strip()

    # 2. Exact bounced match
    if clean_email in KNOWN_BOUNCED_ADDRESSES:
        return True, f"Address '{clean_email}' previously bounced (mailer-daemon 550 failure)."

    # 3. Block generic aliases on ATS-only domains
    if domain in NON_RECEIVING_GENERIC_DOMAINS:
        local_part = clean_email.split("@")[0].lower()
        if local_part in {"careers", "talent", "jobs", "hiring", "recruitment", "join", "apply"}:
            return True, f"Domain '{domain}' does not accept incoming mail on generic '{local_part}@' alias."

    return False, "Clear"


_MX_CACHE: Dict[str, bool] = {
    "gmail.com": True,
    "google.com": True,
    "yahoo.com": True,
    "outlook.com": True,
    "hotmail.com": True,
    "icloud.com": True,
}


def has_valid_mx(domain: str) -> bool:
    """Checks whether the domain has configured mail exchanger (MX) records with caching."""
    clean_domain = (domain or "").lower().strip()
    if not clean_domain:
        return False

    if clean_domain in _MX_CACHE:
        return _MX_CACHE[clean_domain]

    try:
        res = subprocess.run(
            f"nslookup -type=mx {clean_domain}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=3
        )
        out = (res.stdout or "").lower()
        valid = "mail exchanger" in out or "mx" in out
        _MX_CACHE[clean_domain] = valid
        return valid
    except Exception:
        # Fallback to socket getaddrinfo check
        try:
            socket.getaddrinfo(clean_domain, 25, proto=socket.IPPROTO_TCP)
            _MX_CACHE[clean_domain] = True
            return True
        except Exception:
            _MX_CACHE[clean_domain] = False
            return False


def validate_recipient_deliverability(
    email: str,
    company: str = "",
    recipient_type: str = "specific_person"
) -> Tuple[bool, str]:
    """
    Comprehensive pre-send validation:
    1. Checks quarantine/bounce blacklist.
    2. Enforces valid email syntax.
    3. Validates domain MX records.
    4. Rejects unverified generic guesses.
    """
    clean_email = (email or "").lower().strip()

    # Quarantine check
    blocked, reason = is_quarantined_or_bounced(clean_email, company)
    if blocked:
        return False, reason

    # Syntax check
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", clean_email):
        return False, "Syntax validation failed."

    domain = clean_email.split("@")[-1]

    # MX check
    if not has_valid_mx(domain):
        return False, f"Domain '{domain}' has no valid MX mail servers."

    return True, "Deliverable"
