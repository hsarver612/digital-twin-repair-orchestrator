import json
import re

def extract_json(text: str) -> dict:
    """
    Extract the first JSON object found in text.
    Assumes agent is instructed to output JSON only, but this guards against slight deviations.
    """
    text = text.strip()

    # If it's pure JSON
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    # Otherwise, attempt to find a JSON object
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in agent response.")
    return json.loads(match.group(0))
