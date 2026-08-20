# AI Service — FastAPI

Layanan **stateless** untuk demand forecasting & rekomendasi restock. Dipanggil hanya oleh backend (via `X-API-Key`), tidak pernah langsung oleh frontend.

## Struktur

```
ai-service/
├── requirements.txt
├── .env.example
└── src/
    ├── main.py          # aplikasi FastAPI + router
    ├── config.py        # pydantic-settings (env)
    ├── envelope.py      # helper envelope respons (sukses/error)
    ├── forecast/        # logika model (MA, ES) + evaluasi metrik
    └── shared/          # util bersama (mis. validasi input)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

Buat file `.env` dari `.env.example`, lalu jalankan:

```bash
uvicorn src.main:app --reload --port 8001
```

Cek kesehatan: `GET http://localhost:8001/health` (header `X-API-Key`).

## Kontrak API

### `POST /forecast`

Request:

```json
{
  "product_id": 1,
  "sales_history": [{"date": "2026-05-01", "qty": 5}],
  "horizon_days": [7, 14]
}
```

Response (envelope):

```json
{
  "product_id": 1,
  "horizons": [
    {"horizon_days": 7, "total_predicted": 42, "daily": [{"date": "...", "qty": 6}],
     "metrics": {"mae": 1.2, "rmse": 1.8, "mape": 18.5, "wape": 17.2}}
  ],
  "model": "exponential_smoothing",
  "generated_at": "2026-08-12T10:00:00Z"
}
```

Error:

```json
{"error": {"code": "INSUFFICIENT_DATA", "message": "Riwayat penjualan kurang dari 30 hari"}}
```

## Prinsip

- **Stateless** — tidak menyimpan data; hasil dikembalikan ke backend.
- **Tanpa LLM** — model baseline statistik (Moving Average / Exponential Smoothing); model terlatih tim DS dapat di-drop-in belakangan.
- Setiap endpoint butuh header `X-API-Key` (nilai dari `AI_SERVICE_API_KEY`).
