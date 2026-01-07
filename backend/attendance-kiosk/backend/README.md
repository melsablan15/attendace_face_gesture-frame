# 🔧 FRAMES Attendance Kiosk - Backend

## 📋 Overview

This is a **lightweight, standalone backend** specifically designed for the attendance kiosk. It handles face recognition and attendance recording without the overhead of the full system backend.

---

## ✨ Features

- 🎯 **Lightweight** - Only attendance recording APIs
- 🔐 **Secure** - No admin/user management endpoints exposed
- 📦 **Portable** - Easy to deploy anywhere
- 🚀 **Fast** - Minimal dependencies, quick startup
- 🔌 **Independent** - Works separately from main backend
- 🌐 **Cross-platform** - Windows, Linux, macOS

---

## 🚀 Quick Start

### Option 1: Automatic Setup (Windows)

```bash
cd attendance-kiosk/backend
setup.bat
```

### Option 2: Automatic Setup (Linux/Mac)

```bash
cd attendance-kiosk/backend
chmod +x setup.sh
./setup.sh
```

### Option 3: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# 5. Edit .env with your database credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

---

## ⚙️ Configuration

### 1. Database Setup

Edit `.env` file:

```env
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
DB_PORT=3306

# Optional: For cloud databases with SSL
# DB_SSL_CA=path/to/ca.pem
```

### 2. Test Connection

```bash
python kiosk_api.py
```

Should see:
```
✅ DeepFace models loaded successfully!
📊 Database: your_host:3306
🗄️ Database Name: your_database
* Running on http://0.0.0.0:5001
```

---

## 🔌 API Endpoints

### 1. Record Attendance

**POST** `/api/attendance/record`

**Form Data:**
```
face_capture: base64 encoded image (required)
event_type: "attendance_in" | "attendance_out" | "break_in" | "break_out"
timestamp: ISO format timestamp (optional)
schedule_id: integer (optional)
```

**Response (Success):**
```json
{
  "message": "✅ Attendance recorded for John Doe",
  "user_id": 123,
  "user_name": "John Doe",
  "event_type": "attendance_in",
  "timestamp": "2026-01-07T14:30:00",
  "course_code": "CS101",
  "room_name": "Room 301",
  "confidence_score": 95.0
}
```

**Response (Error):**
```json
{
  "error": "Face not recognized. Please register first."
}
```

### 2. Health Check

**GET** `/health`

**Response:**
```json
{
  "status": "running",
  "message": "FRAMES Kiosk Backend is operational",
  "timestamp": "2026-01-07T14:30:00"
}
```

### 3. Test Database Connection

**GET** `/api/test/connection`

**Response:**
```json
{
  "status": "connected",
  "registered_users": 15,
  "message": "Database connection successful"
}
```

---

## 📊 System Architecture

```
┌─────────────────────────┐
│   KIOSK FRONTEND        │
│   localhost:3001        │◄─── User faces camera
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   KIOSK BACKEND         │
│   localhost:5001        │◄─── Face recognition API
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   MYSQL DATABASE        │
│   (Shared with main)    │◄─── Stores attendance
└─────────────────────────┘
```

---

## 🎯 Why Separate Backend?

### Benefits:

1. **Independent Deployment**
   - Deploy kiosk without full backend
   - Different servers/locations
   - Easier to maintain

2. **Lightweight**
   - Only ~50MB vs 200MB+ full backend
   - Faster startup
   - Lower resource usage

3. **Security**
   - No admin endpoints exposed
   - Limited API surface
   - Kiosk can't access sensitive features

4. **Scalability**
   - Deploy multiple kiosk backends
   - Load balance across locations
   - Independent scaling

5. **Portability**
   - Easy to move
   - Simple configuration
   - Single .env file

---

## 🔐 Security Features

1. **No Authentication Endpoints** - Can't create/modify users
2. **Read-Only User Data** - Only reads for face matching
3. **Write-Only EventLog** - Can only add attendance records
4. **No Admin Access** - No privileged operations
5. **CORS Configured** - Only allows specified origins
6. **Database Isolation** - Can use read-replica if needed

---

