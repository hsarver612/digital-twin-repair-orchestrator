import numpy as np
import pandas as pd
from faker import Faker
from .config import REGION_CLUSTERS

fake = Faker()

MAKES = ["Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Hyundai", "Kia", "Nissan", "Tesla"]
MODEL_CLASSES = ["Sedan", "SUV", "Truck", "Crossover", "Compact"]

def generate_fleet(n=3000, seed=42):
    rng = np.random.default_rng(seed)

    df = pd.DataFrame({
        "vehicle_id": [fake.unique.bothify(text="VHC-#####") for _ in range(n)],
        "make": rng.choice(MAKES, n),
        "model_class": rng.choice(MODEL_CLASSES, n),
        "model_year": rng.integers(2008, 2026, n),
        "mileage": rng.integers(5_000, 180_000, n),
        "zip_cluster": rng.choice(REGION_CLUSTERS, n, p=[0.35, 0.30, 0.20, 0.15]),
        "adas": rng.choice([0, 1], n, p=[0.55, 0.45]),
        "prior_claims": rng.poisson(0.6, n)
    })

    # risk_score 0-1 (simple proxy)
    age = (2026 - df["model_year"]).clip(lower=0)
    df["risk_score"] = (
        0.12
        + 0.012 * age
        + 0.000002 * df["mileage"]
        + 0.06 * df["prior_claims"]
        + 0.05 * (df["zip_cluster"] == "city").astype(int)
        + 0.02 * (df["zip_cluster"] == "inner_suburb").astype(int)
    ).clip(0, 1)

    return df
