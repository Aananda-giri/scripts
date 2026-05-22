import json

from openai import OpenAI

ALLOWED_VALUES = {
    "job_category": [
        "IT & Software",
        "Advertising and Marketing",
        "Data and Analytics",
        "Design and UX",
        "General",
        "Project Management",
        "Sales",
    ],
    "job_level": [
        "Internship",
        "Entry Level",
        "Mid Level",
        "Senior Level",
    ],
    "tags": [
        "Fast Growing Companies",
        "Fortune 1000",
    ],
}

EXTRACTION_SYSTEM_PROMPT = """You are a query understanding system for a job search engine.
Your task is to extract structured metadata filters and a cleaned semantic query
from the user's raw search query.

## Rules
1. Extract only the fields listed below. Use null for any field not mentioned.
2. For each field, ONLY use values from the allowed lists. Never invent values.
3. For the semantic_query, rewrite the user's query to remove filter phrases
   (like "mid-level", "in IT", "Fortune 1000") so it focuses on skills, role
   descriptions, and what the candidate wants. Preserve location references
   if present.
4. Return ONLY valid JSON, no other text."""


def _build_extraction_prompt(query: str) -> str:
    def fmt_list(items):
        return ", ".join(items)

    return f"""## Allowed Values
job_category: {fmt_list(ALLOWED_VALUES["job_category"])}
job_level: {fmt_list(ALLOWED_VALUES["job_level"])}
tags: {fmt_list(ALLOWED_VALUES["tags"])}

## User Query
{query}

## Output Format
Return JSON with exactly these keys:
{{
  "job_category": null or one of the allowed values,
  "job_level": null or one of the allowed values,
  "tags": [] or subset of allowed values,
  "semantic_query": "cleaned query string"
}}"""


def validate_filters(extracted: dict) -> dict:
    result = {}
    for field in ["job_category", "job_level"]:
        val = extracted.get(field)
        if val and val in ALLOWED_VALUES[field]:
            result[field] = [val]
    tag_vals = extracted.get("tags") or []
    valid_tags = [t for t in tag_vals if t in ALLOWED_VALUES["tags"]]
    if valid_tags:
        result["tags"] = valid_tags
    return result


class EntityExtractor:
    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 base_url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def extract(self, query: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": _build_extraction_prompt(query)},
            ],
            temperature=0.0,
            max_tokens=256,
        )
        raw = response.choices[0].message.content.strip()

        try:
            extracted = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: try to find JSON in the response
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    extracted = json.loads(match.group(0))
                except json.JSONDecodeError:
                    extracted = {}
            else:
                extracted = {}

        filters = validate_filters(extracted)
        semantic_query = extracted.get("semantic_query") or query

        return {
            "filters": filters,
            "semantic_query": semantic_query,
        }
