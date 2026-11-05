import hashlib
import hmac
from email.utils import getaddresses


def norm_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    lines = (line.rstrip() for line in s.split("\n"))

    return "\n".join(lines).strip()


def norm_addrs(addr_string: str) -> str:

    parsed = getaddresses([addr_string])

    emails = sorted({email.lower() for _, email in parsed if email})

    return ", ".join(emails)


def compute_hash(
    to: str,
    cc: str,
    subject: str,
    body: str,
    thread_id: str
) -> str:

    norm_to = norm_addrs(to)
    norm_cc = norm_addrs(cc)
    norm_subject = norm_text(subject)
    norm_body = norm_text(body)

    combined = f"{norm_to}|{norm_cc}|{norm_subject}|{norm_body}|{thread_id}"

    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify_hash(
    to: str,
    cc: str,
    subject: str,
    body: str,
    thread_id: str,
    expected_hash: str
) -> bool:
    computed = compute_hash(to, cc, subject, body, thread_id)

    return hmac.compare_digest(computed, expected_hash)