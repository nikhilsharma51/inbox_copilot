# Project Dependencies Versions

## Verified with pip freeze

- langchain: 1.4.9
- langchain-core: 1.7.6
- langchain-groq: 1.1.3
- groq: 0.37.1
- pydantic: 2.13.5
- python: 3.11.3

## Structured Output Method

Method used: `with_structured_output()`

This method is available on ChatGroq and uses function calling capabilities. 

For Groq models via langchain-groq 1.1.3:
- Default method: `with_structured_output()` (supports schema validation)
- Implementation: Converts Pydantic schema to function calling format and parses response

Model tested: `openai/gpt-oss-120b`
- Supports structured output via function calling
- Returns parsed Pydantic model instance
