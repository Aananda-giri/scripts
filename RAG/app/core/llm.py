from google import genai
from google.genai import types

SYSTEM_INSTRUCTION = """You are a precise job search assistant. Your role is to match job \
seekers with relevant positions based on their queries, using retrieved job \
description chunks as your source of truth.

## Core Rules
1. Only use information from the provided job description chunks. Do not invent details.
2. If the retrieved chunks do not contain enough information, say so clearly.
3. Cite specific job IDs and companies when referencing jobs.
4. Be concise and actionable.

## Response Format
Start with a brief overall assessment (1-2 sentences).
Then, for each relevant job (max 3), provide:
  - **Job Title** at **Company** (Location)
  - **Why it matches**: specific evidence from the description
  - **Key Requirements**: top 3-5 qualifications mentioned
  - **Relevance**: High / Medium / Low

If no jobs match, say so and suggest alternative search terms."""


class GeminiLLM:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_answer(self, query: str, chunks: list[dict]) -> str:
        if not chunks:
            return "No matching job descriptions found. Try broadening your search terms."

        context = self._format_context(chunks)
        prompt = self._build_prompt(query, context)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        return response.text

    @staticmethod
    def _format_context(chunks: list[dict]) -> str:
        parts = []
        for c in chunks:
            header = (
                f"[Source: {c.get('job_id', '?')} - "
                f"{c.get('job_title', 'Unknown')} at "
                f"{c.get('company_name', 'Unknown')} "
                f"({c.get('job_location', 'Unknown')})]"
            )
            text = c.get("text", "")
            if len(text) > 800:
                text = text[:800] + "..."
            parts.append(f"{header}\n{text}")
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _build_prompt(query: str, context: str) -> str:
        return f"""## User Query
{query}

## Retrieved Job Descriptions
{context}

## Instructions
Based on the retrieved job description sections above, answer the user's query.
Follow the response format specified in the system instructions.
If the retrieved information does not fully answer the query, acknowledge the gap."""
