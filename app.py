import streamlit as st
import plotly.express as px

from core.config import HORIZONS, WEATHER_LEVELS, DEFAULT_FLEET_SIZE
from core.data_gen import generate_fleet
from core.forecast import forecast_claims
from core.parts import parts_forecast
from core.shops import generate_shops, allocate_repairs
from core.procurement import create_purchase_order, mock_submit_po, po_to_json

st.set_page_config(page_title="Digital Twin Repair Orchestrator", layout="wide")
st.title("🚗 Digital Twin Repair Orchestrator (MVP)")

with st.sidebar:
    st.header("Scenario controls")
    fleet_size = st.slider("Fleet size", 500, 10000, DEFAULT_FLEET_SIZE, step=500)
    horizon = st.selectbox("Forecast horizon (days)", HORIZONS, index=2)
    weather = st.selectbox("Weather scenario", WEATHER_LEVELS, index=0)
    min_po_threshold = st.slider("Procure parts when qty ≥", 5, 100, 20, step=5)
    run = st.button("Run simulation")

if not run:
    st.info("Set scenario controls in the sidebar, then click **Run simulation**.")
    st.stop()

fleet = generate_fleet(n=fleet_size)
claims = forecast_claims(fleet, horizon_days=horizon, weather=weather)

repairs = claims[~claims["total_loss"]]
tls = claims[claims["total_loss"]]

parts_detail, parts_summary = parts_forecast(claims)

shops = generate_shops()
repairs_alloc, shops_after = allocate_repairs(claims, shops)

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Fleet", f"{len(fleet):,}")
c2.metric("Predicted claims", f"{len(claims):,}")
c3.metric("Repairs", f"{len(repairs):,}")
c4.metric("Total losses", f"{len(tls):,}")

left, right = st.columns(2)

with left:
    st.subheader("Claims by damage type")
    if len(claims) > 0:
        fig = px.histogram(claims, x="damage_type", color="total_loss", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No claims predicted for this scenario.")

with right:
    st.subheader("Top parts demand (repairs only)")
    if not parts_summary.empty:
        fig2 = px.bar(parts_summary.head(12), x="part", y="qty")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("No parts demand predicted (no repairs).")

st.subheader("Repair network capacity")
if len(repairs_alloc) > 0:
    assigned = repairs_alloc["assigned_shop"].value_counts().reset_index()
    assigned.columns = ["shop_id", "jobs_assigned"]
    st.dataframe(assigned, use_container_width=True)

    st.caption("Shops availability (before → after)")
    comp = shops.merge(
        shops_after[["shop_id", "available"]],
        on="shop_id",
        suffixes=("_before", "_after")
    )
    st.dataframe(comp.sort_values("available_after"), use_container_width=True)
else:
    st.write("No repairs to allocate.")

st.subheader("Procurement automation (mock)")
if not parts_summary.empty:
    po = create_purchase_order(parts_summary, min_threshold=min_po_threshold)
    st.code(po_to_json(po), language="json")

    if st.button("Submit PO (mock)"):
        confirmed = mock_submit_po(po)
        st.success("PO confirmed (mock).")
        st.code(po_to_json(confirmed), language="json")
else:
    st.write("No parts to procure.")
