import re
import secrets
from ai_pipeline.config import PROMPT_VERSION


def _generate_tag_and_strip_lookalikes(text: str) -> tuple:
    tag = secrets.token_hex(8)
    tag_pattern = r'</?email_[0-9a-f]*>'
    text_cleaned = re.sub(tag_pattern, '', text)
    return tag, text_cleaned


def build_prompt(subject: str, sender: str, body: str, categories: list) -> str:
    template_path = f"prompts/classify_{PROMPT_VERSION}.md"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    categories_text = '\n'.join([f"{name}: {desc}" for name, desc in categories])
    template = template.replace('{categories}', categories_text)
    
    tag, subject_clean = _generate_tag_and_strip_lookalikes(subject)
    _, sender_clean = _generate_tag_and_strip_lookalikes(sender)
    _, body_clean = _generate_tag_and_strip_lookalikes(body)
    
    email_content = f"Subject: {subject_clean}\nFrom: {sender_clean}\n\n{body_clean}"
    wrapped_email = f"<email_{tag}>\n{email_content}\n</email_{tag}>"
    
    return template + "\n" + wrapped_email


def build_draft_prompt(instruction: str, thread_messages: list) -> str:
    template_path = f"prompts/draft_{PROMPT_VERSION}.md"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    tag, _ = _generate_tag_and_strip_lookalikes("")
    
    message_texts = []
    for msg in thread_messages:
        sender = msg.get('sender', '')
        body = msg.get('body', '')
        is_from_me = msg.get('is_from_me', False)
        
        _, sender_clean = _generate_tag_and_strip_lookalikes(sender)
        _, body_clean = _generate_tag_and_strip_lookalikes(body)
        
        from_label = "You" if is_from_me else sender_clean
        message_texts.append(f"{from_label}:\n{body_clean}")
    
    messages_block = "\n\n".join(message_texts)
    wrapped_thread = f"<email_{tag}>\n{messages_block}\n</email_{tag}>"
    
    return template + f"\nUser instruction: {instruction}\n\n" + wrapped_thread
