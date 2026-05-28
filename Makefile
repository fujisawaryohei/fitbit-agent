.PHONY: server frontend ngrok

server:
	uv run uvicorn server:app --reload --port 8000

frontend:
	cd frontend && npm run dev

ngrok:
	ngrok http 3000
