import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './LiveDetectionPage.css';

const LiveDetectionPage = () => {
    const [detections, setDetections] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(new Date());
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [scanning, setScanning] = useState(false);

    // Fetch recent detections
    const fetchDetections = async () => {
        try {
            setScanning(true);
            
            console.log('🔄 Fetching attendance records...');
            
            // Get records from last 24 hours
            const response = await axios.get('http://localhost:5000/api/admin/attendance-records', {
                params: { days: 1 }
            });
            
            console.log(`📊 API returned ${response.data.length} total records`);
            
            // Filter to last 30 minutes (increased from 10 for testing)
            const thirtyMinutesAgo = new Date(Date.now() - 30 * 60 * 1000);
            const recentDetections = response.data.filter(record => {
                const recordTime = new Date(record.timestamp);
                return recordTime > thirtyMinutesAgo;
            });
            
            console.log(`✅ Found ${recentDetections.length} detections in last 30 minutes`);
            if (recentDetections.length > 0) {
                console.log('Latest detection:', recentDetections[0]);
            }
            
            setDetections(recentDetections);
            setLastUpdate(new Date());
            setLoading(false);
            
            // Show scanning indicator for at least 500ms for visual feedback
            setTimeout(() => setScanning(false), 500);
        } catch (err) {
            console.error('❌ Error fetching detections:', err);
            console.error('Error details:', err.response?.data || err.message);
            setLoading(false);
            setScanning(false);
        }
    };

    // Auto-refresh every 3 seconds
    useEffect(() => {
        fetchDetections();
        
        if (autoRefresh) {
            const interval = setInterval(() => {
                fetchDetections();
            }, 3000); // 3 seconds
            
            return () => clearInterval(interval);
        }
    }, [autoRefresh]);

    // Format time (show seconds for real-time feeling)
    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    // Get time ago
    const getTimeAgo = (timestamp) => {
        const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
        if (seconds < 10) return 'Just now';
        if (seconds < 60) return `${seconds}s ago`;
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        return `${hours}h ago`;
    };

    // Get event style
    const getEventStyle = (eventType) => {
        switch (eventType) {
            case 'attendance_in':
                return { icon: 'fas fa-sign-in-alt', color: '#28a745', label: 'Check In' };
            case 'attendance_out':
                return { icon: 'fas fa-sign-out-alt', color: '#ff9800', label: 'Check Out' };
            case 'break_in':
                return { icon: 'fas fa-pause-circle', color: '#2196F3', label: 'Break Start' };
            case 'break_out':
                return { icon: 'fas fa-play-circle', color: '#9c27b0', label: 'Break End' };
            default:
                return { icon: 'fas fa-clock', color: '#607d8b', label: 'Event' };
        }
    };

    return (
        <div className="live-detection-container">
            {/* HEADER */}
            <div className="detection-header">
                <div className="header-left">
                    <h1>
                        <i className="fas fa-video"></i> Live Face Detection
                    </h1>
                    <p>Real-time camera attendance monitoring</p>
                </div>
                <div className="header-right">
                    <div className="status-indicator">
                        <div className={`status-dot ${autoRefresh ? 'active' : 'inactive'}`}></div>
                        <span>{scanning ? 'Scanning...' : autoRefresh ? 'Live' : 'Paused'}</span>
                    </div>
                    <button 
                        className={`btn-toggle ${autoRefresh ? 'active' : ''}`}
                        onClick={() => setAutoRefresh(!autoRefresh)}
                    >
                        <i className={`fas fa-${autoRefresh ? 'pause' : 'play'}`}></i>
                        {autoRefresh ? 'Pause' : 'Resume'}
                    </button>
                    <button className="btn-refresh" onClick={fetchDetections}>
                        <i className="fas fa-sync"></i> Refresh
                    </button>
                </div>
            </div>

            {/* STATS BAR */}
            <div className="detection-stats">
                <div className="stat-item">
                    <i className="fas fa-users"></i>
                    <div>
                        <div className="stat-value">{detections.length}</div>
                        <div className="stat-label">Detected (10min)</div>
                    </div>
                </div>
                <div className="stat-item">
                    <i className="fas fa-clock"></i>
                    <div>
                        <div className="stat-value">{formatTime(lastUpdate)}</div>
                        <div className="stat-label">Last Update</div>
                    </div>
                </div>
                <div className="stat-item">
                    <i className="fas fa-check-circle"></i>
                    <div>
                        <div className="stat-value">
                            {detections.filter(d => d.event_type === 'attendance_in').length}
                        </div>
                        <div className="stat-label">Check-Ins</div>
                    </div>
                </div>
            </div>

            {/* SCANNING OVERLAY */}
            {scanning && !loading && (
                <div className="scanning-banner">
                    <i className="fas fa-radar"></i>
                    <span>Scanning for faces...</span>
                    <div className="scanning-animation">
                        <div className="scan-line"></div>
                    </div>
                </div>
            )}

            {/* DETECTION GRID */}
            <div className="detection-grid">
                {loading ? (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Loading detections...</p>
                    </div>
                ) : detections.length > 0 ? (
                    detections.map((detection, index) => {
                        const eventStyle = getEventStyle(detection.event_type);
                        const isRecent = (new Date() - new Date(detection.timestamp)) < 30000; // Last 30 seconds
                        
                        return (
                            <div 
                                key={index} 
                                className={`detection-card ${isRecent ? 'recent-detection' : ''}`}
                            >
                                {/* Captured Face */}
                                <div className="detection-image">
                                    {detection.face_data ? (
                                        <img 
                                            src={detection.face_data} 
                                            alt="Detected Face"
                                            className="face-image"
                                        />
                                    ) : (
                                        <div className="no-image">
                                            <i className="fas fa-user-circle"></i>
                                        </div>
                                    )}
                                    {isRecent && (
                                        <div className="new-badge">
                                            <i className="fas fa-circle"></i> NEW
                                        </div>
                                    )}
                                </div>

                                {/* Detection Info */}
                                <div className="detection-info">
                                    <div className="person-name">
                                        {detection.user_name || 'Unknown Person'}
                                    </div>
                                    <div className="person-id">
                                        ID: {detection.user_id}
                                    </div>
                                    
                                    <div className="event-badge" style={{ backgroundColor: eventStyle.color }}>
                                        <i className={eventStyle.icon}></i>
                                        {eventStyle.label}
                                    </div>

                                    <div className="detection-details">
                                        <div className="detail-row">
                                            <i className="fas fa-clock"></i>
                                            <span>{formatTime(detection.timestamp)}</span>
                                            <span className="time-ago">{getTimeAgo(detection.timestamp)}</span>
                                        </div>
                                        <div className="detail-row">
                                            <i className="fas fa-door-open"></i>
                                            <span>{detection.room_name || 'Unknown Room'}</span>
                                        </div>
                                        <div className="detail-row">
                                            <i className="fas fa-book"></i>
                                            <span>{detection.course_code || 'N/A'}</span>
                                        </div>
                                        <div className="detail-row">
                                            <i className="fas fa-percentage"></i>
                                            <span className="confidence">
                                                {detection.confidence_score || 0}% Confidence
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <div className="no-detections">
                        <i className="fas fa-inbox"></i>
                        <h3>No Recent Detections</h3>
                        <p>Waiting for camera activity...</p>
                        <div className="pulse-indicator">
                            <div className="pulse-dot"></div>
                            <span>Monitoring</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default LiveDetectionPage;
