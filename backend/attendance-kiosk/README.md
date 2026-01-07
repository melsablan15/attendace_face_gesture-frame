# 🎥 FRAMES Attendance Kiosk - Standalone

## 📋 Overview

This is a **standalone attendance capture system** that can be deployed independently from the main FRAMES application. Perfect for classroom displays, entrance kiosks, or dedicated attendance stations.

---

## ✨ Features

- 🎯 **Pure Face Recognition** - No login required, identifies users by face only
- 📹 **Auto-Zoom** - Automatically zooms in on detected faces
- 🟢 **Animated Detection Box** - Green glowing box with pulsing corners
- 📊 **Real-time Feedback** - Shows who was detected instantly
- 🔄 **Auto-Refresh** - Continuously monitors for faces
- 📱 **Responsive Design** - Works on tablets, monitors, and touchscreens
- 🎨 **Professional UI** - Clean, modern interface

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd attendance-kiosk
npm install
```

### 2. Start the Kiosk
```bash
npm start
```

The kiosk will open at `http://localhost:3000`

### 3. Configure Backend Connection

Make sure your backend is running on `localhost:5000`. If using a different URL, edit:

**File:** `src/AttendanceCapturePage.jsx` (line ~210)
```javascript
const response = await axios.post(
    'http://localhost:5000/api/attendance/record',  // Change this URL
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
);
```

---

## 📦 Folder Structure

```
attendance-kiosk/
├── public/
│   └── index.html           # HTML template
├── src/
│   ├── index.js             # Entry point
│   ├── AttendanceCapturePage.jsx  # Main component
│   └── AttendanceCapturePage.css  # Styles
├── package.json             # Dependencies
└── README.md               # This file
```

---

## 🔧 Configuration

### Backend API Endpoint

Change the API URL in `AttendanceCapturePage.jsx`:

```javascript
// Line ~210
const response = await axios.post(
    'http://YOUR_SERVER_IP:5000/api/attendance/record',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
);
```

### Detection Cooldown

Prevent duplicate submissions (default: 10 seconds):

```javascript
// Line ~224
if (now - lastSubmit < 10000) return;  // Change 10000 to adjust cooldown (in milliseconds)
```

### Face Detection Sensitivity

Adjust how many pixels needed to detect a face:

```javascript
// Line ~125
if (facePixels > 500) {  // Lower = more sensitive, Higher = less sensitive
```

### Zoom Level

Change how much the camera zooms in:

```javascript
// Line ~138
setZoomLevel(1.3);  // Change to 1.5 for more zoom, 1.2 for less
```

---

## 🎯 Use Cases

### 1. Classroom Display
- Mount tablet/monitor at classroom entrance
- Students look at camera when entering
- Automatic attendance recording
- No interaction needed

### 2. Office Check-In
- Place kiosk at office entrance
- Employees check in on arrival
- Tracks attendance automatically
- Professional appearance

### 3. Event Registration
- Set up at event entrance
- Attendees registered by face
- Real-time attendance list
- No manual check-in needed

### 4. Library/Lab Access
- Monitor room access
- Track who enters/exits
- Automatic logging
- Security monitoring

---

## 🖥️ Deployment Options

### Option 1: Local Network

1. **Build for production:**
```bash
npm run build
```

2. **Serve the build folder:**
```bash
npm install -g serve
serve -s build -p 3000
```

3. **Access from any device on network:**
```
http://YOUR_COMPUTER_IP:3000
```

### Option 2: Dedicated Kiosk Device

1. **Use a Raspberry Pi / Mini PC**
2. **Install Chrome/Chromium**
3. **Set to fullscreen kiosk mode:**
```bash
chromium-browser --kiosk --incognito http://localhost:3000
```

### Option 3: Tablet Mount

1. **Use Android/iOS tablet**
2. **Open in browser**
3. **Add to home screen**
4. **Enable fullscreen mode**

---

## 🎨 Customization

### Change Theme Colors

**File:** `src/AttendanceCapturePage.css`

```css
/* Primary Color (Red) */
.frames-header {
    background: linear-gradient(90deg, #c82333 0%, #a01d2a 100%);
    /* Change to your school colors */
}

/* Detection Box Color (Green) */
.face-detection-box {
    border: 3px solid #00ff00;  /* Change to any color */
}

/* Success Color (Green) */
.success-notification-large {
    border: 2px solid #28a745;  /* Change to match brand */
}
```

### Change Logo Text

**File:** `src/AttendanceCapturePage.jsx` (line ~287)

```javascript
<h1 className="frames-logo">FRAMES</h1>
// Change "FRAMES" to your institution name
```

### Change Footer Text

**File:** `src/AttendanceCapturePage.jsx` (line ~397)

```javascript
<p>FRAMES - Intelligent Attendance System | Powered by TUP</p>
// Change to your institution details
```

---

## 🔍 Troubleshooting

### Issue: Camera not working
**Solution:**
- Grant camera permissions in browser
- Check if camera is already in use
- Try different browser (Chrome recommended)
- Check browser console for errors

### Issue: Backend connection failed
**Solution:**
- Verify backend is running on port 5000
- Check firewall settings
- Update API URL in code
- Test with: `http://localhost:5000/api/test/face-data`

### Issue: Face not being detected
**Solution:**
- Ensure good lighting
- Face camera directly
- Move closer to camera
- Check backend console for face matching logs

### Issue: Wrong person detected
**Solution:**
- Re-register with better face capture
- Check database for duplicate face data
- Adjust detection threshold in backend
- Ensure proper lighting during registration

---

## 📊 System Requirements

### Minimum:
- **CPU:** Dual-core 2GHz
- **RAM:** 4GB
- **Camera:** 720p webcam
- **Browser:** Chrome 90+ / Firefox 88+
- **Network:** Local network access to backend

### Recommended:
- **CPU:** Quad-core 2.5GHz+
- **RAM:** 8GB
- **Camera:** 1080p webcam with good low-light performance
- **Browser:** Latest Chrome
- **Network:** Wired Ethernet connection
- **Display:** 1920x1080 or higher

---

## 🔐 Security Considerations

1. **No Authentication** - This is intentional for kiosk use
2. **Network Security** - Deploy on secure internal network
3. **Physical Security** - Mount in monitored location
4. **Data Privacy** - Face embeddings stored securely in database
5. **Access Control** - Backend handles all authentication

---

## 🎓 For Capstone/Thesis

### Key Points to Highlight:

1. **Standalone System** - Can operate independently
2. **Zero User Interaction** - Fully automatic
3. **Real-time Processing** - Instant face recognition
4. **Professional Design** - Production-ready interface
5. **Scalable** - Deploy multiple kiosks easily

### Demo Setup:

1. Setup kiosk on display/tablet
2. Show automatic face detection
3. Demonstrate zoom feature
4. Show real-time attendance list
5. Display admin dashboard showing results

---

## 📝 Credits

**Developed for:** TUP-Manila Capstone Project
**System:** FRAMES (Face Recognition Attendance Management & Evaluation System)
**Technology Stack:**
- React 18
- Axios
- HTML5 Canvas
- CSS3 Animations
- WebRTC (getUserMedia)

---

## 📞 Support

For issues or questions:
1. Check the main project README
2. Review troubleshooting section
3. Check backend logs
4. Test with diagnostic script

---

## 🚀 Next Steps

After setting up the kiosk:

1. ✅ Test face detection
2. ✅ Verify backend connection
3. ✅ Check admin dashboard shows results
4. ✅ Test with multiple users
5. ✅ Deploy to production location
6. ✅ Monitor and maintain

---

**Happy Kiosking! 🎉**
