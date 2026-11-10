import random
import time
from langchain_groq import ChatGroq
from app.config import settings


def get_llm(model: str) -> ChatGroq:
    return ChatGroq(
        model=model,
        temperature=0,
        timeout=30,
        max_retries=0,
        api_key=settings.groq_api_key
    )


def call_with_retry(fn, sleep_fn=None):
    if sleep_fn is None:
        sleep_fn = time.sleep
    
    max_retries = 2
    retry_count = 0
    
    while True:
        try:
            return fn()
        except Exception as e:
            status_code = None
            
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
            
            if status_code == 429:
                if retry_count >= max_retries:
                    raise
                
                sleep_duration = random.uniform(10, 20)
                sleep_fn(sleep_duration)
                retry_count += 1
            else:
                raise
