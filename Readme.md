\# MS 2026 Tipper – Complete Sample App

\## Usage guide

See `docs/APP_USAGE_GUIDE.md` for full setup, real-data loading, and app usage.

\## Run With Docker

docker-compose down -v
docker-compose up --build

\## Run locally (no Docker)

```bash

cd backend

python -m venv .venv

source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

pip install -r requirements.txt

uvicorn app.main:app --reload


cd frontend
npm install
npm run dev



