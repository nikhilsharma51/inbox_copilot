import logging
from ai_pipeline.schemas import Classification
from ai_pipeline.prompt import build_prompt
from ai_pipeline.llm import get_llm, call_with_retry
from ai_pipeline.config import CLASSIFY_MODEL
from ai_pipeline.preprocess import clean_email

logger = logging.getLogger(__name__)


def classify_thread(subject: str, sender: str, body: str, categories: list, llm=None) -> tuple:
    if llm is None:
        llm = get_llm(CLASSIFY_MODEL)
    
    body_clean = clean_email(body)
    prompt_text = build_prompt(subject, sender, body_clean, categories)
    
    category_names = [name for name, _ in categories]
    
    structured_llm = llm.with_structured_output(Classification, include_raw=True)
    
    def call_llm():
        return structured_llm.invoke(prompt_text)
    
    result = None
    usage_tokens = 0
    
    for attempt in range(2):
        try:
            response = call_with_retry(call_llm)
            
            if response is None:
                if attempt == 0:
                    continue
                break
            
            parsed = response
            if isinstance(response, dict):
                if 'parsed' in response:
                    parsed = response['parsed']
                    if 'raw' in response:
                        raw = response['raw']
                        if hasattr(raw, 'usage_metadata'):
                            usage_tokens = getattr(raw.usage_metadata, 'total_tokens', 0)
                elif hasattr(response, '__getitem__'):
                    parsed = response
            
            if not isinstance(parsed, Classification):
                if isinstance(parsed, dict):
                    if 'summary' in parsed and len(parsed['summary']) > 160:
                        parsed['summary'] = parsed['summary'][:160]
                    parsed = Classification(**parsed)
                else:
                    parsed = None
            
            if parsed is None:
                if attempt == 0:
                    continue
                break
            
            if parsed.category not in category_names:
                if attempt == 0:
                    continue
                break
            
            if not isinstance(parsed.priority, int) or parsed.priority < 1 or parsed.priority > 4:
                if attempt == 0:
                    continue
                break
            
            if not isinstance(parsed.confidence, (int, float)) or parsed.confidence < 0 or parsed.confidence > 1:
                if attempt == 0:
                    continue
                break
            
            if len(parsed.summary) > 160:
                parsed.summary = parsed.summary[:160]
            
            result = parsed
            break
        
        except Exception as e:
            if attempt == 0:
                continue
            break
    
    if result is None:
        result = Classification(
            category="Needs Review",
            summary="",
            needs_reply=False,
            priority=3,
            confidence=0.0
        )
    
    return (result, usage_tokens)
