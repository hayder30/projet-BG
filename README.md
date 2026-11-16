# Brazilian Glow – Stock Management (Phase 1)

A simple web app to manage the stock of cosmetic products.

| Part | Tech | Folder |
|---|---|---|
| Frontend | HTML / CSS / JavaScript, served by nginx | `frontend/` |
| Backend API | Python, FastAPI, SQLAlchemy | `backend/` |
| Database | PostgreSQL (SQLite for quick local runs) | `database/` |

## Features
- Sign in (JWT). Two roles: **admin** (everything) and **staff** (view products, move stock).
- Products: SKU, name, category, supplier, price, cost, stock, low-stock alert level; search and filters.
- Stock movements: add stock, remove stock, set an exact count; every change is logged with user and reason. Stock can never go below zero.
- Dashboard: totals, stock value, products to restock, units per category, recent movements.
- Settings (admin): categories, suppliers, users.

Default login: `admin` / `admin123` (change it in `.env`).
Demo products are sample data only: replace them with the real catalog.

## Run with Docker
```bash
cp .env.example .env
docker compose up --build
```
Frontend: http://localhost:8080 · API docs: http://localhost:8000/docs

## Run without Docker
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # uses SQLite (stock.db)

# in another terminal
cd frontend && python -m http.server 8080
```

## Tests
```bash
cd backend
pytest -v
# or inside Docker:
docker compose run --rm backend pytest -v
```

## API overview
`POST /api/auth/login` · `GET /api/auth/me` · `GET|POST /api/auth/users` (admin)
`GET|POST /api/categories` · `GET|POST /api/suppliers`
`GET|POST /api/products` · `GET|PUT|DELETE /api/products/{id}`
`POST|GET /api/stock/movements` · `GET /api/dashboard` · `GET /api/health`
