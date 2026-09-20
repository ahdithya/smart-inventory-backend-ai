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
from src.forecast.pretrained import PretrainedDemandForecaster
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

    # Pemilihan model:
    # 1. auto/pretrained/champion -> prioritaskan champion pretrained model jika tersedia
    # 2. moving_average / exponential_smoothing -> model baseline spesifik
    # 3. fallback -> baseline statistik via select_best_model
    if request.model in ("auto", "pretrained", "champion") and PretrainedDemandForecaster.is_available():
        model_instance = PretrainedDemandForecaster()
        chosen_model_name = model_instance.name
        is_pretrained = True
    elif request.model == "moving_average":
        model_instance = MovingAverageModel(window=7)
        chosen_model_name = "moving_average"
        is_pretrained = False
    elif request.model == "exponential_smoothing":
        model_instance = ExponentialSmoothingModel()
        chosen_model_name = "exponential_smoothing"
        is_pretrained = False
    else:
        chosen_model_name = select_best_model(series, eval_horizon=7)
        if chosen_model_name == "moving_average":
            model_instance = MovingAverageModel(window=7)
        else:
            model_instance = ExponentialSmoothingModel()
        is_pretrained = False

    horizon_results: List[HorizonResult] = []

    # Urutkan horizon (misal 7, 14)
    horizons = sorted(request.horizon_days)

    for h in horizons:
        eval_horizon = min(h, len(series) // 2)

        if is_pretrained:
            predictions = model_instance.fit_predict(series, horizon=h, last_date=last_date)
            _, metrics_dict = model_instance.backtest_evaluate(
                series, last_date=last_date, eval_horizon=eval_horizon
            )
        else:
            predictions = model_instance.fit_predict(series, horizon=h)
            _, metrics_dict = run_backtest_evaluation(
                chosen_model_name, series, eval_horizon=eval_horizon
            )

        daily_list: List[DailyForecast] = []
        for i, qty in enumerate(predictions):
            future_date = last_date + timedelta(days=i + 1)
            daily_list.append(DailyForecast(date=future_date.isoformat(), qty=qty))

        total_predicted = round(sum(d.qty for d in daily_list), 2)

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
