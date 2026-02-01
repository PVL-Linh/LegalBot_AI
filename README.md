# LegalBot AI Backend - Hướng Dẫn Chạy

## Cách Chạy Server Chính Thức

### Bước 1: Đảm bảo đã activate venv
```bash
cd e:\LegalBot_AI
venv\Scripts\activate
```

### Bước 2: Chạy từ thư mục backend
```bash
cd backend
uvicorn app.main:app --reload
```

**HOẶC** chạy từ root project:
```bash
cd e:\LegalBot_AI
uvicorn backend.app.main:app --reload
```

## Server URL
```
http://127.0.0.1:8000
```

## Các Endpoint Quan Trọng
- **Health Check**: http://127.0.0.1:8000/health
- **API Docs (Swagger)**: http://127.0.0.1:8000/docs
- **API Docs (ReDoc)**: http://127.0.0.1:8000/redoc

## Lỗi Thường Gặp

### 🔴 "Port already in use" hoặc CancelledError
**Nguyên nhân**: Port 8000 đã bị chiếm

**Giải pháp 1**: Tắt tất cả server đang chạy (Ctrl+C)

**Giải pháp 2**: Chạy trên port khác
```bash
uvicorn app.main:app --reload --port 8001
```

**Giải pháp 3**: Kill process trên port 8000 (Windows)
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_number> /F
```

### 🔴 "ModuleNotFoundError: No module named 'app'"
**Nguyên nhân**: Chạy file Python trực tiếp thay vì qua uvicorn

**Giải pháp**: KHÔNG chạy `python app/main.py`. Phải dùng uvicorn.

### 🔴 "Database not configured"
**Nguyên nhân**: Chưa setup database schema

**Giải pháp**: Xem file `DATABASE_SETUP.md`

## Script Nhanh (Recommended)

Tạo file `run.bat` trong thư mục `backend`:
```batch
@echo off
cd /d %~dp0
..\\venv\\Scripts\\uvicorn app.main:app --reload
```

Rồi chỉ cần:
```bash
cd backend
.\\run.bat
```

## Kiểm Tra Sau Khi Chạy

1. **Health Check**:
```bash
curl http://localhost:8000/health
```

2. **Test API** (cần API Key):
```bash
curl -X POST http://localhost:8000/api/v1/chat ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: 123456" ^
  -d "{\"message\": \"hello\"}"
```

## Development Tips

### Hot Reload
Server tự động reload khi code thay đổi (do flag `--reload`)

### Debug Mode
Đã bật trong `.env`: `DEBUG=True`

### Logs
Uvicorn hiển thị logs realtime trong terminal

## Production (Sau Này)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Hoặc dùng Gunicorn:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```
