import os
import streamlit as st
from lyzr_python_sdk import LyzrAgentAPI  # lyzr-python-sdk [1](https://github.com/LyzrCore/lyzr-python)[2](https://docs.lyzr.ai/agent-api/python-client/python-client)

def get_secret(name: str):
    # Prefer Streamlit secrets, fallback to env
    if name in st.secrets:
        return st.secrets[name]
    return os.environ.get(name)

def get_client():
    api_key = get_secret("LYZR_AGENT_API_KEY")
    if not api_key:
        raise RuntimeError("Missing LYZR_AGENT_API_KEY. Add it to Streamlit Secrets.")
    return LyzrAgentAPI(api_key=api_key)  # [1](https://github.com/LyzrCore/lyzr-python)[2](https://docs.lyzr.ai/agent-api/python-client/python-client)

def _extract_agent_text(raw):
    """
    Lyzr SDK commonly returns a dict like:
      {"response": "<agent_text>", "module_outputs": {...}}
    We want ONLY the agent_text string (which should be JSON-only per your system prompt).
    """
    if isinstance(raw, str):
        return raw

    if isinstance(raw, dict):
        # Most common field (based on what you pasted)
        if "response" in raw and isinstance(raw["response"], str):
            return raw["response"]

        # Fallbacks (just in case response schema differs)
        for k in ["message", "content", "text", "output"]:
            if k in raw and isinstance(raw[k], str):
                return raw[k]

        # Nested fallback
        if "data" in raw and isinstance(raw["data"], dict):
            for k in ["response", "message", "content", "text", "output"]:
                if k in raw["data"] and isinstance(raw["data"][k], str):
                    return raw["data"][k]

    # Last resort (may not be JSON-safe, but avoids crashing here)
    return str(raw)

def chat_with_agent(message: str, user_id: str, agent_id: str, session_id: str | None = None):
    client = get_client()
    payload = {
        "user_id": user_id,
        "agent_id": agent_id,
        "message": message,
    }
    if session_id:
        payload["session_id"] = session_id  # session continuity [1](https://github.com/LyzrCore/lyzr-python)[2](https://docs.lyzr.ai/agent-api/python-client/python-client)

    raw = client.inference.chat(payload)  # [1](https://github.com/LyzrCore/lyzr-python)[2](https://docs.lyzr.ai/agent-api/python-client/python-client)
    return _extract_agent_text(raw)
