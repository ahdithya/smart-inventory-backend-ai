- **backend** = satu-satunya pintu masuk bagi frontend.
- **ai-service** = stateless; dipanggil hanya oleh backend dengan header `X-API-Key`.

Dokumentasi lengkap: `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/PRD.md`, `docs/SDD.md`.

## Prasyarat

- Python 3.11+
- Docker & Docker Compose
- Git

## Menjalankan Database (PostgreSQL)

```bash
cd backend-ai
docker compose up -d
```
