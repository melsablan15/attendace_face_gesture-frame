# 🎯 COMPLETE STANDALONE KIOSK SETUP

## 📋 What You Now Have

A **completely independent attendance kiosk system** that can run separately from your main FRAMES application!

```
📁 attendance-kiosk/
├── 📁 backend/              ⭐ Standalone backend (Port 5001)
│   ├── kiosk_api.py         # Main API server
│   ├── db_config.py         # Database config
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Config template
│   ├── setup.sh             # Linux/Mac setup
│   ├── setup.bat            # Windows setup
│   └── README.md            # Backend docs
│
└── 📁 src/                  ⭐ Standalone frontend (Port 3001)
    ├── index.js             # Entry point
    ├── AttendanceCapturePage.jsx
    ├── AttendanceCapturePage.css
    ├── package.json
    └── README.md            # Frontend docs
```

---

## 🚀 Complete Setup Guide

### Step 1: Setup Backend

```bash
# Go to backend folder
cd attendance-kiosk/backend

# Windows:
setup.bat

# Linux/Mac:
chmod +x setup.sh
./setup.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install Python dependencies
- ✅ Create .env configuration file

### Step 2: Configure Database

Edit `.env` file in `backend/` folder:

```env
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
DB_PORT=3306
```

**Example for local MySQL:**
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=frames_db
DB_PORT=3306
```

**Example for cloud database:**
```env
DB_HOST=your-cloud-host.com
DB_USER=admin
DB_PASSWORD=secure_password
DB_NAME=frames_production
DB_PORT=3306
DB_SSL_CA=path/to/ca.pem
```

### Step 3: Start Backend

```bash
cd attendance-kiosk/backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Start server
python kiosk_api.py
```

Should see:
```
✅ DeepFace models loaded successfully!
📊 Database: your_host:3306
🗄️ Database Name: your_database
* Running on http://0.0.0.0:5001
```

### Step 4: Setup Frontend

```bash
# Open new terminal
cd attendance-kiosk

# Install dependencies (first time only)
npm install

# Start frontend
npm start
```

Will run on: `http://localhost:3001` (or next available port)

### Step 5: Test the System

1. **Test Backend Health:**
   - Open: `http://localhost:5001/health`
   - Should show: `{"status": "running", ...}`

2. **Test Database Connection:**
   - Open: `http://localhost:5001/api/test/connection`
   - Should show registered users count

3. **Test Kiosk:**
   - Open: `http://localhost:3001`
   - Stand in front of camera
   - Green box should appear
   - Your name should be recognized

---

## 🎯 System Architecture

### Current Setup (After Separation):

```
┌──────────────────────┐
│  MAIN BACKEND        │
│  localhost:5000      │◄─── Main app, admin, reports
│                      │
└──────────────────────┘

┌──────────────────────┐
│  KIOSK BACKEND       │
│  localhost:5001      │◄─── ONLY face recognition
│                      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  MYSQL DATABASE      │
│  (Shared)            │◄─── Both backends use same DB
│                      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  KIOSK FRONTEND      │
│  localhost:3001      │◄─── Attendance capture page
│                      │
└──────────────────────┘
```

---

## 💡 Benefits of This Setup

### 1. Independent Deployment

**Before:**
- Had to deploy entire backend (200MB+)
- All features exposed to kiosk
- Complex dependencies

**After:**
- Deploy lightweight backend (50MB)
- Only attendance endpoints
- Minimal dependencies

### 2. Security

**Before:**
- Kiosk could potentially access admin endpoints
- All routes exposed

**After:**
- Kiosk backend has NO admin routes
- Only 3 endpoints total
- Isolated from main system

### 3. Scalability

**Before:**
- Single backend for everything
- Hard to scale kiosks

**After:**
- Deploy kiosk backend per location
- Load balance independently
- Scale based on need

### 4. Portability

**Before:**
- Needed full codebase
- Complex setup

**After:**
- Copy `attendance-kiosk` folder
- Simple .env configuration
- Ready to deploy

---

## 🚀 Deployment Scenarios

### Scenario 1: Single Classroom Kiosk

**Setup:**
```
Classroom Computer:
- Frontend: localhost:3001
- Backend: localhost:5001
- Database: Cloud (AWS/Azure)
```

**Benefits:**
- Everything runs locally
- Fast response
- Works offline (if DB cached)

### Scenario 2: Multiple Classroom Kiosks

**Setup:**
```
Classroom 1:
- Frontend: localhost:3001
- Backend: localhost:5001 ──┐
                            │
Classroom 2:                │
- Frontend: localhost:3001  ├──► Central Database
- Backend: localhost:5001 ──┤      (AWS RDS)
                            │
Classroom 3:                │
- Frontend: localhost:3001  │
- Backend: localhost:5001 ──┘
```

