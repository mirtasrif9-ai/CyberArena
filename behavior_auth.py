import os
import json
import numpy as np

MODEL_DIR = "behavior_models"
os.makedirs(MODEL_DIR, exist_ok=True)


def build_feature_vector(sample: dict):
    hold_times = np.array(sample.get("hold_times", []), dtype=float)
    flight_times = np.array(sample.get("flight_times", []), dtype=float)
    total_time = float(sample.get("total_time", 0))
    backspace_count = int(sample.get("backspace_count", 0))
    key_count = int(sample.get("key_count", 0))

    hold_mean = hold_times.mean() if len(hold_times) > 0 else 0
    hold_std = hold_times.std() if len(hold_times) > 0 else 0
    flight_mean = flight_times.mean() if len(flight_times) > 0 else 0
    flight_std = flight_times.std() if len(flight_times) > 0 else 0

    return np.array([
        hold_mean,
        hold_std,
        flight_mean,
        flight_std,
        total_time,
        backspace_count,
        key_count
    ], dtype=float)


def train_admin_model(username: str, samples: list):
    if len(samples) < 5:
        raise ValueError("At least 5 typing samples are required for training.")

    X = np.array([build_feature_vector(sample) for sample in samples])

    profile_mean = X.mean(axis=0)
    profile_std = X.std(axis=0)

    # avoid division by zero
    profile_std = np.where(profile_std == 0, 1, profile_std)

    model_data = {
        "mean": profile_mean.tolist(),
        "std": profile_std.tolist(),
        "threshold": 12.0
    }

    model_path = os.path.join(MODEL_DIR, f"{username}.json")
    with open(model_path, "w") as f:
        json.dump(model_data, f)

    return model_path


def load_admin_model(username: str):
    model_path = os.path.join(MODEL_DIR, f"{username}.json")
    if not os.path.exists(model_path):
        return None

    with open(model_path, "r") as f:
        return json.load(f)


def verify_admin_behavior(username: str, sample: dict):
    model = load_admin_model(username)
    if model is None:
        return False, "Model not found"

    x = build_feature_vector(sample)
    mean = np.array(model["mean"], dtype=float)
    std = np.array(model["std"], dtype=float)
    threshold = float(model["threshold"])

    z = np.abs((x - mean) / std)
    distance = z.sum()

    if distance <= threshold:
        return True, f"Behavior matched (distance={distance:.2f})"
    return False, f"Behavior mismatch (distance={distance:.2f})"


def admin_model_exists(username: str):
    model_path = os.path.join(MODEL_DIR, f"{username}.json")
    return os.path.exists(model_path)