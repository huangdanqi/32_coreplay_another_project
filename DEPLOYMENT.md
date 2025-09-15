## CorePlay Agent - Cloud Deployment (Docker)

This guide deploys the backend API and Vue3 test frontend on a public server using Docker Compose and nginx.

### 1) Prerequisites
- A cloud VM (Linux x86_64) with public IP or domain
- Docker Engine + Docker Compose v2

### 2) Files Overview
- `deploy/docker-compose.yml`: defines backend + frontend services
- `deploy/backend.Dockerfile`: builds Flask backend container
- `deploy/frontend.Dockerfile`: builds Vue static site and serves via nginx
- `deploy/nginx.default.conf`: nginx config (routes `/api` to backend)
- `test_frontend/vite.config.js`: uses `VITE_API_BASE_URL` for dev proxy
- `test_frontend/src/services/apiService.js`: uses `VITE_API_BASE_URL` at runtime

### 3) Configure IP/Domain
Create a `.env` (next to `deploy/docker-compose.yml`) with your public host and ports:

```
PUBLIC_HOST=your.public.ip.or.domain
FRONTEND_HTTP_PORT=80
BACKEND_HTTP_PORT=5003
```

Notes:
- Frontend image is built with `VITE_API_BASE_URL=http://$PUBLIC_HOST:$BACKEND_HTTP_PORT/api` so the SPA calls the backend directly.
- nginx serves the SPA on port `$FRONTEND_HTTP_PORT` and proxies `/api` internally to the backend.

### 4) Build and Run

From the project root:

```
cd deploy
docker compose --env-file .env build
docker compose --env-file .env up -d
```

Check:
- Frontend: `http://PUBLIC_HOST:FRONTEND_HTTP_PORT`
- Backend health: `http://PUBLIC_HOST:BACKEND_HTTP_PORT/api/health`

### 5) Updating the IP/Domain
- Edit `deploy/.env` and change `PUBLIC_HOST` (and ports if needed)
- Rebuild frontend to bake new API base: `docker compose --env-file .env build frontend && docker compose --env-file .env up -d frontend`

### 6) Development vs Production
- Dev (local): Vite dev server proxies `/api` to `VITE_API_BASE_URL` or `http://localhost:5003`
- Prod (cloud): Built SPA uses the baked `VITE_API_BASE_URL` from build-arg

### 7) Where prompts are saved
- Diary prompt: `diary_agent/config/prompt_configuration.json`
- Sensor prompt: `sensor_event_agent/config/prompt.json`
- BaZi prompt: `bazi_wuxing_agent/prompt.json`

### 8) Troubleshooting
- If Chinese logs cause Unicode errors, containers set UTF-8 via `PYTHONIOENCODING` and `LANG`.
- If 401 on save: default password is `GOODluck!328` unless changed in `auth_config.json` (created at runtime).
- If `/api` calls fail in production, verify:
  - `PUBLIC_HOST` is reachable
  - Backend is up: `docker logs coreplay-backend`
  - Frontend env baked: open browser console and check `VITE_API_BASE_URL`


