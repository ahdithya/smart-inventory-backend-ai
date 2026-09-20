"""Modul feature engineering untuk time-series demand forecasting."""

from datetime import date, datetime
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "dayofweek",
    "is_weekend",
    "month",
    "day",
    "dayofyear",
    "lag_1",
    "lag_2",
    "lag_7",
    "lag_14",
    "lag_21",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_30",
    "rolling_std_7",
]


def extract_calendar_features(dt: Union[date, datetime, pd.Timestamp]) -> Dict[str, Union[int, float]]:
    """Mengekstrak fitur kalender dari objek tanggal."""
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)
    dayofweek = int(dt.weekday()) if hasattr(dt, "weekday") else int(dt.dayofweek)
    return {
        "dayofweek": dayofweek,
        "is_weekend": 1 if dayofweek in (5, 6) else 0,
        "month": int(dt.month),
        "day": int(dt.day),
        "dayofyear": int(dt.timetuple().tm_yday if hasattr(dt, "timetuple") else dt.dayofyear),
    }


def build_feature_row_from_series(
    historical_series: List[float],
    target_date: Union[date, datetime],
) -> Dict[str, float]:
    """
    Membangun satu baris fitur lengkap untuk memprediksi nilai pada target_date
    berdasarkan deret waktu historis (panjang minimal disarankan >= 30).
    """
    feats = extract_calendar_features(target_date)
    series_len = len(historical_series)

    # Fitur lag (jika data kurang, fallback ke nilai terawal atau 0.0)
    for lag in [1, 2, 7, 14, 21, 28]:
        if series_len >= lag:
            feats[f"lag_{lag}"] = float(historical_series[-lag])
        elif series_len > 0:
            feats[f"lag_{lag}"] = float(historical_series[0])
        else:
            feats[f"lag_{lag}"] = 0.0

    # Fitur rolling window
    for window in [7, 14, 30]:
        w = min(series_len, window)
        if w > 0:
            sub = historical_series[-w:]
            feats[f"rolling_mean_{window}"] = float(np.mean(sub))
        else:
            feats[f"rolling_mean_{window}"] = 0.0

    # Rolling std (window 7)
    w_std = min(series_len, 7)
    if w_std > 1:
        feats["rolling_std_7"] = float(np.std(historical_series[-w_std:], ddof=1))
    else:
        feats["rolling_std_7"] = 0.0

    return feats


def create_features_dataframe(
    df: pd.DataFrame,
    date_col: str = "date",
    target_col: str = "sales",
    group_col: Optional[str] = "item",
) -> pd.DataFrame:
    """
    Membangun dataset fitur lengkap dari DataFrame tabular (misal data Kaggle Store Item).
    Menghasilkan kolom kalender, lag (1..28), dan rolling stats per produk.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values([group_col, date_col] if group_col else [date_col]).reset_index(drop=True)

    # Fitur Kalender
    df["dayofweek"] = df[date_col].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["month"] = df[date_col].dt.month
    df["day"] = df[date_col].dt.day
    df["dayofyear"] = df[date_col].dt.dayofyear

    # Fitur Lag & Rolling per group
    def _add_group_features(group: pd.DataFrame) -> pd.DataFrame:
        g = group.sort_values(date_col).copy()
        for lag in [1, 2, 7, 14, 21, 28]:
            g[f"lag_{lag}"] = g[target_col].shift(lag)

        for w in [7, 14, 30]:
            # Shift 1 hari untuk mencegah data leakage pada rolling stats
            g[f"rolling_mean_{w}"] = g[target_col].shift(1).rolling(window=w, min_periods=1).mean()

        g["rolling_std_7"] = g[target_col].shift(1).rolling(window=7, min_periods=2).std().fillna(0.0)
        return g

    if group_col and group_col in df.columns:
        processed_groups = [_add_group_features(g) for _, g in df.groupby(group_col)]
        df = pd.concat(processed_groups, axis=0)
    else:
        df = _add_group_features(df)

    # Drop baris awal yang memiliki NaN karena lag 28
    df = df.dropna(subset=[f"lag_28"]).reset_index(drop=True)
    return df
