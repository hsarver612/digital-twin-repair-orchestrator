import streamlit as st
from core.agent.runner_lyzr import run_agent_loop

st.set_page_config(layout="wide")
st.title("🤖 Agent Console (Lyzr Tool-Calling)")

with st.sidebar:
    st.header("Goal & Scenario")
    goal = st.text_area("Agent goal", "Forecast repair demand and align parts + shop capacity to minimize cycle time.", height=100)

    fleet_size = st.slider("Fleet size", 500, 10000, 3000, step=500)
    horizon = st.selectbox("Horizon (days)", [7, 14, 30], index=1)
    weather = st.selectbox("Weather", ["normal", "rain", "snow", "hail"], index=0)
    seed = st.number_input("Seed", 1, 99999, 42)
    po_threshold = st.slider("PO min threshold (qty)", 5, 100, 20, step=5)
    execute = st.checkbox("Execute actions (submit PO)", value=False)

    run_btn = st.button("Run Agent")

scenario = {
    "fleet_size": int(fleet_size),
    "horizon": int(horizon),
    "weather": weather,
    "seed": int(seed),
    "po_threshold": int(po_threshold),
    "user_id": "hackathon-user"
}

if run_btn:
    result = run_agent_loop(goal=goal, scenario=scenario, execute_actions=execute)
    st.session_state["agent_result"] = result

if "agent_result" not in st.session_state:
    st.info("Click **Run Agent** to start the Lyzr-controlled agent loop.")
    st.stop()

result = st.session_state["agent_result"]

# Status
st.subheader(f"Status: {result['status']}")
st.caption(f"Session ID: {result['session_id']}")

# Timeline
st.subheader("Timeline")
for i, item in enumerate(result["log"], start=1):
    with st.expander(f"Step {i}: {list(item.keys())}"):
        st.json(item)

# Approval handling
if result["status"] == "AWAITING_APPROVAL":
    st.warning("Approval required to proceed.")
    st.json(result["final"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve"):
            # For MVP: re-run with execute_actions enabled, keeping same session_id
            result2 = run_agent_loop(goal=goal, scenario=scenario, execute_actions=True, existing_session_id=result["session_id"])
            st.session_state["agent_result"] = result2
            st.rerun()

    with col2:
        if st.button("Reject"):
            st.error("Action rejected. Agent run stopped.")
            # You could also send a rejection message back to Lyzr and continue planning.

# Final output
if result["status"] == "COMPLETED":
    st.success("Agent completed.")
    st.subheader("Final")
    st.json(result["final"])

# Artifacts for other dashboards
st.subheader("Artifacts available to dashboards")
st.write("Keys in state:", list(result["state"].keys()))
