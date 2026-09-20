"""Service logika bisnis orkestrasi peramalan permintaan (forecasting service)."""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List

from src.forecast.models import (
    ExponentialSmoothingModel,
    MovingAverageModel,
    run_backtest_evaluation,
    select_best_model,
)
from src.forecast.schemas import (
    DailyForecast,
    ForecastData,
    ForecastRequest,
    HorizonResult,
    MetricsResult,
)


class InsufficientDataError(Exception):
    """Exception dilempar jika riwayat penjualan kurang dari 30 hari."""

    def __init__(
        self,
        message: str = "Riwayat penjualan kurang dari 30 hari",
        code: str = "INSUFFICIENT_DATA",
        status_code: int = 400,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def _parse_date(date_val) -> date:
    """Konversi string atau date object ke datetime.date."""
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        return datetime.strptime(date_val[:10], "%Y-%m-%d").date()
    raise ValueError(f"Format tanggal tidak valid: {date_val}")


def generate_demand_forecast(request: ForecastRequest) -> ForecastData:
    """
    Validasi data dan jalankan peramalan permintaan untuk produk.
    Memeriksa ambang batas minimal 30 hari riwayat penjualan (BR-11).
    """
    if not request.sales_history:
        raise InsufficientDataError("Riwayat penjualan kurang dari 30 hari")

    # Agregasi data jika terdapat tanggal yang sama dan urutkan
    aggregated_sales: Dict[date, float] = defaultdict(float)
    for item in request.sales_history:
        d = _parse_date(item.date)
        aggregated_sales[d] += float(item.qty)

    sorted_dates = sorted(aggregated_sales.keys())

    # Validasi jumlah hari unik >= 30 (sesuai spesifikasi BR-11)
    if len(sorted_dates) < 30:
        raise InsufficientDataError("Riwayat penjualan kurang dari 30 hari")

    series: List[float] = [aggregated_sales[d] for d in sorted_dates]
    last_date = sorted_dates[-1]

    # Pemilihan model
    if request.model == "auto":
        chosen_model_name = select_best_model(series, eval_horizon=7)
    else:
        chosen_model_name = request.model

    # Inisialisasi model terpilih
    if chosen_model_name == "moving_average":
        model_instance = MovingAverageModel(window=7)
    else:
        model_instance = ExponentialSmoothingModel()

    horizon_results: List[HorizonResult] = []

    # Urutkan horizon (misal 7, 14)
    horizons = sorted(request.horizon_days)

    for h in horizons:
        # Hitung prediksi harian masa depan
        predictions = model_instance.fit_predict(series, horizon=h)

        daily_list: List[DailyForecast] = []
        for i, qty in enumerate(predictions):
            future_date = last_date + timedelta(days=i + 1)
            daily_list.append(DailyForecast(date=future_date.isoformat(), qty=qty))

        total_predicted = round(sum(d.qty for d in daily_list), 2)

        # Hitung metrik backtest untuk horizon ini (menggunakan holdout)
        eval_horizon = min(h, len(series) // 2)
        _, metrics_dict = run_backtest_evaluation(chosen_model_name, series, eval_horizon=eval_horizon)

        horizon_results.append(
            HorizonResult(
                horizon_days=h,
                total_predicted=total_predicted,
                daily=daily_list,
                metrics=MetricsResult(**metrics_dict),
            )
        )

    return ForecastData(
        product_id=request.product_id,
        horizons=horizon_results,
        model=chosen_model_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
