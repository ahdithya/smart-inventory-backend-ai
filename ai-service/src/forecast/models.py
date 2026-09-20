"""Model statistik peramalan: Moving Average, Exponential Smoothing, dan Auto Selector."""

from typing import List, Tuple, Dict
from src.forecast.metrics import evaluate_forecast


class MovingAverageModel:
    """Model Moving Average (MA) berbasis window 7 hari terakhir."""

    name = "moving_average"

    def __init__(self, window: int = 7):
        self.window = window

    def fit_predict(self, series: List[float], horizon: int) -> List[float]:
        """Menghasilkan proyeksi horizon hari ke depan berbasis rata-rata bergerak."""
        if not series:
            return [0.0] * horizon

        w = min(len(series), self.window)
        recent_window = series[-w:]
        avg_val = sum(recent_window) / w

        # Proyeksi harian konstan berbasis rata-rata bergerak non-negatif
        pred_val = round(max(0.0, avg_val), 2)
        return [pred_val] * horizon


class ExponentialSmoothingModel:
    """Model Simple Exponential Smoothing (SES) dengan optimasi alpha."""

    name = "exponential_smoothing"

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def _find_best_alpha(self, series: List[float]) -> float:
        """Mencari alpha terbaik (0.1 - 0.7) dengan SSE terendah pada riwayat."""
        if len(series) < 5:
            return self.alpha

        candidate_alphas = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        best_alpha = self.alpha
        lowest_sse = float("inf")

        for a in candidate_alphas:
            sse = 0.0
            smoothed = series[0]
            for t in range(1, len(series)):
                pred = smoothed
                actual = series[t]
                sse += (actual - pred) ** 2
                smoothed = a * actual + (1.0 - a) * smoothed

            if sse < lowest_sse:
                lowest_sse = sse
                best_alpha = a

        return best_alpha

    def fit_predict(self, series: List[float], horizon: int) -> List[float]:
        """Menghasilkan proyeksi horizon hari ke depan berbasis SES."""
        if not series:
            return [0.0] * horizon

        alpha = self._find_best_alpha(series)
        smoothed = series[0]
        for val in series[1:]:
            smoothed = alpha * val + (1.0 - alpha) * smoothed

        pred_val = round(max(0.0, smoothed), 2)
        return [pred_val] * horizon


def run_backtest_evaluation(
    model_name: str,
    series: List[float],
    eval_horizon: int = 7
) -> Tuple[List[float], Dict[str, float]]:
    """
    Melakukan backtesting holdout (eval_horizon hari terakhir sebagai data uji).
    Mengembalikan (prediksi_holdout, metrik_evaluasi).
    """
    if len(series) <= eval_horizon:
        # Jika data sangat mepet, lakukan in-sample evaluation
        train_data = series
        actual_test = series[-eval_horizon:] if len(series) >= eval_horizon else series
    else:
        train_data = series[:-eval_horizon]
        actual_test = series[-eval_horizon:]

    if model_name == "moving_average":
        model = MovingAverageModel(window=7)
    else:
        model = ExponentialSmoothingModel()

    predictions = model.fit_predict(train_data, horizon=len(actual_test))
    metrics = evaluate_forecast(actual_test, predictions)
    return predictions, metrics


def select_best_model(series: List[float], eval_horizon: int = 7) -> str:
    """
    Memilih model terbaik antara Moving Average dan Exponential Smoothing
    berdasarkan nilai WAPE dan MAPE terendah pada periode holdout backtesting.
    """
    _, metrics_ma = run_backtest_evaluation("moving_average", series, eval_horizon)
    _, metrics_es = run_backtest_evaluation("exponential_smoothing", series, eval_horizon)

    # Prioritaskan WAPE / MAPE terendah
    score_ma = metrics_ma["wape"] + metrics_ma["mape"]
    score_es = metrics_es["wape"] + metrics_es["mape"]

    return "exponential_smoothing" if score_es <= score_ma else "moving_average"
