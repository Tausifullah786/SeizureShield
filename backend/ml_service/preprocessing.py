"""EEG preprocessing — must mirror the training notebook exactly."""

import numpy as np
from ml_service.model_loader import get_config, TARGET_CHANNELS


def validate_and_order_columns(df):
    """
    Check the CSV has exactly the 23 training channels, then reorder the
    columns into training order. Wrong order would silently ruin predictions.
    """
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in TARGET_CHANNELS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required channels: {missing}")

    extra = [c for c in df.columns if c not in TARGET_CHANNELS]
    if extra:
        raise ValueError(f"CSV has unexpected columns: {extra}")

    return df[TARGET_CHANNELS]      # reorder to training order


def slice_windows(data: np.ndarray) -> np.ndarray:
    """
    (n_rows, 23) -> (n_windows, 1024, 23), non-overlapping.
    Rows that don't fill a complete window are dropped.
    """
    cfg = get_config()
    size = cfg["window_size"]                 # 1024

    n_windows = len(data) // size
    if n_windows == 0:
        raise ValueError(
            f"CSV has {len(data)} rows — at least {size} are required for one window"
        )

    usable = data[: n_windows * size]
    return usable.reshape(n_windows, size, data.shape[1])


def downsample(X: np.ndarray) -> np.ndarray:
    """(n, 1024, 23) -> (n, 256, 23). Same reshape-and-mean as training."""
    factor = get_config()["downsample_factor"]     # 4
    n, t, c = X.shape
    return X.reshape(n, t // factor, factor, c).mean(axis=2)


def normalize(X: np.ndarray) -> np.ndarray:
    """Per-channel z-score using the mean/std saved from the training set."""
    cfg = get_config()
    return (X - cfg["mean"]) / cfg["std"]


def preprocess_dataframe(df) -> np.ndarray:
    """Full pipeline: CSV DataFrame -> (n_windows, 256, 23) float32."""
    df = validate_and_order_columns(df)

    if df.isnull().values.any():
        raise ValueError("CSV contains empty or non-numeric values")

    data = df.to_numpy(dtype=np.float32)
    windows = slice_windows(data)
    windows = downsample(windows)
    windows = normalize(windows)
    return windows.astype(np.float32)