**Benefits:**
- Independent operations
- Distributed load
- Fault tolerant

### Scenario 3: Centralized Backend

**Setup:**
```
Server Room:
- Kiosk Backend: 192.168.1.100:5001
- Database: Same server

Classroom 1: Frontend only ──┐
Classroom 2: Frontend only ──┼──► Central Backend
Classroom 3: Frontend only ──┘
```

**Benefits:**
- Easier maintenance
- Single backend to monitor
- Centralized control

---

## ⚙️ Configuration Options

### Frontend Configuration

**File:** `src/AttendanceCapturePage.jsx`

```javascript
// Line ~165 - Backend URL
const response = await axios.post(
    'http://192.168.1.100:5001/api/attendance/record',  // Change this
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
);
```

### Backend Configuration

**File:** `backend/.env`

```env
# Database
DB_HOST=your_host
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database
DB_PORT=3306

# Optional: SSL for cloud databases
DB_SSL_CA=path/to/certificate.pem
```

### Port Configuration

**Backend - File:** `backend/kiosk_api.py` (Last line)

```python
app.run(host='0.0.0.0', port=5001, debug=True)
                           # ^ Change port here
```

**Frontend - File:** `package.json`

```json
{
  "scripts": {
    "start": "PORT=3001 react-scripts start"
           // ^ Change port here
  }
}
```

---

## 🔧 Maintenance

### Update Backend:
```bash
cd attendance-kiosk/backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install --upgrade -r requirements.txt
python kiosk_api.py
```

### Update Frontend:
```bash
cd attendance-kiosk
npm install
npm start
```

### Check Logs:
```bash
# Backend logs (in terminal where it's running)
# Or save to file:
python kiosk_api.py > logs/kiosk.log 2>&1

# Frontend logs (browser console - F12)
```

---

## 🐛 Troubleshooting

### Issue: "Port already in use"

**Backend:**
```bash
# Change port in kiosk_api.py last line:
app.run(host='0.0.0.0', port=5002, debug=True)
```

**Frontend:**
```bash
# Will ask if you want different port
# Press Y to use port 3002
```

### Issue: "Database connection failed"

**Check:**
1. Is database running?
2. Are credentials correct in `.env`?
3. Test connection:
   ```bash
   curl http://localhost:5001/api/test/connection
   ```

### Issue: "Face not recognized"

**Check:**
1. Backend logs showing face matching?
2. Distance scores being printed?
3. Are there registered users?
4. Adjust threshold in `kiosk_api.py`:
   ```python
   threshold = 0.8  # Increase for testing
   ```

---

## 📊 Performance Tips

### For Raspberry Pi:

1. **Use lighter model:**
   ```python
   # kiosk_api.py line ~22
   MODEL_NAME = "Facenet"  # Faster than SFace
   ```

2. **Reduce image quality:**
   ```javascript
   // AttendanceCapturePage.jsx
   const imageData = canvas.toDataURL('image/jpeg', 0.5);
   ```

3. **Increase cooldown:**
   ```javascript
   // AttendanceCapturePage.jsx
   if (now - lastSubmit < 15000) return;  // 15 seconds
   ```

---

## 🎓 For Capstone Defense

### Technical Highlights:

1. **Microservices Architecture**
   - Separated concerns
   - Independent deployment
   - Scalable design

2. **RESTful API Design**
   - Standard HTTP methods
   - JSON responses
   - Clear endpoints

3. **Security by Design**
   - Limited API surface
   - No privileged operations
   - Isolated from main system

4. **Face Recognition**
   - DeepFace framework
   - SFace model
   - Real-time processing

### Demo Flow:

1. Show both backends running independently
2. Test kiosk backend health
3. Demonstrate face recognition
4. Show database records
5. Display live detection on admin dashboard

---

## ✅ Final Checklist

### Backend:
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env configured
- [ ] Database connection tested
- [ ] Server starts on port 5001
- [ ] Health check works
- [ ] Face recognition tested

### Frontend:
- [ ] Dependencies installed
- [ ] Starts on port 3001
- [ ] Camera permissions granted
- [ ] Backend URL configured
- [ ] Face detection working
- [ ] Attendance records created

### System:
- [ ] Both can run simultaneously
- [ ] Database shared correctly
- [ ] Admin can see kiosk records
- [ ] Multiple kiosks work together
- [ ] Ready for deployment

---

## 🎉 Congratulations!

You now have a **fully independent, production-ready attendance kiosk system!**

**Key Achievement:**
- ✅ Standalone frontend
- ✅ Standalone backend
- ✅ Shared database
- ✅ Easy deployment
- ✅ Scalable architecture

**Next Steps:**
1. Test everything
2. Customize branding
3. Deploy to production
4. Monitor and maintain

**Happy Deploying! 🚀**
