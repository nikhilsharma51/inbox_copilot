import re
import unicodedata
from typing import Optional
from bs4 import BeautifulSoup

def preprocess(html_body: Optional[str], text_limit: int = 4000) -> str:
    """
    Preprocess email body for classification.

    Steps:
    1. HTML to text
    2. Unicode normalization
    3. Strip quoted replies and signatures
    4. Redact sensitive information
    5. Truncate to token budget
    """

    if not html_body:
        return ""

    soup = BeautifulSoup(html_body, "html.parser")

    for tag in soup(["script", "style", "meta"]):
        tag.decompose()

    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none")):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    text = unicodedata.normalize("NFKC", text)

    text = re.sub(
        r"[\u200B-\u200D\u2060\uFEFF\u202A-\u202E\u2066-\u2069]",
        "",
        text
    )

    lines = text.split("\n")
    output_lines = []
    in_quote = False

    for line in lines:
        if re.match(
            r"^\s*(On .* wrote:|>|From:|Sent:)",
            line,
            re.IGNORECASE
        ):
            in_quote = True
            continue

        if in_quote and not line.strip():
            in_quote = False
            continue

        if not in_quote:
            output_lines.append(line)

    text = "\n".join(output_lines).strip()

    text = re.sub(
        r"(?i)(?:code|otp|verification|verify|enter|confirm)[\s:]*(\d{4,8})",
        "OTP_REDACTED",
        text
    )

    text = re.sub(r"\b\d{16,}\b", "CARD_REDACTED", text)

    text = re.sub(r"\b\d{10,}\b", "PHONE_REDACTED", text)

    text = re.sub(
        r"(\?[^&\s]*=[^&\s]*)",
        "?PARAMS_REDACTED",
        text
    )

    token_estimate = len(text) // 4

    if token_estimate > text_limit:
        text = text[:text_limit * 4]
        text += "\n[TRUNCATED]"

    return text
