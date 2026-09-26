"""Run the BiLSTM and apply the saved decision threshold."""

import numpy as np
import torch
from ml_service.model_loader import get_model, get_config


def predict_windows(windows: np.ndarray) -> dict:
    """
    windows: (n_windows, 256, 23) preprocessed.
    Returns the overall result plus per-window probabilities.
    """
    model = get_model()
    cfg = get_config()
    threshold = cfg["threshold"]

    x = torch.tensor(windows, dtype=torch.float32)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[:, 1]     # P(preictal)

    probs = probs.numpy()

    # Overall verdict = the highest-risk window (a single preictal window
    # in a recording is clinically significant).
    worst_idx = int(np.argmax(probs))
    p_preictal = float(probs[worst_idx])

    is_preictal = p_preictal >= threshold
    predicted_class = cfg["class_names"][1 if is_preictal else 0]
    confidence = p_preictal if is_preictal else 1.0 - p_preictal

    return {
        "predictedClass": predicted_class,
        "status": "Preictal Warning" if is_preictal else "Normal",
        "probability": round(p_preictal, 4),
        "confidence": round(float(confidence), 4),
        "threshold": threshold,
        "windowsAnalysed": len(probs),
        "worstWindowIndex": worst_idx,
        "windowProbabilities": [round(float(p), 4) for p in probs],
    }