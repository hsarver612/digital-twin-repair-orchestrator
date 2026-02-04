import os
import uuid
from core.agent.lyzr_client import chat_with_agent
from core.agent.toolbelt import run_tool
from core.agent.util import extract_json
from core.agent.policy import requires_po_approval, requires_overflow_approval

def summarize_state(state: dict) -> dict:
    """Small summary to avoid sending big tables to the agent."""
    summary = {}
    if "fleet" in state:
        summary["fleet_size"] = len(state["fleet"])
        summary["avg_risk"] = float(state["fleet"]["risk_score"].mean())
    if "claims" in state:
        summary["claims"] = int(len(state["claims"]))
        summary["repairs"] = int((~state["claims"]["total_loss"]).sum()) if len(state["claims"]) else 0
        summary["total_losses"] = int((state["claims"]["total_loss"]).sum()) if len(state["claims"]) else 0
    if "parts_summary" in state:
        ps = state["parts_summary"]
        summary["top_parts"] = ps.head(5).to_dict(orient="records") if len(ps) else []
    if "repairs_alloc" in state:
        ra = state["repairs_alloc"]
        summary["unassigned_repairs"] = int((ra["assigned_shop"] == "UNASSIGNED").sum()) if len(ra) else 0
    if "po" in state:
        summary["po_lines"] = len(state["po"].get("lines", []))
    return summary

def run_agent_loop(goal: str, scenario: dict, max_steps: int = 12, execute_actions: bool = False, existing_session_id: str | None = None):
    """
    Returns: {status, session_id, log, state, final}
    status: RUNNING/COMPLETED/AWAITING_APPROVAL/ERROR
    """
    agent_id = os.environ.get("LYZR_AGENT_ID")
    if not agent_id:
        raise RuntimeError("Missing LYZR_AGENT_ID in Streamlit Secrets.")

    user_id = scenario.get("user_id", "hackathon-user")
    session_id = existing_session_id or f"session-{uuid.uuid4()}"

    state = {}
    log = []

    # Kickoff message to agent
    kickoff = {
        "goal": goal,
        "scenario": scenario,
        "state_summary": summarize_state(state),
        "instruction": "Begin by proposing the first tool_call JSON."
    }

    msg = str(kickoff)
    resp = chat_with_agent(msg, user_id=user_id, agent_id=agent_id, session_id=session_id)  # uses session_id for continuity [2](https://github.com/LyzrCore/lyzr-python)[3](https://docs.lyzr.ai/agent-api/python-client/python-client)

    for step in range(max_steps):
        # 1) parse agent JSON
        agent_text = resp if isinstance(resp, str) else str(resp)
        # If the SDK returns structured objects, you may need to locate the text field.
        # For hackathon simplicity: treat response as string-like.
        try:
            cmd = extract_json(agent_text)
        except Exception as e:
            return {"status": "ERROR", "session_id": session_id, "log": log, "state": state, "final": {"error": f"Failed to parse agent JSON: {e}", "raw": agent_text}}

        log.append({"step": step + 1, "agent_cmd": cmd})

        # 2) handle command types
        if cmd.get("type") == "final":
            return {"status": "COMPLETED", "session_id": session_id, "log": log, "state": state, "final": cmd}

        if cmd.get("type") == "approval_required":
            # Pause and let UI ask user
            return {"status": "AWAITING_APPROVAL", "session_id": session_id, "log": log, "state": state, "final": cmd}

        if cmd.get("type") != "tool_call":
            return {"status": "ERROR", "session_id": session_id, "log": log, "state": state, "final": {"error": f"Unknown command type: {cmd.get('type')}", "raw": cmd}}

        tool = cmd["tool"]
        args = cmd.get("args", {})

        # 3) execute tool locally
        tool_result = run_tool(tool, args, state)
        log.append({"step": step + 1, "tool": tool, "tool_result": tool_result})

        # 4) enforce policy gates (optional belt-and-suspenders)
        if tool == "shops.allocate_repairs" and requires_overflow_approval(tool_result):
            pause = {
                "type": "approval_required",
                "action": "overflow_routing",
                "reason": "Unassigned repairs exceed threshold; overflow routing requires approval.",
                "payload": tool_result
            }
            return {"status": "AWAITING_APPROVAL", "session_id": session_id, "log": log, "state": state, "final": pause}

        if tool == "procurement.create_purchase_order" and requires_po_approval(tool_result):
            pause = {
                "type": "approval_required",
                "action": "submit_purchase_order",
                "reason": "PO exceeds threshold; requires approval before submitting.",
                "payload": {"po_summary": tool_result, "po": state.get("po")}
            }
            return {"status": "AWAITING_APPROVAL", "session_id": session_id, "log": log, "state": state, "final": pause}

        # 5) send observation back to agent
        observation = {
            "tool_ran": tool,
            "tool_result": tool_result,
            "state_summary": summarize_state(state),
            "execute_actions": execute_actions
        }
        resp = chat_with_agent(str(observation), user_id=user_id, agent_id=agent_id, session_id=session_id)  # continuity via session_id [2](https://github.com/LyzrCore/lyzr-python)[3](https://docs.lyzr.ai/agent-api/python-client/python-client)

    return {"status": "ERROR", "session_id": session_id, "log": log, "state": state, "final": {"error": "Max steps reached without final."}}
