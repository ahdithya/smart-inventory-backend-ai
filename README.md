# Backend — Django + FastAPI

Backend & AI service Smart Inventory & Demand Prediction. Dibangun dengan **Django 5.2 + DRF** (API utama) + **FastAPI** (forecasting) + PostgreSQL.

## Struktur

```
backend-ai/
├── docker-compose.yml    # PostgreSQL (database)
├── backend/              # Django 5.2 + DRF (API utama)
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/           # settings, urls, wsgi/asgi
│   └── apps/             # aplikasi Django (products, accounts, sales, ...)
└── ai-service/           # FastAPI (stateless) — forecasting & restock
    ├── requirements.txt
    ├── .env.example
    └── src/
```

## Setup

Jalankan database PostgreSQL:

```bash
docker compose up -d
```

### Backend (Django — port 8000)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### AI Service (FastAPI — port 8001)

```bash
cd ai-service
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # Windows (Linux/macOS: cp .env.example .env)
uvicorn src.main:app --reload --port 8001
```

## Service

| Service    | Teknologi        | Port | Tanggung Jawab                           |
| ---------- | ---------------- | ---- | ---------------------------------------- |
| backend    | Django 5.2 + DRF | 8000 | REST API, auth, logika bisnis, stok      |
| ai-service | FastAPI          | 8001 | Demand forecasting & rekomendasi restock |
| database   | PostgreSQL 16    | 5432 | Penyimpanan data                         |

## Konvensi

- Semua respons memakai envelope `{status, message, data}` (lihat `docs/ARCHITECTURE.md` §2.3).
- `ai-service` stateless — dipanggil hanya oleh backend via header `X-API-Key`.
- Base URL API: `http://localhost:8000/api/`.
- Health check AI: `GET http://localhost:8001/health` (header `X-API-Key`).
- `AI_SERVICE_API_KEY` harus sama antara backend dan ai-service.
