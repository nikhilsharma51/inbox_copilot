import re
import secrets
from ai_pipeline.config import PROMPT_VERSION


def build_prompt(subject: str, sender: str, body: str, categories: list) -> str:
    template_path = f"prompts/classify_{PROMPT_VERSION}.md"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    categories_text = '\n'.join([f"{name}: {desc}" for name, desc in categories])
    template = template.replace('{categories}', categories_text)
    
    tag = secrets.token_hex(8)
    
    tag_pattern = r'</?email_[0-9a-f]*>'
    subject = re.sub(tag_pattern, '', subject)
    sender = re.sub(tag_pattern, '', sender)
    body = re.sub(tag_pattern, '', body)
    
    email_content = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
    wrapped_email = f"<email_{tag}>\n{email_content}\n</email_{tag}>"
    
    return template + "\n" + wrapped_email