## 🚀 Production Deployment

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/frames-kiosk.service`:

```ini
[Unit]
Description=FRAMES Attendance Kiosk Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/attendance-kiosk/backend
Environment="PATH=/path/to/attendance-kiosk/backend/venv/bin"
ExecStart=/path/to/attendance-kiosk/backend/venv/bin/python kiosk_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable frames-kiosk
sudo systemctl start frames-kiosk
sudo systemctl status frames-kiosk
```

### Option 2: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "kiosk_api.py"]
```

Build and run:
```bash
docker build -t frames-kiosk-backend .
docker run -p 5001:5001 --env-file .env frames-kiosk-backend
```

### Option 3: Gunicorn (Production WSGI)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 kiosk_api:app
```

---

## 🔧 Troubleshooting

### Issue: "Could not connect to database"

**Check:**
1. Is database running?
2. Are credentials correct in `.env`?
3. Is firewall blocking connection?
4. Test with MySQL client:
   ```bash
   mysql -h HOST -u USER -p DATABASE
   ```

### Issue: "DeepFace models not loading"

**Solution:**
```bash
pip install --upgrade deepface opencv-python
python -c "from deepface import DeepFace; DeepFace.build_model('SFace')"
```

### Issue: "Port 5001 already in use"

**Solution:**
```bash
# Find process using port
lsof -i :5001  # Linux/Mac
netstat -ano | findstr :5001  # Windows

# Kill process or change port in kiosk_api.py (last line)
app.run(host='0.0.0.0', port=5002, debug=True)
```

### Issue: "Face not being recognized"

**Check:**
1. Are there registered users?
   ```bash
   curl http://localhost:5001/api/test/connection
   ```
2. Check backend logs for distance scores
3. Adjust threshold in kiosk_api.py (line ~145):
   ```python
   threshold = 0.6  # Increase to 0.8 for testing
   ```

---

## 📊 Performance Tuning

### For Raspberry Pi / Low-Power Devices:

**1. Use lighter face recognition model:**
```python
# Line ~22 in kiosk_api.py
MODEL_NAME = "Facenet"  # Faster than SFace
```

**2. Reduce image quality:**
```python
# In frontend: AttendanceCapturePage.jsx line ~154
const imageData = canvasRef.current.toDataURL('image/jpeg', 0.5);  # Lower quality
```

**3. Disable debug mode:**
```python
# Last line in kiosk_api.py
app.run(host='0.0.0.0', port=5001, debug=False)
```

---

## 📝 Maintenance

### Update Dependencies:
```bash
pip install --upgrade -r requirements.txt
```

### Backup Database Configuration:
```bash
cp .env .env.backup
```

### View Logs:
```bash
# If using systemd
sudo journalctl -u frames-kiosk -f

# If running directly
python kiosk_api.py > logs/kiosk.log 2>&1
```

---

## 🎓 For Capstone Defense

### Key Technical Points:

1. **Microservices Architecture** - Separated backend for kiosk
2. **RESTful API Design** - Standard HTTP endpoints
3. **Face Recognition Pipeline** - DeepFace + SFace model
4. **Database Integration** - Shared database, isolated operations
5. **Security by Design** - Limited API surface, no admin access

### Demo Flow:

1. Show kiosk backend running independently
2. Test health check endpoint
3. Show face recognition in action
4. Display backend logs showing face matching
5. Verify database records created

---

## 📦 Files Overview

```
backend/
├── kiosk_api.py          # Main Flask application
├── db_config.py          # Database configuration helper
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables
├── .env                  # Your configuration (create this)
├── setup.sh              # Linux/Mac setup script
└── setup.bat             # Windows setup script
```

---

## ✅ Quick Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Database connection tested
- [ ] Backend starts without errors
- [ ] Health check endpoint working
- [ ] Face recognition tested
- [ ] Frontend connected (port 5001)
- [ ] Attendance recording works

---

## 🎉 You're All Set!

Your kiosk backend is now **completely independent** and ready to deploy anywhere!

**Next Steps:**
1. Start backend: `python kiosk_api.py`
2. Start frontend: `cd ../` and `npm start`
3. Test face detection
4. Deploy to production

**Happy Deploying! 🚀**
