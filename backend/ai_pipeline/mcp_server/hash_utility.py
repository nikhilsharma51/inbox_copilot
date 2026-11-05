"""Hash utilities for approval verification."""

import hashlib
import hmac
from email.utils import getaddresses


def norm_text(s: str) -> str:
    """
    Normalize text for hashing.

    - Line endings: CRLF/CR -> LF
    - Trailing spaces: remove from each line
    - Outer whitespace: strip
    """
    # Normalize line endings
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing spaces from each line
    lines = (line.rstrip() for line in s.split("\n"))

    # Join and strip outer whitespace
    return "\n".join(lines).strip()


def norm_addrs(addr_string: str) -> str:
    """
    Normalize email address header for hashing.

    - Parse addresses (handles "Name <email>" format)
    - Extract emails only
    - Convert to lowercase
    - Sort
    - Join with ", "
    """
    # Parse addresses
    parsed = getaddresses([addr_string])

    # Extract emails, convert to lowercase, deduplicate, and sort
    emails = sorted({email.lower() for _, email in parsed if email})

    return ", ".join(emails)


def compute_hash(
    to: str,
    cc: str,
    subject: str,
    body: str,
    thread_id: str
) -> str:
    """
    Compute approval hash for a draft.

    This hash ensures the draft hasn't been tampered with before sending.
    All fields are normalized before hashing.
    """
    # Normalize each field
    norm_to = norm_addrs(to)
    norm_cc = norm_addrs(cc)
    norm_subject = norm_text(subject)
    norm_body = norm_text(body)

    # Concatenate all fields with delimiter
    combined = f"{norm_to}|{norm_cc}|{norm_subject}|{norm_body}|{thread_id}"

    # Compute SHA256
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify_hash(
    to: str,
    cc: str,
    subject: str,
    body: str,
    thread_id: str,
    expected_hash: str
) -> bool:
    """
    Verify a draft hash.

    Returns True if hash matches, False otherwise.
    """
    computed = compute_hash(to, cc, subject, body, thread_id)

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed, expected_hash)