# Docker Deployment Guide — Suraksha Life Insurance (RenewAI)

This project is now fully dockerized and ready for deployment.

## Prerequisites
- Docker
- Docker Compose

## Quick Start
1.  **Configure Environment**: Ensure you have a `.env` file in the root with your API keys (e.g., `GEMINI_API_KEY`).
2.  **Start Services**:
    ```bash
    docker compose up --build -d
    ```
3.  **Access the Applications**:
    - **Production UI**: http://localhost (Port 80)
    - **Backend UI / API Docs**: http://localhost:8000 (Port 8000)

## Architecture
- **Backend**: Python 3.10 / FastAPI container serving business logic and agent orchestration.
- **Frontend**: Multi-stage build (Node 18 -> Nginx) serving production-optimized React assets.
- **Reverse Proxy**: Nginx handles internal routing of `/api` and `/ws` to the backend.
- **Persistence**: `renewai.db` is bind-mounted for local data persistence.

## Maintenance
- **Stop**: `docker compose down`
- **Logs**: `docker compose logs -f`
- **Update**: `docker compose up --build -d` (triggers a fresh build of both containers)
