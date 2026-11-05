from typing import Literal


class AIConfig:

    CLASSIFICATION_MODEL = "llama-3.1-8b-instant" 
    CLASSIFICATION_FALLBACK = "openai/gpt-oss-20b"

    DRAFTING_MODEL = "llama-3.3-70b-versatile"    
    DRAFTING_FALLBACK = "openai/gpt-oss-120b"

    EVAL_JUDGE_MODEL = "llama-3.3-70b-versatile"  

    RATE_LIMIT_PER_MINUTE = 30                     
    RATE_LIMIT_TOKENS_PER_MINUTE = 10000          

    TOKEN_BUDGET_CLASSIFICATION = 600               
    TOKEN_BUDGET_DRAFT = 2500                       
    DAILY_TOKEN_BUDGET = 100000                     
    
    LLM_TIMEOUT_SECONDS = 30
    MCP_CALL_TIMEOUT_SECONDS = 20
    MCP_STARTUP_TIMEOUT_SECONDS = 5

    PROMPT_VERSION = "v1"                        
    MODEL_VERSION = "phase-1"


    ENABLE_STRUCTURED_OUTPUT = True
    ENABLE_RETRY_ON_PARSE_ERROR = True
    MAX_RETRIES_ON_429 = 2


    BATCH_SIZE_CLASSIFICATION = 5                 


def get_config() -> AIConfig:
    return AIConfig()