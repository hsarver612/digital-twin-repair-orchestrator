import numpy as np
import pandas as pd
from .config import PARTS_CATALOG

def parts_forecast(claims_df: pd.DataFrame, seed=42):
    rng = np.random.default_rng(seed)

    if claims_df.empty:
        empty = pd.DataFrame(columns=["vehicle_id", "damage_type", "part", "qty"])
        summary = pd.DataFrame(columns=["part", "qty"])
        return empty, summary

    rows = []
    for _, c in claims_df.iterrows():
        if bool(c.get("total_loss", False)):
            continue

        damage = c["damage_type"]
        candidates = PARTS_CATALOG.get(damage, [])
        if not candidates:
            continue

        k = int(np.clip(np.round(float(c["severity"]) / 25), 1, min(5, len(candidates))))
        chosen = rng.choice(candidates, size=k, replace=False)

        for part in chosen:
            rows.append({
                "vehicle_id": c["vehicle_id"],
                "damage_type": damage,
                "part": part,
                "qty": 1
            })

    parts_df = pd.DataFrame(rows, columns=["vehicle_id", "damage_type", "part", "qty"])
    if parts_df.empty:
        summary = pd.DataFrame(columns=["part", "qty"])
    else:
        summary = parts_df.groupby("part", as_index=False)["qty"].sum().sort_values("qty", ascending=False)

    return parts_df, summary
