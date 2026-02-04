from core.data_gen import generate_fleet
from core.forecast import forecast_claims
from core.parts import parts_forecast
from core.shops import generate_shops, allocate_repairs
from core.procurement import create_purchase_order, mock_submit_po

def run_tool(tool_name: str, args: dict, state: dict):
    """
    Executes a tool locally and updates state.
    State holds: fleet, claims, parts_summary, shops_before, repairs_alloc, shops_after, po, po_confirmed
    """
    if tool_name == "fleet.generate_fleet":
        state["fleet"] = generate_fleet(n=args["fleet_size"], seed=args.get("seed", 42))
        return {"fleet_size": len(state["fleet"])}

    if tool_name == "forecast.forecast_claims":
        state["claims"] = forecast_claims(
            state["fleet"],
            horizon_days=args["horizon_days"],
            weather=args.get("weather", "normal"),
            seed=args.get("seed", 42),
        )
        return {"claims": len(state["claims"]), "repairs": int((~state["claims"]["total_loss"]).sum()), "total_losses": int((state["claims"]["total_loss"]).sum())}

    if tool_name == "parts.parts_forecast":
        _, parts_summary = parts_forecast(state["claims"])
        state["parts_summary"] = parts_summary
        top = parts_summary.head(5).to_dict(orient="records") if len(parts_summary) else []
        return {"distinct_parts": int(len(parts_summary)), "top_parts": top}

    if tool_name == "shops.generate_shops":
        state["shops_before"] = generate_shops(seed=args.get("seed", 42))
        return {"shops": len(state["shops_before"])}

    if tool_name == "shops.allocate_repairs":
        repairs_alloc, shops_after = allocate_repairs(state["claims"], state["shops_before"])
        state["repairs_alloc"] = repairs_alloc
        state["shops_after"] = shops_after
        unassigned = int((repairs_alloc["assigned_shop"] == "UNASSIGNED").sum()) if len(repairs_alloc) else 0
        return {"repairs_allocated": len(repairs_alloc), "unassigned_repairs": unassigned}

    if tool_name == "procurement.create_purchase_order":
        po = create_purchase_order(state["parts_summary"], min_threshold=args.get("min_threshold", 20))
        state["po"] = po
        total_qty = sum(line["qty"] for line in po.get("lines", []))
        return {"po_lines": len(po.get("lines", [])), "total_qty": int(total_qty)}

    if tool_name == "procurement.submit_purchase_order":
        state["po_confirmed"] = mock_submit_po(state["po"])
        return {"status": state["po_confirmed"].get("status", "UNKNOWN")}

    raise ValueError(f"Unknown tool: {tool_name}")
