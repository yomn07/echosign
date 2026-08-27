import os
import re
import asyncio
import logging

import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv


router = APIRouter(
    tags=["Translation"],
)

load_dotenv()

logger = logging.getLogger("translation")

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.warning("HF_TOKEN is not set — translation calls will fail.")

HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

SYSTEM_PROMPT = """You are an ASL gloss converter. Convert English to ASL gloss.

OUTPUT FORMAT (strict):
- One line only, uppercase ASL gloss, words separated by single spaces
- No punctuation, no hyphens, no explanations, no labels, no quotes
- Never repeat the English sentence

GRAMMAR RULES:
- Use ASL word order (TIME-TOPIC-COMMENT), not English word order
- Drop articles (A, AN, THE) and auxiliary verbs (IS, AM, ARE, WAS, WERE, BE, WILL, DO, DOES, DID)
- Time expressions go first
- WH-questions go at the end
- Keep numbers, keep possessives (MY, YOUR, HIS, HER, THEIR)
- Fingerspell unknown words, names, and proper nouns in uppercase

EXAMPLES:
English: I am going to the store tomorrow
Gloss: TOMORROW STORE I GO

English: What is your name?
Gloss: YOUR NAME WHAT

English: She doesn't like coffee
Gloss: COFFEE SHE LIKE NOT

Respond with ONLY the gloss line, nothing else."""


class TranslationRequest(BaseModel):
    text: str


def clean_gloss(raw: str) -> str:
    """Sanitize the model's raw output into a clean ASL gloss line."""
    text = raw.strip()

    # strip common leaked labels like "GLOSS:" or "ASL:"
    text = re.sub(r"^(GLOSS|ASL GLOSS|ASL)\s*:\s*", "", text, flags=re.IGNORECASE)

    # take only the first non-empty line
    lines = [line for line in text.splitlines() if line.strip()]
    text = lines[0] if lines else ""

    # strip quotes if the model wrapped the answer
    text = text.strip("\"'")

    # keep only letters, numbers, and spaces, uppercase everything
    text = re.sub(r"[^A-Za-z0-9 ]", "", text).upper()

    # collapse extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


async def call_hf_with_retry(
    client: httpx.AsyncClient,
    payload: dict,
    headers: dict,
    retries: int = 2,
):
    """Call the HF router with retries on timeouts / rate limits / cold starts."""
    last_response = None

    for attempt in range(retries + 1):
        try:
            response = await client.post(HF_API_URL, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            last_response = exc
            logger.warning("HF request timed out (attempt %s/%s)", attempt + 1, retries + 1)
            await asyncio.sleep(1.5 * (attempt + 1))
            continue
        except httpx.HTTPError as exc:
            last_response = exc
            logger.warning("HF request failed: %s (attempt %s/%s)", exc, attempt + 1, retries + 1)
            await asyncio.sleep(1.5 * (attempt + 1))
            continue

        last_response = response

        if response.status_code == 200:
            return response

        # retry on rate limit or model cold-start (HF serverless)
        if response.status_code in (429, 503):
            logger.warning(
                "HF returned %s, retrying (attempt %s/%s)",
                response.status_code,
                attempt + 1,
                retries + 1,
            )
            await asyncio.sleep(1.5 * (attempt + 1))
            continue

        # any other error status is not worth retrying
        break

    return last_response


@router.post("/translate")
async def translate_to_gloss(request: TranslationRequest):
    text = request.text.strip()

    if not text:
        return {"error": "text field is empty"}

    if not HF_TOKEN:
        return {"error": "server misconfigured: HF_TOKEN not set"}

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "max_tokens": 100,
        "temperature": 0,
        "stop": ["\n", "English:", "Gloss:"],
    }

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        result = await call_hf_with_retry(client, payload, headers)

    if isinstance(result, Exception) or result is None:
        logger.error("Translation request failed after retries: %s", result)
        return {"error": "translation service unavailable"}

    response: httpx.Response = result

    if response.status_code != 200:
        logger.error("HF returned non-200: %s %s", response.status_code, response.text)
        return {"error": "translation service returned an error"}

    try:
        data = response.json()
        raw_output = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError) as exc:
        logger.error("Unexpected HF response shape: %s", exc)
        return {"error": "translation service returned an unexpected response"}

    gloss = clean_gloss(raw_output)

    if not gloss:
        logger.warning("Model returned empty gloss for input: %r raw: %r", text, raw_output)
        return {"error": "model returned an empty gloss"}

    return {"gloss": gloss}