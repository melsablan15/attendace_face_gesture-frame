# 📁 ATTENDANCE KIOSK - Standalone Folder Setup

## ✅ What Was Created

I've created a **completely separate standalone folder** for the attendance capture page!

### New Folder Structure:
```
Capstoneee-main/
├── backend/                    # Your existing backend
├── frontend/                   # Your existing frontend
└── attendance-kiosk/           # ⭐ NEW - Standalone kiosk app
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── index.js
    │   ├── AttendanceCapturePage.jsx
    │   └── AttendanceCapturePage.css
    ├── package.json
    └── README.md
```

---

## 🚀 How to Run

### Step 1: Install Dependencies (First Time Only)
```bash
cd attendance-kiosk
npm install
```

### Step 2: Start the Kiosk
```bash
npm start
```

Runs on: `http://localhost:3000` (separate from main app)

---

## 🎯 Why Separate Folder?

### Benefits:

1. **Independent Deployment**
   - Can deploy kiosk without main app
   - Different servers/locations
   - Easier to manage

2. **Simplified Dependencies**
   - Only needs React, Axios
   - No routing, no auth, no complex state
   - Faster loading

3. **Easy Distribution**
   - Share kiosk folder only
   - Deploy to multiple locations
   - No need for full codebase

4. **Better Security**
   - Kiosk has no access to admin features
   - No sensitive code exposed
   - Minimal attack surface

5. **Flexible Deployment**
   - Run on Raspberry Pi
   - Deploy on tablets
   - Dedicated kiosk machines
   - Cloud hosting

---

## 🔄 Running Both Systems

You can run both the main app AND the kiosk simultaneously:

### Terminal 1 - Backend:
```bash
cd backend
python app.py
```
Runs on: `http://localhost:5000`

### Terminal 2 - Main App:
```bash
cd frontend
npm start
```
Runs on: `http://localhost:3000`

### Terminal 3 - Kiosk:
```bash
cd attendance-kiosk
npm start
```
Will ask for different port (usually `http://localhost:3001`)

Or, press `Y` when asked if you want to run on a different port.

---

## 📊 How They Connect

```
┌─────────────────────┐
│   MAIN FRONTEND     │
│   localhost:3000    │◄─── Admin/Faculty/Student dashboards
│                     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      BACKEND        │
│   localhost:5000    │◄─── Handles all API requests
│                     │
└──────────┬──────────┘
           ▲
           │
┌──────────┴──────────┐
│   KIOSK FRONTEND    │
│   localhost:3001    │◄─── Standalone attendance capture
│                     │
└─────────────────────┘
```

All systems use the **same backend** API.

---

## 🎨 Customization

### Change Colors

**File:** `attendance-kiosk/src/AttendanceCapturePage.css`

```css
/* Line ~19 - Header background */
.frames-header {
    background: linear-gradient(90deg, #YOUR_COLOR 0%, #YOUR_COLOR2 100%);
}

/* Line ~94 - Detection box color */
.face-detection-box {
    border: 3px solid #YOUR_COLOR;
}
```

### Change Text

**File:** `attendance-kiosk/src/AttendanceCapturePage.jsx`

```javascript
// Line ~287 - Logo
<h1 className="frames-logo">YOUR SCHOOL NAME</h1>

// Line ~290 - Subtitle
<span className="admin-badge">Your Tagline Here</span>

// Line ~397 - Footer
<p>Your School - Attendance System | Powered by Your Name</p>
```

### Change Backend URL

**File:** `attendance-kiosk/src/AttendanceCapturePage.jsx`

```javascript
// Line ~210 - API endpoint
const response = await axios.post(
    'http://YOUR_SERVER:5000/api/attendance/record',  // Change this
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
);
```

---

## 📦 Production Deployment

### Option 1: Build and Serve

```bash
cd attendance-kiosk
npm run build
npm install -g serve
serve -s build -p 3001
```

### Option 2: Deploy to Netlify/Vercel

```bash
cd attendance-kiosk
npm run build
# Upload 'build' folder to hosting service
```

### Option 3: Raspberry Pi Kiosk

```bash
# 1. Build the app
npm run build

# 2. Install web server
sudo apt install nginx

# 3. Copy build to web root
sudo cp -r build/* /var/www/html/

# 4. Set Chrome to kiosk mode
chromium-browser --kiosk http://localhost
```

---

## 🎯 Use Cases

### Scenario 1: Single Classroom
- Run kiosk on classroom computer
- Students check in when entering
- Display shows who's checked in
- Admin monitors from dashboard

### Scenario 2: Multiple Locations
- Deploy kiosk in each classroom
- All connect to central backend
- Admin sees all locations
- Distributed attendance system

### Scenario 3: Mobile Kiosk
- Install on tablets
- Move between locations
- Flexible deployment
- Easy setup

---

## ✅ Checklist for Setup

- [ ] Backend running (`python app.py`)
- [ ] Installed kiosk dependencies (`npm install`)
- [ ] Started kiosk (`npm start`)
- [ ] Camera permissions granted
- [ ] Tested face detection
- [ ] Verified backend connection
- [ ] Checked admin dashboard shows results
- [ ] Customized branding (optional)
- [ ] Tested with multiple users
- [ ] Ready for deployment

---

## 📁 Main App vs Kiosk

| Feature | Main App (frontend/) | Kiosk (attendance-kiosk/) |
|---------|---------------------|---------------------------|
| **Purpose** | Full system management | Attendance capture only |
| **Users** | Admin/Faculty/Students | Anyone (no login) |
| **Features** | Dashboards, reports, settings | Face capture only |
| **Complexity** | High | Low |
| **Size** | ~50MB | ~5MB |
| **Dependencies** | Many | Few |
| **Deployment** | Main server | Distributed kiosks |

---

## 🔧 Maintenance

### Update Kiosk Code:
```bash
cd attendance-kiosk
# Make your changes
npm start  # Test
npm run build  # Build for production
```

### Update Backend Connection:
```bash
cd attendance-kiosk/src
# Edit AttendanceCapturePage.jsx
# Change API URL on line ~210
```

### Reset Kiosk:
```bash
cd attendance-kiosk
rm -rf node_modules package-lock.json
npm install
npm start
```

---

## 🎓 For Demonstration

### Setup for Capstone Defense:

1. **Main Display** - Show admin dashboard with Live Detection
2. **Kiosk Display** - Show attendance capture page
3. **Demo Flow:**
   - Person walks to kiosk
   - Face detected automatically
   - Admin dashboard updates in real-time
   - Show attendance record created

---

## 📞 Quick Support

### Kiosk not starting?
```bash
cd attendance-kiosk
rm -rf node_modules
npm install
npm start
```

### Backend not connecting?
- Check backend is running
- Verify URL in code
- Check firewall settings

### Camera not working?
- Grant browser permissions
- Check if camera in use
- Try different browser

---

## 🎉 You're All Set!

Your attendance kiosk is now in a **separate, independent folder** ready to deploy anywhere!

**Next Steps:**
1. Test it: `cd attendance-kiosk && npm start`
2. Customize it: Edit colors, text, logos
3. Deploy it: Build and serve on kiosk devices
4. Monitor it: Check admin dashboard for results

**Happy Deploying! 🚀**
