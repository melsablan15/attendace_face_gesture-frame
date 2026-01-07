import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './LiveDetectionPage.css';

const LiveDetectionPage = () => {
    const [detections, setDetections] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(new Date());
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [scanning, setScanning] = useState(false);
    const [timeFilter, setTimeFilter] = useState(24); // hours

    // Fetch recent detections
    const fetchDetections = async () => {
        try {
            setScanning(true);
            
            console.log('🔄 Fetching attendance records...');
            
            // Get records from configurable time period
            const days = Math.ceil(timeFilter / 24);
            const response = await axios.get('http://localhost:5000/api/admin/attendance-records', {
                params: { days: days }
            });
            
            console.log(`📊 API returned ${response.data.length} total records`);
            
            // Filter based on selected time period
            const filterTime = new Date(Date.now() - timeFilter * 60 * 60 * 1000);
            const recentDetections = response.data.filter(record => {
                const recordTime = new Date(record.timestamp);
                return recordTime > filterTime;
            });
            
            console.log(`✅ Found ${recentDetections.length} detections in last ${timeFilter} hours`);
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
    }, [autoRefresh, timeFilter]);

    // Format time (show seconds for real-time feeling)
    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    // Format date with day
    const formatDate = (timestamp) => {
        return new Date(timestamp).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
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
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
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
                    <div className="time-filter-selector">
                        <label>Show: </label>
                        <select 
                            value={timeFilter} 
                            onChange={(e) => setTimeFilter(Number(e.target.value))}
                            className="time-filter-dropdown"
                        >
                            <option value={1}>Last Hour</option>
                            <option value={2}>Last 2 Hours</option>
                            <option value={6}>Last 6 Hours</option>
                            <option value={12}>Last 12 Hours</option>
                            <option value={24}>Last 24 Hours</option>
                            <option value={48}>Last 2 Days</option>
                            <option value={168}>Last Week</option>
                        </select>
                    </div>
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
                        <div className="stat-label">Detected ({timeFilter}h)</div>
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
                <div className="stat-item">
                    <i className="fas fa-sign-out-alt"></i>
                    <div>
                        <div className="stat-value">
                            {detections.filter(d => d.event_type === 'attendance_out').length}
                        </div>
                        <div className="stat-label">Check-Outs</div>
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
                        <p>Loading detection records...</p>
                    </div>
                ) : detections.length > 0 ? (
                    <div className="records-list-container">
                        <div className="records-count-badge">
                            <i className="fas fa-database"></i>
                            Showing {detections.length} record{detections.length !== 1 ? 's' : ''} from EventLog table
                        </div>
                        <table className="detection-records-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Name</th>
                                    <th>Role</th>
                                    <th>Event</th>
                                    <th>Date</th>
                                    <th>Time</th>
                                    <th>Room</th>
                                    <th>Confidence</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {detections.map((detection, index) => {
                                    const eventStyle = getEventStyle(detection.event_type);
                                    const isRecent = (new Date() - new Date(detection.timestamp)) < 30000;
                                    const isToday = new Date(detection.timestamp).toDateString() === new Date().toDateString();
                                    
                                    return (
                                        <tr key={index} className={`record-row ${isRecent ? 'recent-record' : ''}`}>
                                            <td className="cell-number">{index + 1}</td>
                                            <td className="cell-name">
                                                <div className="name-with-avatar">
                                                    <div className="avatar-circle">
                                                        <i className="fas fa-user"></i>
                                                    </div>
                                                    <span className="name-text">{detection.user_name || 'Unknown'}</span>
                                                    {isRecent && (
                                                        <span className="new-indicator">NEW</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="cell-role">
                                                <span className={`role-badge role-${detection.user_role?.toLowerCase() || 'default'}`}>
                                                    {detection.user_role === 'student' && <i className="fas fa-user-graduate"></i>}
                                                    {detection.user_role === 'faculty' && <i className="fas fa-chalkboard-teacher"></i>}
                                                    {detection.user_role === 'admin' && <i className="fas fa-user-shield"></i>}
                                                    {detection.user_role || 'N/A'}
                                                </span>
                                            </td>
                                            <td className="cell-event">
                                                <div className="event-indicator" style={{ backgroundColor: eventStyle.color }}>
                                                    <i className={eventStyle.icon}></i>
                                                    <span>{eventStyle.label}</span>
                                                </div>
                                            </td>
                                            <td className="cell-date">
                                                <div className="date-info">
                                                    <span className={isToday ? 'date-today' : 'date-past'}>
                                                        {isToday ? 'Today' : formatDate(detection.timestamp)}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="cell-time">
                                                <div className="time-info">
                                                    <span className="time-main">{formatTime(detection.timestamp)}</span>
                                                    <span className="time-ago">{getTimeAgo(detection.timestamp)}</span>
                                                </div>
                                            </td>
                                            <td className="cell-room">{detection.room_name || 'TBA'}</td>
                                            <td className="cell-confidence">
                                                <div className="confidence-bar">
                                                    <div 
                                                        className="confidence-fill" 
                                                        style={{ 
                                                            width: `${detection.confidence_score}%`,
                                                            backgroundColor: detection.confidence_score >= 80 ? '#28a745' : 
                                                                           detection.confidence_score >= 60 ? '#ffc107' : '#dc3545'
                                                        }}
                                                    ></div>
                                                    <span className="confidence-text">{detection.confidence_score}%</span>
                                                </div>
                                            </td>
                                            <td className="cell-status">
                                                <span className={`status-badge status-${detection.remarks?.toLowerCase().replace(' ', '-') || 'default'}`}>
                                                    {detection.remarks || 'N/A'}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="no-detections">
                        <i className="fas fa-inbox"></i>
                        <h3>No Recent Detections</h3>
                        <p>No attendance records found in the last {timeFilter} hour{timeFilter !== 1 ? 's' : ''}.</p>
                        <p className="helper-text">Try selecting a longer time period or wait for new detections.</p>
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
