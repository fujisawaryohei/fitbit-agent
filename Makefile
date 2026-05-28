.PHONY: server frontend ngrok

server:
	FRONTEND_URL=$(or $(FRONTEND_URL),http://localhost:3000) uv run uvicorn server:app --reload --port 8000

frontend:
	cd frontend && npm run dev

ngrok:
	ngrok http 3000
