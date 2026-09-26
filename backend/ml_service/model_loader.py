"""Loads the deployment bundle once at application startup."""

from pathlib import Path
import numpy as np
import torch
from app.config import settings
from ml_service.model import BiLSTMModel

# Channel order used during training — CSV columns are reordered to match.
TARGET_CHANNELS = [
    'FP1-F7', 'F7-T7', 'T7-P7', 'P7-O1', 'FP1-F3', 'F3-C3', 'C3-P3',
    'P3-O1', 'FP2-F4', 'F4-C4', 'C4-P4', 'P4-O2', 'FP2-F8', 'F8-T8',
    'T8-P8-0', 'T8-P8-1', 'P8-O2', 'FZ-CZ', 'CZ-PZ', 'P7-T7',
    'T7-FT9', 'FT9-FT10', 'FT10-T8',
]

_bundle = None
_model = None


def load_model():
    """Called once from FastAPI's lifespan startup."""
    global _bundle, _model

    path = Path(__file__).resolve().parent.parent / settings.model_path
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    # weights_only=False is required: the bundle holds numpy mean/std arrays
    _bundle = torch.load(path, map_location="cpu", weights_only=False)

    arch = _bundle["architecture"]
    _model = BiLSTMModel(
        n_channels=arch["n_channels"],
        hidden=arch["hidden"],
        layers=arch["layers"],
        dropout=arch["dropout"],
    )
    _model.load_state_dict(_bundle["state_dict"])
    _model.eval()

    pre = _bundle["preprocessing"]
    print(
        f"Model loaded: {arch['class_name']} | "
        f"{pre['timesteps']} timesteps x {arch['n_channels']} channels | "
        f"threshold {_bundle['threshold']}"
    )
    return _model


def get_model() -> BiLSTMModel:
    if _model is None:
        raise RuntimeError("Model not loaded — check application startup")
    return _model


def get_config() -> dict:
    """Preprocessing constants, threshold and class names from the bundle."""
    if _bundle is None:
        raise RuntimeError("Model not loaded — check application startup")
    pre = _bundle["preprocessing"]
    return {
        "fs": pre["fs"],
        "window_size": pre["window_size"],            # 1024
        "downsample_factor": pre["downsample_factor"],  # 4
        "timesteps": pre["timesteps"],                # 256
        "mean": np.asarray(pre["mean"], dtype=np.float32),
        "std": np.asarray(pre["std"], dtype=np.float32),
        "threshold": float(_bundle["threshold"]),     # 0.70
        "class_names": _bundle["class_names"],
        "test_metrics": _bundle.get("test_metrics", {}),
        "architecture": _bundle["architecture"],
    }