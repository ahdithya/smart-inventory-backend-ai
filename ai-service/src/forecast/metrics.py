"""Kalkulasi metrik evaluasi peramalan: MAE, RMSE, MAPE, WAPE."""

import math
from typing import List, Dict


def calculate_mae(actual: List[float], predicted: List[float]) -> float:
    """Mean Absolute Error: Rata-rata selisih absolut antara nilai aktual dan prediksi."""
    if len(actual) == 0:
        return 0.0
    errors = [abs(a - p) for a, p in zip(actual, predicted)]
    return round(sum(errors) / len(errors), 2)


def calculate_rmse(actual: List[float], predicted: List[float]) -> float:
    """Root Mean Squared Error: Akar kuadrat dari rata-rata kuadrat selisih."""
    if len(actual) == 0:
        return 0.0
    sq_errors = [(a - p) ** 2 for a, p in zip(actual, predicted)]
    return round(math.sqrt(sum(sq_errors) / len(sq_errors)), 2)


def calculate_mape(actual: List[float], predicted: List[float]) -> float:
    """
    Mean Absolute Percentage Error (dalam persen, 0-100%).
    Menggunakan penyebut max(a, 1.0) untuk mencegah division by zero ketika actual = 0.
    """
    if len(actual) == 0:
        return 0.0
    pct_errors = [abs(a - p) / max(float(a), 1.0) for a, p in zip(actual, predicted)]
    mape = (sum(pct_errors) / len(pct_errors)) * 100.0
    return round(mape, 2)


def calculate_wape(actual: List[float], predicted: List[float]) -> float:
    """
    Weighted Absolute Percentage Error (dalam persen, 0-100%).
    WAPE = (sum |actual - predicted| / sum actual) * 100%.
    """
    if len(actual) == 0:
        return 0.0
    total_actual = float(sum(actual))
    total_abs_error = sum(abs(a - p) for a, p in zip(actual, predicted))
    if total_actual <= 0:
        # Jika seluruh data aktual 0, gunakan fallback rata-rata error
        return round(min(total_abs_error * 100.0, 100.0), 2)
    return round((total_abs_error / total_actual) * 100.0, 2)


def evaluate_forecast(actual, predicted) -> Dict[str, float]:
    """Menghitung kumpulan metrik evaluasi lengkap."""
    act_list = [float(x) for x in actual]
    pred_list = [float(x) for x in predicted]
    return {
        "mae": calculate_mae(act_list, pred_list),
        "rmse": calculate_rmse(act_list, pred_list),
        "mape": calculate_mape(act_list, pred_list),
        "wape": calculate_wape(act_list, pred_list),
    }
