import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './AttendanceCapturePage.css';

const AttendanceCapturePage = () => {
    const [cameraActive, setCameraActive] = useState(false);
    const [faceDetected, setFaceDetected] = useState(false);
    const [recordedPeople, setRecordedPeople] = useState([]);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [classInfo, setClassInfo] = useState(null);
    
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const lastSubmitTimeRef = useRef({});

    const API_URL = 'http://3.27.88.93:5001';

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        setClassInfo({
            classId: params.get('classId'),
            className: params.get('className')
        });

        const initCamera = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: 1280, height: 720 }
                });
                streamRef.current = stream;
                if (videoRef.current) videoRef.current.srcObject = stream;
                setCameraActive(true);
            } catch (err) {
                setError('❌ Camera access denied.');
            }
        };
        initCamera();
        return () => streamRef.current?.getTracks().forEach(t => t.stop());
    }, []);

    useEffect(() => {
        if (!cameraActive) return;
        const interval = setInterval(() => detectAndSubmit(), 2000);
        return () => clearInterval(interval);
    }, [cameraActive]);

    const detectAndSubmit = async () => {
        if (!videoRef.current || videoRef.current.videoWidth === 0) return;

        const canvas = canvasRef.current;
        const video = videoRef.current;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        const formData = new FormData();
        
        // FIX: Key must match Flask request.files['face_capture']
        formData.append('face_capture', imageData);
        if (classInfo?.classId) formData.append('schedule_id', classInfo.classId);

        try {
            const res = await axios.post(`${API_URL}/api/attendance/record`, formData);
            if (res.status === 200) {
                const { user_id, user_name } = res.data;
                if (Date.now() - (lastSubmitTimeRef.current[user_id] || 0) < 10000) return;

                lastSubmitTimeRef.current[user_id] = Date.now();
                setRecordedPeople(prev => [{ name: user_name, time: new Date().toLocaleTimeString() }, ...prev]);
                setSuccessMessage(`Welcome, ${user_name}!`);
                setFaceDetected(true);
                setTimeout(() => { setSuccessMessage(null); setFaceDetected(false); }, 3000);
            }
        } catch (err) {
            // Log 400 errors to see what the backend specifically dislikes
            console.error("Backend Error:", err.response?.data);
        }
    };

    return (
        <div className="app-container">
            <header className="main-header">
                <h1>FRAMES</h1>
                <div className="class-badge">{classInfo?.className || 'General Attendance'}</div>
            </header>

            <div className="main-layout">
                <section className="video-section">
                    <div className="video-card">
                        <video ref={videoRef} autoPlay muted playsInline className="video-feed" />
                        {faceDetected && <div className="scan-line"></div>}
                    </div>
                    <div className="instruction-box">Please align your face with the camera</div>
                </section>

                <aside className="data-section">
                    <div className="status-card">
                        <h2>System Status</h2>
                        {successMessage ? <div className="alert-success">{successMessage}</div> : <p>Scanning...</p>}
                    </div>

                    <div className="log-card">
                        <h2>Recent Records</h2>
                        <div className="log-list">
                            {recordedPeople.map((p, i) => (
                                <div key={i} className="log-entry">
                                    <strong>{p.name}</strong> <span>{p.time}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </aside>
            </div>
            <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
    );
};

export default AttendanceCapturePage;