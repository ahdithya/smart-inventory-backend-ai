"""Adaptor inferensi peramalan permintaan berbasis Champion Pre-trained Model."""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.forecast.features import FEATURE_COLUMNS, build_feature_row_from_series
from src.forecast.loader import get_champion_model, get_model_metadata, is_champion_model_available
from src.forecast.metrics import evaluate_forecast


class PretrainedDemandForecaster:
    """
    Forecaster yang menggunakan model Machine Learning terlatih (Champion Model)
    yang dimuat dari artifacts (.joblib).
    Mendukung peramalan multi-step autoregresif untuk horizon 7 dan 14 hari.
    """

    def __init__(self):
        self.model = get_champion_model()
        meta = get_model_metadata()
        self.name = meta.get("model_name", "champion_model")

    @classmethod
    def is_available(cls) -> bool:
        """Cek apakah model champion siap digunakan."""
        return is_champion_model_available()

    def fit_predict(
        self,
        series: List[float],
        horizon: int,
        last_date: Optional[date] = None,
    ) -> List[float]:
        """
        Menghasilkan proyeksi horizon hari ke depan secara multi-step autoregressive
        menggunakan model terlatih dan ekstraksi fitur lag/kalender dinamis.
        """
        if not self.model or not series:
            return [0.0] * horizon

        if last_date is None:
            last_date = date.today()

        running_series = list(series)
        predictions: List[float] = []

        for step in range(1, horizon + 1):
            target_date = last_date + timedelta(days=step)
            feat_dict = build_feature_row_from_series(running_series, target_date)
            # Pastikan urutan fitur tepat sama dengan yang digunakan saat training
            X_row = pd.DataFrame([[feat_dict[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)

            raw_pred = float(self.model.predict(X_row)[0])
            pred_val = round(max(0.0, raw_pred), 2)
            predictions.append(pred_val)
            running_series.append(pred_val)

        return predictions

    def backtest_evaluate(
        self,
        series: List[float],
        last_date: Optional[date] = None,
        eval_horizon: int = 7,
    ) -> Tuple[List[float], Dict[str, float]]:
        """
        Evaluasi performa model champion pada periode holdout riwayat penjualan produk.
        """
        if len(series) <= eval_horizon:
            train_series = series
            actual_test = series[-eval_horizon:] if len(series) >= eval_horizon else series
        else:
            train_series = series[:-eval_horizon]
            actual_test = series[-eval_horizon:]

        holdout_start_date = (last_date - timedelta(days=eval_horizon)) if last_date else date.today()
        preds = self.fit_predict(train_series, horizon=len(actual_test), last_date=holdout_start_date)
        metrics = evaluate_forecast(actual_test, preds)
        return preds, metrics
