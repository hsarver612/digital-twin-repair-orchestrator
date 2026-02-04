import os
from lyzr_python_sdk import LyzrAgentAPI  # provided by lyzr-python-sdk [2](https://github.com/LyzrCore/lyzr-python)[3](https://docs.lyzr.ai/agent-api/python-client/python-client)

def get_client():
    api_key = os.environ.get("LYZR_AGENT_API_KEY")
    if not api_key:
        raise RuntimeError("Missing LYZR_AGENT_API_KEY. Add it to Streamlit Secrets.")
    return LyzrAgentAPI(api_key=api_key)  # [2](https://github.com/LyzrCore/lyzr-python)[3](https://docs.lyzr.ai/agent-api/python-client/python-client)

def chat_with_agent(message: str, user_id: str, agent_id: str, session_id: str | None = None):
    client = get_client()
    payload = {
        "user_id": user_id,
        "agent_id": agent_id,
        "message": message,
    }
    # session_id enables conversation continuity (optional) [2](https://github.com/LyzrCore/lyzr-python)[3](https://docs.lyzr.ai/agent-api/python-client/python-client)
    if session_id:
        payload["session_id"] = session_id

    return client.inference.chat(payload)  # [2](https://github.com/LyzrCore/lyzr-python)[3](https://docs.lyzr.ai/agent-api/python-client/python-client)
