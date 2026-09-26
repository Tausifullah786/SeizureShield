"""Integrated Gradients explainability for the BiLSTM prediction."""

import numpy as np
import torch
from captum.attr import IntegratedGradients
from ml_service.model_loader import get_model, get_config, TARGET_CHANNELS

N_STEPS = 50          # IG approximation steps — higher is more accurate, slower
TOP_K = 3             # how many channels to highlight
REGION_PERCENTILE = 75  # timesteps above this are "important"


def _find_regions(time_importance: np.ndarray, threshold: float,
                  min_length: int = 5) -> list[dict]:
    """Find contiguous runs of timesteps whose importance exceeds threshold."""
    above = time_importance >= threshold
    regions, start = [], None

    for i, flag in enumerate(above): #Above has two things one is Flag that is True or False and second one is Index 
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            if i - start >= min_length:
                regions.append((start, i - 1))
            start = None
    if start is not None and len(above) - start >= min_length:
        regions.append((start, len(above) - 1))

    # Score each region by its mean importance, strongest first
    scored = [
        {
            "start": int(s),
            "end": int(e),
            "importance": round(float(time_importance[s:e + 1].mean()), 4),
        }
        for s, e in regions
    ]
    scored.sort(key=lambda r: r["importance"], reverse=True)
    return scored[:3] #bcz we only return three important region 


def explain_window(window: np.ndarray, target_class: int) -> dict:
    """
    window: (256, 23) preprocessed, single window.
    target_class: 0 = interictal, 1 = preictal.
    Returns visualization-ready explainability data.
    """
    model = get_model()
    cfg = get_config()
    fs = cfg["fs"]
    factor = cfg["downsample_factor"]

    #Adding a Singlaton Dimension Which odel expact 
    x = torch.tensor(window, dtype=torch.float32).unsqueeze(0)   # (1, 256, 23)
    baseline = torch.zeros_like(x)      #  Create Zero like tensor With same dimension 

    # IG needs gradients, so this must NOT run inside torch.no_grad()
    ig = IntegratedGradients(model)

    attributions, delta = ig.attribute(
        x,
        baselines=baseline,
        target=target_class,
        n_steps=N_STEPS,
        return_convergence_delta=True,
    )

    attr = attributions.squeeze(0).detach().numpy()       # (256, 23)
    abs_attr = np.abs(attr)

    #  channel importance: average over time, normalised to 0-1 
    channel_raw = abs_attr.mean(axis=0)                   # (23,)
    channel_norm = channel_raw / (channel_raw.max() + 1e-12)

    channel_importance = [
        {"channel": TARGET_CHANNELS[i], "importance": round(float(channel_norm[i]), 4)}
        for i in range(len(TARGET_CHANNELS))
    ]

    top_idx = np.argsort(channel_raw)[::-1][:TOP_K]
    top_channels = [TARGET_CHANNELS[i] for i in top_idx]

    #  time importance: sum across channels, normalised 
    time_raw = abs_attr.sum(axis=1)                       # (256,)
    time_norm = time_raw / (time_raw.max() + 1e-12)

    #  important regions, converted to seconds for the doctor-facing text 
    cutoff = float(np.percentile(time_norm, REGION_PERCENTILE))
    regions = _find_regions(time_norm, cutoff)
    seconds_per_step = factor / fs                        # 4/256 = 0.015625 s

    for r in regions:
        r["startSec"] = round(r["start"] * seconds_per_step, 2)
        r["endSec"] = round((r["end"] + 1) * seconds_per_step, 2)

    #  heatmap: 256 -> 64 rows so the UI can render it 
    heatmap = abs_attr.reshape(64, 4, len(TARGET_CHANNELS)).mean(axis=1)
    heatmap = heatmap / (heatmap.max() + 1e-12)

    return {
        "method": "Integrated Gradients",
        "baseline": "zero (mean of training distribution)",
        "convergenceDelta": round(float(delta.abs().item()), 6),
        "channels": TARGET_CHANNELS,
        "channelImportance": channel_importance,
        "topChannels": top_channels,
        "timeImportance": [round(float(v), 4) for v in time_norm],
        "importantTimeRegions": regions,
        "heatmap": np.round(heatmap, 4).tolist(),          # 64 x 23
        "summary": _doctor_summary(top_channels, regions),
    }


def _doctor_summary(top_channels: list[str], regions: list[dict]) -> str:
    """Plain-language explanation shown above the charts."""
    channels_text = ", ".join(top_channels)
    if regions:
        r = regions[0]
        time_text = f"{r['startSec']}s to {r['endSec']}s into the recording window"
    else:
        time_text = "spread evenly across the window"

    return (
        f"The model's decision was influenced most by channels {channels_text}, "
        f"with the strongest contribution from {time_text}."
    )