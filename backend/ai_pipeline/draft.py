import re
from email.utils import getaddresses

from ai_pipeline.schemas import DraftOut
from ai_pipeline.prompt import build_draft_prompt
from ai_pipeline.llm import get_llm, call_with_retry
from ai_pipeline.config import DRAFT_MODEL
from ai_pipeline.preprocess import clean_email


class DraftFailed(Exception):
    pass


def pick_recipients(thread, my_email) -> list[str]:
    messages = thread.get("messages", [])
    
    if not messages:
        return []
    
    my_email_lower = my_email.strip().lower()
    latest_message = messages[-1]
    
    if latest_message.get("is_from_me"):
        header_str = latest_message.get("to", "")
    else:
        reply_to = latest_message.get("reply_to", "")
        sender = latest_message.get("sender", "")
        header_str = reply_to if reply_to else sender
    
    recipients = []
    seen = set()
    
    for _, address in getaddresses([header_str]):
        address = address.strip().lower()
        
        if address and address != my_email_lower and address not in seen:
            recipients.append(address)
            seen.add(address)
    
    return recipients


def recipient_warning(thread) -> str or None:
    messages = thread.get("messages", [])
    
    if not messages:
        return None
    
    latest_message = messages[-1]
    
    if latest_message.get("is_from_me"):
        return None
    
    sender = latest_message.get("sender", "").lower()
    
    sender_local = sender.split("@")[0] if "@" in sender else sender
    
    if sender_local.startswith("noreply") or sender_local.startswith("no-reply") or sender_local.startswith("donotreply"):
        return "this sender probably does not read replies"
    
    if latest_message.get("list_unsubscribe"):
        return "this sender probably does not read replies"
    
    return None


def write_draft(thread, instruction, style, user_name, llm=None) -> DraftOut:
    if llm is None:
        llm = get_llm(DRAFT_MODEL)
    
    messages = thread.get("messages", [])
    cleaned_messages = []
    
    for msg in messages:
        cleaned_msg = msg.copy()
        cleaned_msg['body'] = clean_email(msg.get('body', ''))
        cleaned_messages.append(cleaned_msg)
    
    prompt_text = build_draft_prompt(instruction, cleaned_messages)
    
    structured_llm = llm.with_structured_output(DraftOut, include_raw=True)
    
    def call_llm():
        return structured_llm.invoke(prompt_text)
    
    result = None
    
    for attempt in range(2):
        try:
            response = call_with_retry(call_llm)
            
            if response is None:
                if attempt == 0:
                    continue
                break
            
            parsed = response
            if isinstance(response, dict) and 'parsed' in response:
                parsed = response['parsed']
            
            if not isinstance(parsed, DraftOut):
                if isinstance(parsed, dict):
                    parsed = DraftOut(**parsed)
                else:
                    parsed = None
            
            if parsed is None:
                if attempt == 0:
                    continue
                break
            
            parsed.body = _strip_signature(parsed.body)
            parsed.body = parsed.body.rstrip() + f"\n\n{user_name}"
            
            subject = thread.get("messages", [{}])[0].get("subject", "")
            parsed.subject = _normalize_subject(subject)
            
            result = parsed
            break
        
        except Exception as e:
            if attempt == 0:
                continue
            break
    
    if result is None:
        raise DraftFailed("Failed to generate draft after retries")
    
    return result


def _strip_signature(body: str) -> str:
    lines = body.split('\n')
    
    signature_markers = [
        r'^Best regards[,:]?',
        r'^Thanks[,:]?',
        r'^Regards[,:]?',
        r'^Sincerely[,:]?',
    ]
    
    for i, line in enumerate(lines):
        for marker in signature_markers:
            if re.match(marker, line, re.IGNORECASE):
                return '\n'.join(lines[:i]).rstrip()
    
    return body.rstrip()


def _normalize_subject(subject: str) -> str:
    while re.match(r'^(re|RE|Re):\s*', subject, re.IGNORECASE):
        subject = re.sub(r'^(re|RE|Re):\s*', '', subject, count=1, flags=re.IGNORECASE).strip()
    return f"Re: {subject}"


def flag_draft(draft: DraftOut, thread, instruction: str) -> list[str]:
    warnings = []
    
    body_lower = draft.body.lower()
    thread_text = ' '.join([msg.get('body', '') for msg in thread.get('messages', [])])
    thread_lower = thread_text.lower()
    instruction_lower = instruction.lower()
    
    urls = re.findall(r'https?://[^\s]+', draft.body)
    for url in urls:
        domain = re.search(r'https?://([^\s/]+)', url).group(1) if re.search(r'https?://([^\s/]+)', url) else ''
        if domain and domain not in thread_lower and domain not in instruction_lower:
            warnings.append(f"URL {url} not found in thread or instruction")
    
    emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\b', draft.body)
    for email in emails:
        if email.lower() not in thread_lower and email.lower() not in instruction_lower:
            warnings.append(f"Email address {email} not found in thread or instruction")
    
    if re.search(r'!\[.*?\]\(.*?\)', draft.body):
        warnings.append("Markdown image detected in draft")
    
    if re.search(r'<[^>]+>', draft.body):
        warnings.append("HTML tag detected in draft")
    
    if re.search(r'gsk_\w+', draft.body):
        warnings.append("API key pattern (gsk_) detected")
    
    if re.search(r'ya29\.\w+', draft.body):
        warnings.append("API key pattern (ya29.) detected")
    
    if re.search(r'AIza\w+', draft.body):
        warnings.append("API key pattern (AIza) detected")
    
    return warnings
