import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

_model = None


def _ensure_model():
    """Lazy-initialize and return the Gemini model. Raises if API key missing."""
    global _model
    if _model is None:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")

    return _model


def generate_summary(text: str) -> str:
    """Generate a summary from text using Gemini.

    Returns a plain summary string.
    """
    model = _ensure_model()

    prompt = f"""Please provide a concise and clear summary of the following text.\nThe summary should capture the main points and be suitable for study purposes.\n\nText:\n{text}\n\nSummary:"""

    response = model.generate_content(prompt)
    # Prefer `text` attribute but fall back to a safe string conversion
    result = getattr(response, "text", None) or getattr(response, "content", None) or response
    return str(result).strip()


def _strip_code_fence_block(s: str) -> str:
    """If text contains a code fence (```), extract the inner content; otherwise return original."""
    if not s:
        return s
    # Look for a fenced block like ```json\n{...}\n``` or ```\n{...}\n```
    m = re.search(r"```(?:[a-zA-Z0-9_-]+)?\n(.*?)\n```", s, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    # Also handle cases without surrounding newlines: ```{...}```
    m = re.search(r"```(?:[a-zA-Z0-9_-]+)?(.*?)```", s, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return s


def _extract_json_substring(s: str) -> str:
    """Return the substring between the first '{' and the last '}', if present."""
    if not s:
        return s
    first = s.find("{")
    last = s.rfind("}")
    if first != -1 and last != -1 and last > first:
        return s[first:last + 1]
    return s


def _parse_json_from_text(s: str):
    """Try multiple strategies to parse JSON from model output. Returns dict or None."""
    if s is None:
        return None
    text = str(s).strip()

    # 1) Try raw parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) Strip code fence blocks and try again
    cleaned = _strip_code_fence_block(text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3) Extract first {...} substring and try
    candidate = _extract_json_substring(cleaned)
    try:
        return json.loads(candidate)
    except Exception:
        pass

    return None


def _ensure_even_flashcards(flashcards: list[dict]) -> list[dict]:
    """Guarantee an even number of flashcards.

    If the model returns an odd count, trim the final card.
    """
    if len(flashcards) % 2 == 1:
        return flashcards[:-1]
    return flashcards


def generate_study_materials(text: str) -> dict:
    """Generate study materials (summary, quiz, flashcards) using Gemini.

    Returns a dict with keys: 'summary', 'quiz', 'flashcards'. Uses json.loads
    to parse the model output. If parsing fails, returns safe defaults.
    """
    model = _ensure_model()

    prompt = f"""Return ONLY valid JSON. Do not include any markdown, code fences, or explanatory text.\n\nThe JSON object must have exactly these keys: \"summary\", \"quiz\", \"flashcards\".\n\n- \"summary\": a single concise study summary (string).\n- \"quiz\": an array of 5 multiple-choice questions. Each question must be an object with keys: \"question\" (string), \"options\" (array of 4 strings), \"answer\" (string, exactly one of the options).\n- \"flashcards\": an array of 6 objects with keys: \"term\" and \"definition\" (both strings). The number of flashcards must be EVEN.\n\nDo NOT use markdown code fences (```), do not add any explanation or extra fields, and return only the JSON object.\n\nText:\n{text}\n"""

    response = model.generate_content(prompt)
    result_text = getattr(response, "text", None) or getattr(response, "content", None) or response

    parsed = _parse_json_from_text(result_text)

    # Fallback defaults
    summary = ""
    quiz = []
    flashcards = []

    if isinstance(parsed, dict):
        summary = parsed.get("summary", "") if isinstance(parsed.get("summary", ""), str) else str(parsed.get("summary", ""))

        q = parsed.get("quiz", [])
        if isinstance(q, list):
            # Basic validation: keep only dict-like items
            quiz = [item for item in q if isinstance(item, dict)]

        f = parsed.get("flashcards", [])
        if isinstance(f, list):
            flashcards = [item for item in f if isinstance(item, dict)]

    flashcards = _ensure_even_flashcards(flashcards)

    return {"summary": summary or "", "quiz": quiz or [], "flashcards": flashcards or []}


def generate_quiz_from_topic(topic: str) -> list[dict]:
    """Generate a quiz strictly constrained to a provided topic using Gemini.
    
    Returns a list of 5 multiple-choice question dicts.
    Each dict matches: {'question': str, 'options': list[str], 'answer': str}.
    """
    model = _ensure_model()
    
    prompt = f"""Return ONLY valid JSON. Do not include any markdown, code fences, or explanatory text.
    
The JSON object must have exactly one key: "quiz".
"quiz": an array of exactly 5 multiple-choice questions about the topic "{topic}".
Each question in the array must be an object with:
- "question" (string)
- "options" (array of 4 distinct string choices)
- "answer" (string, must exactly match one of the options)

Do NOT use markdown code fences (```), do not add any explanation, and return only the JSON object.
"""
    
    response = model.generate_content(prompt)
    result_text = getattr(response, "text", None) or getattr(response, "content", None) or response
    
    parsed = _parse_json_from_text(result_text)
    
    quiz = []
    if isinstance(parsed, dict):
        q = parsed.get("quiz", [])
        if isinstance(q, list):
            quiz = [item for item in q if isinstance(item, dict)]
            
    return quiz


def generate_quiz_from_text(text: str) -> list[dict]:
    """Generate quiz questions directly from source text.

    Returns a list of quiz question objects.
    """
    model = _ensure_model()

    prompt = f"""Return ONLY valid JSON. Do not include markdown, code fences, or explanatory text.

The JSON object must have exactly one key: "quiz".
"quiz" must be an array of exactly 5 objects. Each object must include:
- "question" (string)
- "options" (array of 4 distinct strings)
- "answer" (string, exactly one of the options)

Text:
{text}
"""

    response = model.generate_content(prompt)
    result_text = getattr(response, "text", None) or getattr(response, "content", None) or response
    parsed = _parse_json_from_text(result_text)

    if isinstance(parsed, dict) and isinstance(parsed.get("quiz"), list):
        return [item for item in parsed.get("quiz", []) if isinstance(item, dict)]

    return []


def generate_flashcards_from_text(text: str) -> list[dict]:
    """Generate flashcards directly from source text.

    Returns a list of flashcard objects with an even count.
    """
    model = _ensure_model()

    prompt = f"""Return ONLY valid JSON. Do not include markdown, code fences, or explanatory text.

The JSON object must have exactly one key: "flashcards".
"flashcards" must be an array of exactly 6 objects.
Each object must include:
- "term" (string)
- "definition" (string)

The number of flashcards must be EVEN.

Text:
{text}
"""

    response = model.generate_content(prompt)
    result_text = getattr(response, "text", None) or getattr(response, "content", None) or response
    parsed = _parse_json_from_text(result_text)

    flashcards = []
    if isinstance(parsed, dict) and isinstance(parsed.get("flashcards"), list):
        flashcards = [item for item in parsed.get("flashcards", []) if isinstance(item, dict)]

    return _ensure_even_flashcards(flashcards)
