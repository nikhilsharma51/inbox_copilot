import re
import unicodedata
from bs4 import BeautifulSoup
from ai_pipeline.config import MAX_BODY_CHARS


def _looks_like_html(text: str) -> bool:
    return bool(re.search(r'<[a-z]+[^>]*>', text, re.IGNORECASE))


def _parse_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    
    for script in soup.find_all('script'):
        script.decompose()
    
    for style in soup.find_all('style'):
        style.decompose()
    
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()
    
    comments = soup.find_all(string=lambda text: isinstance(text, type(soup.contents[0])) if soup.contents else False)
    for item in soup.contents[:]:
        if isinstance(item, type(soup.contents[0]).__bases__[0]) if hasattr(type(soup.contents[0]), '__bases__') else False:
            continue
    
    for element in soup.find_all(True):
        style_attr = element.get('style', '')
        if style_attr:
            style_lower = style_attr.lower()
            style_normalized = re.sub(r'\s+', '', style_lower)
            if 'display:none' in style_normalized or 'visibility:hidden' in style_normalized or 'font-size:0' in style_normalized:
                element.decompose()
    
    return soup.get_text()


def _normalize(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    zero_width_chars = '\u200b\u200c\u200d\u2060\ufeff'
    for char in zero_width_chars:
        text = text.replace(char, '')
    return text


def _cut_quoted_and_signatures(text: str) -> str:
    lines = text.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        if re.search(r'^On\s+.+\s+wrote:', line, re.IGNORECASE):
            break
        if line.lstrip().startswith('>'):
            continue
        result.append(line)
    
    text = '\n'.join(result)
    
    signature_markers = [
        r'^\s*--\s*$',
        r'Sent from my',
        r'This email and any attachments',
        r'Confidentiality notice',
        r'Unsubscribe'
    ]
    
    lines = text.split('\n')
    cutoff_index = len(lines)
    for i, line in enumerate(lines):
        for marker in signature_markers:
            if re.search(marker, line, re.IGNORECASE):
                cutoff_index = i
                break
        if cutoff_index != len(lines):
            break
    
    text = '\n'.join(lines[:cutoff_index])
    return text.rstrip()


def _redact(text: str) -> str:
    def replace_code(match):
        pos = match.start()
        context_start = max(0, pos - 40)
        context_end = min(len(text), pos + 40)
        context = text[context_start:context_end].lower()
        
        if any(word in context for word in ['code', 'otp', 'verification']):
            return '[REDACTED_CODE]'
        return match.group(0)
    
    text = re.sub(r'\d{4,8}', replace_code, text)
    
    text = re.sub(
        r'\d[\d\s\-]{11,17}\d',
        '[REDACTED_NUMBER]',
        text
    )
    
    text = re.sub(r'\?[^\s]*', '', text)
    
    return text


def clean_email(raw: str) -> str:
    if not raw:
        return ''
    
    if _looks_like_html(raw):
        text = _parse_html(raw)
    else:
        text = raw
    
    text = _normalize(text)
    text = _cut_quoted_and_signatures(text)
    text = _redact(text)
    
    if len(text) > MAX_BODY_CHARS:
        text = text[:MAX_BODY_CHARS] + ' [truncated]'
    
    return text
