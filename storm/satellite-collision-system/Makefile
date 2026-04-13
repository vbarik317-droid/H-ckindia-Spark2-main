.PHONY: help setup backend frontend run clean

help:
	@echo "Available commands:"
	@echo "  setup     - Install dependencies for both backend and frontend"
	@echo "  backend   - Run backend server"
	@echo "  frontend  - Run frontend server"
	@echo "  run       - Run both backend and frontend"
	@echo "  clean     - Clean up virtual environment and node_modules"

setup:
	@echo "Setting up backend..."
	cd backend && python -m venv venv && \
	source venv/bin/activate && pip install -r requirements.txt
	@echo "Setting up frontend..."
	cd frontend && npm install

backend:
	@echo "Starting backend server..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend:
	@echo "Starting frontend server..."
	cd frontend && npm run dev

run:
	@echo "Starting both servers..."
	@make -j2 backend frontend

clean:
	@echo "Cleaning up..."
	rm -rf backend/venv
	rm -rf frontend/node_modules
	rm -rf frontend/dist