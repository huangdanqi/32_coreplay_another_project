## CorePlay Agent - Cloud Deployment (No Docker)

This guide deploys the Flask backend and Vue3 frontend on a Linux server with nginx and systemd.

### 1) Prerequisites (on the cloud server)
- Ubuntu 20.04+/Debian 11+/CentOS 8+
- Python 3.11 (or 3.10)
- Node.js 18+ and npm
- nginx

### 2) Copy project to server
Place project at `/opt/coreplay_agent` (recommended):
```
sudo mkdir -p /opt/coreplay_agent
sudo chown -R $USER:$USER /opt/coreplay_agent
rsync -avz --exclude .venv/ ./ /opt/coreplay_agent/
```

### 3) Backend setup (Flask)
```
cd /opt/coreplay_agent
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Test run:
```
python simple_diary_api.py --host 0.0.0.0 --port 5003
```

### 4) systemd service
Create service file `/etc/systemd/system/coreplay-backend.service`:
```
[Unit]
Description=CorePlay Backend (Flask)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/coreplay_agent
ExecStart=/opt/coreplay_agent/.venv/bin/python simple_diary_api.py --host 0.0.0.0 --port 5003
Restart=always
RestartSec=3
Environment=PYTHONIOENCODING=utf-8
Environment=LANG=C.UTF-8
Environment=LC_ALL=C.UTF-8

[Install]
WantedBy=multi-user.target
```

Enable and start:
```
sudo systemctl daemon-reload
sudo systemctl enable coreplay-backend
sudo systemctl start coreplay-backend
sudo systemctl status coreplay-backend
```

Health check:
```
curl http://127.0.0.1:5003/api/health
```

### 5) Frontend build (Vue)
Set public API URL (replace with your public IP/domain):
```
cd /opt/coreplay_agent/test_frontend
cp .env.production.example .env.production
echo VITE_API_BASE_URL=http://YOUR_PUBLIC_HOST:5003 >> .env.production
npm ci || npm install
npm run build
```
This generates `test_frontend/dist/`.

### 6) nginx config
Create `/etc/nginx/sites-available/coreplay.conf`:
```
server {
    listen 80;
    server_name _;

    root /opt/coreplay_agent/test_frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5003/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and reload nginx:
```
sudo ln -sf /etc/nginx/sites-available/coreplay.conf /etc/nginx/sites-enabled/coreplay.conf
sudo nginx -t && sudo systemctl reload nginx
```

Visit: `http://YOUR_PUBLIC_HOST` (SPA) and `http://YOUR_PUBLIC_HOST:5003/api/health` (backend)

### 7) Updating IP/host later
- Edit `test_frontend/.env.production` to the new `VITE_API_BASE_URL`
- Rebuild: `npm run build`
- Reload nginx: `sudo systemctl reload nginx`

### 8) Where prompts are saved
- Diary: `/opt/coreplay_agent/diary_agent/config/prompt_configuration.json`
- Sensor: `/opt/coreplay_agent/sensor_event_agent/config/prompt.json`
- BaZi: `/opt/coreplay_agent/bazi_wuxing_agent/prompt.json`

### 9) Logs
Backend journal:
```
sudo journalctl -u coreplay-backend -f
```
Backend app log (if enabled): `simple_diary_api.log` in project root.


