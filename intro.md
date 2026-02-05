## 后端启动
```bash
export FLASK_PORT=5000 && uv run --with flask --with flask-cors frontend/api_server.py
```

## 前端启动
```bash
python3 -m http.server 8080 --directory frontend
```