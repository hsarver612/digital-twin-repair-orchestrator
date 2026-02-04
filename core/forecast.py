import numpy as np
import pandas as pd
from .config import WEATHER_LEVELS

DAMAGE_TYPES = ["front", "rear", "side", "glass"]

def forecast_claims(fleet_df: pd.DataFrame, horizon_days: int, weather="normal", seed=42):
    if weather not in WEATHER_LEVELS:
        weather = "normal"

    rng = np.random.default_rng(seed)

    weather_mult = {"normal": 1.0, "rain": 1.15, "snow": 1.35, "hail": 1.25}[weather]

    # claim probability within horizon (tuned for demo)
    base = 0.004 * (horizon_days / 7)
    p_claim = (base * weather_mult) * (0.6 + 1.2 * fleet_df["risk_score"].values)
    p_claim = np.clip(p_claim, 0, 0.25)

    has_claim = rng.random(len(fleet_df)) < p_claim
    claims = fleet_df.loc[has_claim, [
        "vehicle_id", "make", "model_class", "model_year", "mileage",
        "adas", "zip_cluster", "risk_score"
    ]].copy()

    if claims.empty:
        claims["severity"] = []
        claims["damage_type"] = []
        claims["total_loss"] = []
        return claims

    sev = (rng.normal(45, 18, len(claims)) + 35 * claims["risk_score"].values).clip(5, 100)
    claims["severity"] = sev
    claims["damage_type"] = rng.choice(DAMAGE_TYPES, len(claims), p=[0.35, 0.28, 0.25, 0.12])

    age = (2026 - claims["model_year"]).clip(lower=0)
    tl_score = (claims["severity"] / 100) * 0.7 + (age / 20) * 0.2 + (claims["mileage"] / 200_000) * 0.1
    tl_prob = np.clip(tl_score - 0.45, 0, 0.9)
    claims["total_loss"] = rng.random(len(claims)) < tl_prob

    return claims
