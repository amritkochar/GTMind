"""
Prompts and schemas for LLM interactions.
"""

EXTRACTION_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_insights",
        "description": "Pull key trends, companies (its context) and whitespace gaps from article text.",
        "parameters": {
            "type": "object",
            "properties": {
                "trends": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 3,
                },
                "companies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "context": {"type": "string"},
                        },
                        "required": ["name", "context"]
                    },
                },
                "whitespace_opportunities": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["trends", "companies", "whitespace_opportunities"],
        },
    },
}

EXTRACTION_SYSTEM_PROMPT = (
    "You are a focused industry research agent. Your job is to extract structured insights from articles.\n\n"
    "For each article, extract the following:\n"
    "1. Up to 3 concise, high-signal industry trends mentioned or implied.\n"
    "2. For every company referenced:\n"
    "   - name (string)\n"
    "   - context (string) a one-sentence summary explaining its mention or relevance in context.\n"
    "3. Any whitespace, gap, or unmet market need explicitly or implicitly highlighted.\n\n"
    "Return your output strictly using the provided JSON schema. Do not include free text or explanations outside the schema."
)