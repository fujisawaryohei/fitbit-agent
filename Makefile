.PHONY: server ngrok

server:
	uv run uvicorn server:app --reload --port 8000

ngrok:
	ngrok http 8000
