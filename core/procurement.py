import json
from datetime import datetime

def create_purchase_order(parts_summary_df, min_threshold=20):
    to_order = parts_summary_df[parts_summary_df["qty"] >= min_threshold].copy()

    po = {
        "po_id": f"PO-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "created_utc": datetime.utcnow().isoformat() + "Z",
        "lines": [{"part": r["part"], "qty": int(r["qty"])} for _, r in to_order.iterrows()],
        "status": "CREATED"
    }
    return po

def mock_submit_po(po: dict):
    po2 = dict(po)
    po2["status"] = "CONFIRMED"
    po2["confirmation"] = {"eta_days": 3, "fill_rate": 0.92}
    return po2

def po_to_json(po: dict):
    return json.dumps(po, indent=2)
