import json
import re
import time
from typing import Optional

from openai import OpenAI

from config import settings

def _get_client() -> OpenAI:
    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )
    return OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url=settings.GROQ_API_BASE,
    )


ANALYZE_SYSTEM = """You are an expert customer-review analyst.
Your job: analyse a single review and return ONLY a valid JSON object — no prose, no markdown fences.

JSON schema (all fields required):
{
  "sentiment": "<positive|negative|neutral|mixed>",
  "confidence": <float 0.0-1.0>,
  "aspects": [
    {"aspect": "<aspect name>", "sentiment": "<positive|negative|neutral>", "score": <float 0.0-1.0>}
  ],
  "summary": "<one-sentence summary of the review>",
  "suggested_reply": "<polite professional business reply>",
  "key_phrases": ["<phrase1>", "<phrase2>"]
}

Rules:
- Extract every meaningful aspect (food, delivery, price, support, quality, packaging, staff, etc.)
- confidence must reflect how clearly positive/negative the overall tone is
- suggested_reply should directly address the reviewer's points
- key_phrases: up to 5 short phrases that capture the review's essence
- Return ONLY the JSON object, nothing else."""


BATCH_SUMMARY_SYSTEM = """You are a senior business intelligence analyst.
Given a JSON array of review analysis results, produce an executive summary report.
Return ONLY a valid JSON object — no prose, no markdown fences.

JSON schema:
{
  "top_complaints": ["<complaint1>", "<complaint2>", ...],   // up to 5
  "top_praise": ["<praise1>", "<praise2>", ...],             // up to 5
  "executive_summary": "<3-4 sentence overall insight paragraph>"
}"""


REPLY_SYSTEM = """You are a professional customer-success specialist.
Generate a warm, concise, business-appropriate reply to the customer review provided.
Tone guidance will be included in the user message.
Return ONLY the reply text — no preamble, no JSON, no quotes."""



def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse the first JSON object found."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Find first {...} block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not extract JSON from LLM response: {text[:200]}")


def _chat(client: OpenAI, system: str, user: str, temperature: float = 0.3) -> str:
    resp = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=1024,
    )
    return resp.choices[0].message.content or ""


def analyze_single_review(text: str) -> dict:
    """
    Analyse one review.  Returns a dict matching ReviewAnalysisResult fields.
    Raises on hard failures; individual field fallbacks are applied for soft failures.
    """
    client = _get_client()
    raw = _chat(client, ANALYZE_SYSTEM, f"Review to analyse:\n\n{text}")
    data = _extract_json(raw)

    # Normalise & apply defaults so the response schema is always satisfied
    data.setdefault("sentiment", "neutral")
    data.setdefault("confidence", 0.5)
    data.setdefault("aspects", [])
    data.setdefault("summary", "No summary available.")
    data.setdefault("suggested_reply", "Thank you for your feedback.")
    data.setdefault("key_phrases", [])

    # Clamp confidence
    data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))

    # Ensure aspect objects have required fields
    cleaned_aspects = []
    for a in data["aspects"]:
        if isinstance(a, dict) and "aspect" in a:
            cleaned_aspects.append(
                {
                    "aspect": a["aspect"],
                    "sentiment": a.get("sentiment", "neutral"),
                    "score": max(0.0, min(1.0, float(a.get("score", 0.5)))),
                }
            )
    data["aspects"] = cleaned_aspects

    return data


def analyze_reviews_batch(texts: list[str]) -> list[dict]:
    """
    Analyse each review individually and collect results.
    Failed reviews get an error field instead of raising globally.
    """
    results = []
    for text in texts:
        try:
            result = analyze_single_review(text)
            result["text"] = text
            result["error"] = None
        except Exception as exc:
            result = {
                "text": text,
                "sentiment": "neutral",
                "confidence": 0.0,
                "aspects": [],
                "summary": "Analysis failed.",
                "suggested_reply": "Thank you for your feedback.",
                "key_phrases": [],
                "error": str(exc),
            }
        results.append(result)
        # Small courtesy delay to avoid rate-limit bursts on free Groq tier
        time.sleep(0.15)
    return results


def generate_batch_insights(results: list[dict]) -> dict:
    """
    Call the LLM once with all results to get top complaints, praise, and an
    executive summary.  Falls back to simple heuristics on failure.
    """
    client = _get_client()
    # Send a lightweight version of results to stay within context limits
    slim = [
        {
            "sentiment": r.get("sentiment"),
            "aspects": r.get("aspects", []),
            "summary": r.get("summary", ""),
            "key_phrases": r.get("key_phrases", []),
        }
        for r in results
    ]
    user_msg = f"Review analysis results:\n\n{json.dumps(slim, indent=2)}"

    try:
        raw = _chat(client, BATCH_SUMMARY_SYSTEM, user_msg, temperature=0.4)
        data = _extract_json(raw)
        data.setdefault("top_complaints", [])
        data.setdefault("top_praise", [])
        data.setdefault("executive_summary", "No executive summary generated.")
        return data
    except Exception:
        # Heuristic fallback
        complaints = [
            r["summary"]
            for r in results
            if r.get("sentiment") in ("negative", "mixed") and r.get("summary")
        ][:5]
        praise = [
            r["summary"]
            for r in results
            if r.get("sentiment") == "positive" and r.get("summary")
        ][:5]
        return {
            "top_complaints": complaints,
            "top_praise": praise,
            "executive_summary": (
                f"Analysed {len(results)} reviews. "
                f"{sum(1 for r in results if r.get('sentiment') == 'positive')} positive, "
                f"{sum(1 for r in results if r.get('sentiment') == 'negative')} negative."
            ),
        }


def generate_reply(
    text: str,
    sentiment: Optional[str] = None,
    business_name: Optional[str] = None,
    tone: str = "professional",
) -> str:
    """Generate a standalone business reply for a single review."""
    client = _get_client()
    tone_map = {
        "professional": "formal and professional",
        "friendly": "warm and friendly",
        "apologetic": "sincere and apologetic",
    }
    tone_desc = tone_map.get(tone, "professional and polite")
    biz = f" on behalf of {business_name}" if business_name else ""
    sentiment_hint = f" The detected sentiment is {sentiment}." if sentiment else ""

    user_msg = (
        f"Write a {tone_desc} customer reply{biz}.{sentiment_hint}\n\n"
        f"Customer review:\n{text}"
    )
    return _chat(client, REPLY_SYSTEM, user_msg, temperature=0.5).strip()
