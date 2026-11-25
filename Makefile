.PHONY: setup train test dev-api dev-web build up lint
setup:
	pip install -r backend/requirements-dev.txt && cd frontend && npm install
train:
	cd ml && python -m crop_recommendation.train && python -m yield_prediction.train
test:
	cd backend && python -m pytest -q && cd ../frontend && npm test --silent
dev-api:
	cd backend && uvicorn app.main:app --reload
dev-web:
	cd frontend && npm run dev
build:
	cd frontend && npm run build
up:
	docker compose up --build
lint:
	cd backend && ruff check app tests
