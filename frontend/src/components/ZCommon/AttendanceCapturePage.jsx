import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './AttendanceCapturePage.css';

const AttendanceCapturePage = () => {
    // --- STATES ---
    const [cameraActive, setCameraActive] = useState(false);
    const [faceDetected, setFaceDetected] = useState(false);
    const [recordedPeople, setRecordedPeople] = useState([]);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [user, setUser] = useState(null);
    const [liveTime, setLiveTime] = useState(new Date());
    const [classInfo, setClassInfo] = useState(null);
    const [autoDetectionEnabled, setAutoDetectionEnabled] = useState(true);
    const [faceBox, setFaceBox] = useState(null); // For face bounding box
    const [zoomLevel, setZoomLevel] = useState(1); // For zoom effect
    
    // --- REFS ---
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const detectionIntervalRef = useRef(null);
    const lastSubmitTimeRef = useRef({});

    // --- INITIAL LOAD ---
    useEffect(() => {
        console.log('📋 Attendance Capture Page Loaded');
        console.log('🔐 Face Recognition Mode: Will identify users by face only');
        
        // Get class info from URL params
        const params = new URLSearchParams(window.location.search);
        const classId = params.get('classId');
        const className = params.get('className');
        const classCode = params.get('classCode');
        
        if (className) {
            setClassInfo({
                classId,
                className,
                classCode
            });
        }

        // Auto-start camera
        startCamera();

        // Live clock update
        const clockInterval = setInterval(() => {
            setLiveTime(new Date());
        }, 1000);

        return () => {
            clearInterval(clockInterval);
            if (detectionIntervalRef.current) {
                clearInterval(detectionIntervalRef.current);
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    // --- START CAMERA ---
    const startCamera = async () => {
        try {
            setError(null);
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 1920 }, height: { ideal: 1080 } },
                audio: false
            });
            
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.onloadedmetadata = () => {
                    videoRef.current.play();
                };
            }
            setCameraActive(true);

            // Start face detection interval
            if (autoDetectionEnabled) {
                startFaceDetection();
            }
        } catch (err) {
            setError('❌ Camera access denied. Please allow camera permissions.');
            console.error('Camera error:', err);
        }
    };

    // --- DETECT FACE POSITION FOR ZOOM ---
    const detectFacePosition = () => {
        if (!videoRef.current || !canvasRef.current) return null;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);

        // Simple face detection using skin color detection
        // This is a basic approach - in production you'd use a proper face detection library
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        let minX = canvas.width, minY = canvas.height;
        let maxX = 0, maxY = 0;
        let facePixels = 0;

        // Scan for skin-colored pixels (rough face detection)
        for (let y = 0; y < canvas.height; y += 4) {
            for (let x = 0; x < canvas.width; x += 4) {
                const i = (y * canvas.width + x) * 4;
                const r = data[i];
                const g = data[i + 1];
                const b = data[i + 2];

                // Skin color range (simplified)
                if (r > 95 && g > 40 && b > 20 &&
                    r > g && r > b &&
                    Math.abs(r - g) > 15) {
                    
                    if (x < minX) minX = x;
                    if (x > maxX) maxX = x;
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;
                    facePixels++;
                }
            }
        }

        // If we detected enough face pixels, return the bounding box
        if (facePixels > 500) {
            const padding = 50;
            return {
                x: Math.max(0, minX - padding),
                y: Math.max(0, minY - padding),
                width: Math.min(canvas.width, maxX - minX + padding * 2),
                height: Math.min(canvas.height, maxY - minY + padding * 2)
            };
        }

        return null;
    };

    // --- CONTINUOUS FACE TRACKING ---
    useEffect(() => {
        if (!cameraActive) return;

        const trackingInterval = setInterval(() => {
            const box = detectFacePosition();
            if (box) {
                setFaceBox(box);
                setZoomLevel(1.3); // Zoom in when face detected
            } else {
                setFaceBox(null);
                setZoomLevel(1); // Zoom out when no face
            }
        }, 100); // Check 10 times per second

        return () => clearInterval(trackingInterval);
    }, [cameraActive]);

    // --- DETECT FACE AND AUTO-SUBMIT ---
    const startFaceDetection = () => {
        console.log('🔄 Starting face detection polling...');
        detectionIntervalRef.current = setInterval(() => {
            if (videoRef.current && canvasRef.current) {
                detectAndSubmit();
            }
        }, 1000); // Check every 1 second
    };

    const detectAndSubmit = async () => {
        try {
            if (!videoRef.current || !canvasRef.current) return;

            // Capture current frame
            const context = canvasRef.current.getContext('2d');
            canvasRef.current.width = videoRef.current.videoWidth;
            canvasRef.current.height = videoRef.current.videoHeight;
            context.drawImage(videoRef.current, 0, 0);
            
            const imageData = canvasRef.current.toDataURL('image/jpeg', 0.8);

            // Submit to backend for face recognition (NO user_id - let backend identify)
            const formData = new FormData();
            formData.append('face_capture', imageData);
            formData.append('event_type', 'attendance_in');
            formData.append('timestamp', new Date().toISOString());
            // DON'T send user_id - let face recognition identify the person
            
            if (classInfo?.classId) {
                formData.append('schedule_id', classInfo.classId);
            }

            console.log(`📤 Sending face for recognition...`);

            const response = await axios.post(
                'http://localhost:5000/api/attendance/record',
                formData,
                {
                    headers: { 'Content-Type': 'multipart/form-data' }
                }
            );

            if (response.status === 200) {
                const recognizedUser = response.data;
                const userId = recognizedUser.user_id;
                const userName = recognizedUser.user_name || 'Unknown Person';

                // Check cooldown (prevent duplicate submissions within 10 seconds)
                const now = Date.now();
                const lastSubmit = lastSubmitTimeRef.current[userId] || 0;
                
                if (now - lastSubmit < 10000) {
                    return; // Skip if submitted recently
                }

                // Mark submission time
                lastSubmitTimeRef.current[userId] = now;

                // Add to recorded list
                const newRecord = {
                    id: userId,
                    name: userName,
                    timestamp: new Date().toLocaleTimeString(),
                    image: imageData,
                    message: recognizedUser.message
                };

                console.log(`✅ Face recognized as: ${userName} (ID: ${userId})`);
                setRecordedPeople(prev => [newRecord, ...prev]);
                setFaceDetected(true);
                setSuccessMessage(`✅ ${userName} recorded at ${newRecord.timestamp}`);

                // Clear success message after 3 seconds
                setTimeout(() => {
                    setSuccessMessage(null);
                    setFaceDetected(false);
                }, 3000);
            }
        } catch (err) {
            // Log errors for debugging
            if (err.response) {
                console.log(`ℹ️ Backend response: ${err.response.status} - ${err.response.data?.error || err.response.data?.message || 'No message'}`);
            } else if (err.request) {
                console.error('❌ No response from backend - is the backend running on port 5000?', err.message);
            } else {
                console.error('❌ Error:', err.message);
            }
        }
    };

    // --- STOP CAMERA ---
    const stopCamera = () => {
        if (detectionIntervalRef.current) {
            clearInterval(detectionIntervalRef.current);
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setCameraActive(false);
    };

    // --- RENDER ---
    return (
        <div className="frames-container">
            {/* HEADER */}
            <div className="frames-header">
                <div className="header-left">
                    <h1 className="frames-logo">FRAMES</h1>
                </div>
                <div className="header-right">
                    <span className="admin-badge">Smart Attendance System</span>
                </div>
            </div>

            {/* MAIN CONTENT */}
            <div className="frames-content-grid">
                {/* LEFT SIDE - LARGE CAMERA */}
                <div className="camera-section">
                    <div className="camera-wrapper-large">
                        <div className="camera-container-large">
                            {cameraActive && (
                                <>
                                    <video
                                        ref={videoRef}
                                        className="camera-feed-large"
                                        autoPlay
                                        playsInline
                                        style={{
                                            transform: `scale(${zoomLevel})`,
                                            transition: 'transform 0.3s ease-out'
                                        }}
                                    />
                                    {/* FACE DETECTION BOX */}
                                    {faceBox && (
                                        <div
                                            className="face-detection-box"
                                            style={{
                                                left: `${(faceBox.x / videoRef.current.videoWidth) * 100}%`,
                                                top: `${(faceBox.y / videoRef.current.videoHeight) * 100}%`,
                                                width: `${(faceBox.width / videoRef.current.videoWidth) * 100}%`,
                                                height: `${(faceBox.height / videoRef.current.videoHeight) * 100}%`,
                                            }}
                                        >
                                            <div className="corner corner-tl"></div>
                                            <div className="corner corner-tr"></div>
                                            <div className="corner corner-bl"></div>
                                            <div className="corner corner-br"></div>
                                        </div>
                                    )}
                                </>
                            )}
                            {!cameraActive && (
                                <div className="camera-loading">
                                    <i className="fas fa-spinner fa-spin"></i>
                                    <p>Initializing Camera...</p>
                                </div>
                            )}
                        </div>

                        {/* FACE DETECTION INDICATOR */}
                        {faceDetected && (
                            <div className="face-detection-overlay">
                                <div className="detection-pulse"></div>
                                <span className="detection-text">FACE DETECTED</span>
                            </div>
                        )}
                    </div>

                    {/* INSTRUCTIONS */}
                    <div className="kiosk-instructions">
                        <i className="fas fa-camera"></i>
                        <h2>Please look at the camera</h2>
                    </div>
                </div>

                {/* RIGHT SIDE - INFORMATION PANEL */}
                <div className="info-section">
                    <div className="info-panel">
                        <h2 className="panel-title">
                            <i className="fas fa-users"></i> Detection Information
                        </h2>

                        {/* SUCCESS MESSAGE */}
                        {successMessage && (
                            <div className="success-notification-large">
                                <i className="fas fa-check-circle"></i>
                                <p>{successMessage}</p>
                            </div>
                        )}

                        {/* RECORDED LIST */}
                        {recordedPeople.length > 0 ? (
                            <div className="recorded-section-large">
                                <div className="records-header">
                                    <h3><i className="fas fa-check-double"></i> Recorded Attendance</h3>
                                    <span className="record-count">{recordedPeople.length}</span>
                                </div>
                                <div className="recorded-list-large">
                                    {recordedPeople.map((person, index) => (
                                        <div key={index} className="recorded-item-large">
                                            <div className="item-number">{index + 1}</div>
                                            <div className="item-details">
                                                <div className="item-name">{person.name}</div>
                                                <div className="item-time">
                                                    <i className="fas fa-clock"></i> {person.timestamp}
                                                </div>
                                            </div>
                                            <div className="item-status">
                                                <i className="fas fa-check-circle"></i>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="empty-state">
                                <i className="fas fa-inbox"></i>
                                <p>Waiting for attendance...</p>
                                <p className="subtitle">Stand in front of the camera</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* FOOTER */}
            <div className="frames-footer">
                <p>FRAMES - Intelligent Attendance System | Powered by TUP</p>
            </div>

            <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
    );
};

export default AttendanceCapturePage;
