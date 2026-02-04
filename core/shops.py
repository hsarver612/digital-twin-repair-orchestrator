import numpy as np
import pandas as pd
from .config import SHOP_SPECIALTIES

def generate_shops(seed=42):
    rng = np.random.default_rng(seed)
    n = 12
    shops = pd.DataFrame({
        "shop_id": [f"SHP-{i:03d}" for i in range(1, n + 1)],
        "region": rng.choice(["city", "inner_suburb", "outer_suburb"], n, p=[0.4, 0.35, 0.25]),
        "specialty": rng.choice(SHOP_SPECIALTIES, n, p=[0.55, 0.15, 0.20, 0.10]),
        "weekly_capacity": rng.integers(35, 90, n),
        "backlog": rng.integers(0, 35, n),
    })
    shops["available"] = (shops["weekly_capacity"] - shops["backlog"]).clip(lower=0)
    return shops

def allocate_repairs(claims_df: pd.DataFrame, shops_df: pd.DataFrame):
    repairs = claims_df.loc[~claims_df["total_loss"]].copy()
    if repairs.empty:
        return repairs, shops_df

    repairs["work_units"] = (repairs["severity"] / 10).clip(1, 10).round(1)
    shops = shops_df.copy()
    assignments = []

    for _, r in repairs.sort_values("work_units", ascending=False).iterrows():
        region = r["zip_cluster"]
        needs_adas = int(r["adas"]) == 1 and float(r["severity"]) > 50

        candidates = shops.copy()
        if region in candidates["region"].unique():
            candidates = candidates[candidates["region"] == region]

        if needs_adas:
            candidates = candidates[candidates["specialty"].isin(["adas_calibration", "general"])]

        candidates = candidates.sort_values("available", ascending=False)

        if len(candidates) == 0 or float(candidates.iloc[0]["available"]) <= 0:
            shop_id = "UNASSIGNED"
        else:
            shop_id = candidates.iloc[0]["shop_id"]
            idx = shops.index[shops["shop_id"] == shop_id][0]
            shops.loc[idx, "available"] = max(0.0, float(shops.loc[idx, "available"]) - float(r["work_units"]))

        assignments.append(shop_id)

    repairs["assigned_shop"] = assignments
    return repairs, shops
