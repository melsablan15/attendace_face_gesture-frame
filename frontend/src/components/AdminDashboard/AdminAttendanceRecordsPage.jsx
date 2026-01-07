import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AdminAttendanceRecordsPage.css';

const AdminAttendanceRecordsPage = () => {
    // --- STATES ---
    const [records, setRecords] = useState([]);
    const [filteredRecords, setFilteredRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [filterType, setFilterType] = useState("All");
    const [dateFilter, setDateFilter] = useState("");
    const [userFilter, setUserFilter] = useState("");
    const [selectedRecord, setSelectedRecord] = useState(null);
    const [showModal, setShowModal] = useState(false);

    // --- INITIAL LOAD ---
    useEffect(() => {
        fetchAttendanceRecords();
    }, []);

    // --- FETCH ATTENDANCE RECORDS ---
    const fetchAttendanceRecords = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.get('http://localhost:5000/api/admin/attendance-records');
            setRecords(response.data);
            setFilteredRecords(response.data);
        } catch (err) {
            setError('Failed to load attendance records: ' + err.message);
            console.error('Error fetching records:', err);
        } finally {
            setLoading(false);
        }
    };

    // --- APPLY FILTERS ---
    useEffect(() => {
        let filtered = records;

        // Search filter
        if (searchTerm) {
            filtered = filtered.filter(r =>
                r.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                r.user_id?.toString().includes(searchTerm) ||
                r.course_code?.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Event type filter
        if (filterType !== "All") {
            filtered = filtered.filter(r => r.event_type === filterType);
        }

        // Date filter
        if (dateFilter) {
            filtered = filtered.filter(r => {
                const recordDate = new Date(r.timestamp).toLocaleDateString();
                return recordDate === new Date(dateFilter).toLocaleDateString();
            });
        }

        // User role filter
        if (userFilter !== "") {
            filtered = filtered.filter(r => r.user_role === userFilter);
        }

        setFilteredRecords(filtered);
    }, [searchTerm, filterType, dateFilter, userFilter, records]);

    // --- OPEN RECORD DETAILS ---
    const viewRecordDetails = (record) => {
        setSelectedRecord(record);
        setShowModal(true);
    };

    // --- CLOSE MODAL ---
    const closeModal = () => {
        setShowModal(false);
        setSelectedRecord(null);
    };

    // --- FORMAT TIMESTAMP ---
    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleString();
    };

    // --- GET EVENT ICON & COLOR ---
    const getEventStyle = (eventType) => {
        switch (eventType) {
            case 'attendance_in':
                return { icon: 'fas fa-sign-in-alt', color: 'green', label: 'Attendance In' };
            case 'attendance_out':
                return { icon: 'fas fa-sign-out-alt', color: 'orange', label: 'Attendance Out' };
            case 'break_in':
                return { icon: 'fas fa-pause-circle', color: 'blue', label: 'Break In' };
            case 'break_out':
                return { icon: 'fas fa-play-circle', color: 'purple', label: 'Break Out' };
            default:
                return { icon: 'fas fa-clock', color: 'grey', label: 'Event' };
        }
    };

    // --- GET ROLE BADGE COLOR ---
    const getRoleBadgeColor = (role) => {
        switch (role?.toLowerCase()) {
            case 'student':
                return 'badge-student';
            case 'faculty':
                return 'badge-faculty';
            case 'admin':
                return 'badge-admin';
            default:
                return 'badge-default';
        }
    };

    // --- STATISTICS ---
    const statistics = {
        totalRecords: records.length,
        todayRecords: records.filter(r => new Date(r.timestamp).toDateString() === new Date().toDateString()).length,
        attendanceIn: records.filter(r => r.event_type === 'attendance_in').length,
        attendanceOut: records.filter(r => r.event_type === 'attendance_out').length,
    };

    // --- RENDER ---
    return (
        <div className="admin-attendance-container">
            {/* HEADER */}
            <div className="attendance-page-header">
                <h1><i className="fas fa-video"></i> Camera Attendance Records</h1>
                <p>View all attendance records captured from camera</p>
            </div>

            {/* STATISTICS */}
            <div className="attendance-stats-grid">
                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#667eea' }}>
                        <i className="fas fa-video"></i>
                    </div>
                    <div className="stat-content">
                        <div className="stat-value">{statistics.totalRecords}</div>
                        <div className="stat-label">Total Records</div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#28a745' }}>
                        <i className="fas fa-sign-in-alt"></i>
                    </div>
                    <div className="stat-content">
                        <div className="stat-value">{statistics.attendanceIn}</div>
                        <div className="stat-label">Check-Ins</div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#ff9800' }}>
                        <i className="fas fa-sign-out-alt"></i>
                    </div>
                    <div className="stat-content">
                        <div className="stat-value">{statistics.attendanceOut}</div>
                        <div className="stat-label">Check-Outs</div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#f44336' }}>
                        <i className="fas fa-calendar-today"></i>
                    </div>
                    <div className="stat-content">
                        <div className="stat-value">{statistics.todayRecords}</div>
                        <div className="stat-label">Today's Records</div>
                    </div>
                </div>
            </div>

            {/* ERROR ALERT */}
            {error && (
                <div className="alert-error">
                    <i className="fas fa-exclamation-circle"></i> {error}
                    <button onClick={fetchAttendanceRecords}>Retry</button>
                </div>
            )}

            {/* FILTERS */}
            <div className="attendance-filters">
                <div className="filter-group">
                    <label><i className="fas fa-search"></i> Search</label>
                    <input
                        type="text"
                        placeholder="Search by name, ID, or course code..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="filter-input"
                    />
                </div>

                <div className="filter-group">
                    <label><i className="fas fa-filter"></i> Event Type</label>
                    <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="filter-select"
                    >
                        <option>All</option>
                        <option value="attendance_in">Check-In</option>
                        <option value="attendance_out">Check-Out</option>
                        <option value="break_in">Break In</option>
                        <option value="break_out">Break Out</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label><i className="fas fa-calendar"></i> Date</label>
                    <input
                        type="date"
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value)}
                        className="filter-input"
                    />
                </div>

                <div className="filter-group">
                    <label><i className="fas fa-users"></i> User Type</label>
                    <select
                        value={userFilter}
                        onChange={(e) => setUserFilter(e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Types</option>
                        <option value="Student">Students</option>
                        <option value="Faculty">Faculty</option>
                        <option value="Admin">Admins</option>
                    </select>
                </div>

                <button
                    className="btn-refresh"
                    onClick={() => {
                        setSearchTerm("");
                        setFilterType("All");
                        setDateFilter("");
                        setUserFilter("");
                        fetchAttendanceRecords();
                    }}
                >
                    <i className="fas fa-redo"></i> Reset
                </button>
            </div>

            {/* RECORDS TABLE */}
            <div className="attendance-records-section">
                {loading ? (
                    <div className="loading-spinner">
                        <div className="spinner"></div>
                        <p>Loading attendance records...</p>
                    </div>
                ) : filteredRecords.length > 0 ? (
                    <div className="records-container">
                        <div className="records-table-wrapper">
                            <table className="records-table">
                                <thead>
                                    <tr>
                                        <th><i className="fas fa-user"></i> Name</th>
                                        <th><i className="fas fa-id-card"></i> ID</th>
                                        <th><i className="fas fa-shield-alt"></i> Role</th>
                                        <th><i className="fas fa-book"></i> Course</th>
                                        <th><i className="fas fa-door-open"></i> Event</th>
                                        <th><i className="fas fa-clock"></i> Timestamp</th>
                                        <th><i className="fas fa-chart-line"></i> Confidence</th>
                                        <th><i className="fas fa-eye"></i> Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredRecords.map((record, index) => {
                                        const eventStyle = getEventStyle(record.event_type);
                                        return (
                                            <tr key={index} className="record-row">
                                                <td className="cell-name">
                                                    <div className="name-cell">
                                                        <div className="user-avatar">
                                                            <i className="fas fa-user"></i>
                                                        </div>
                                                        <div className="name-info">
                                                            <div className="name-text">{record.user_name || 'Unknown'}</div>
                                                            <div className="room-text">{record.room_name || 'TBA'}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="cell-id">{record.user_id}</td>
                                                <td className="cell-role">
                                                    <span className={`badge ${getRoleBadgeColor(record.user_role)}`}>
                                                        {record.user_role || 'N/A'}
                                                    </span>
                                                </td>
                                                <td className="cell-course">{record.course_code || 'TBA'}</td>
                                                <td className="cell-event">
                                                    <div className={`event-badge event-${eventStyle.color}`}>
                                                        <i className={eventStyle.icon}></i> {eventStyle.label}
                                                    </div>
                                                </td>
                                                <td className="cell-timestamp">{formatTime(record.timestamp)}</td>
                                                <td className="cell-confidence">
                                                    <div className={`confidence-bar ${record.confidence_score >= 90 ? 'high' : record.confidence_score >= 70 ? 'medium' : 'low'}`}>
                                                        <span>{record.confidence_score || 0}%</span>
                                                    </div>
                                                </td>
                                                <td className="cell-actions">
                                                    <button
                                                        className="btn-view"
                                                        onClick={() => viewRecordDetails(record)}
                                                        title="View details"
                                                    >
                                                        <i className="fas fa-expand"></i>
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                        <div className="records-footer">
                            <p>Showing {filteredRecords.length} of {records.length} records</p>
                        </div>
                    </div>
                ) : (
                    <div className="no-records">
                        <i className="fas fa-inbox"></i>
                        <p>No attendance records found</p>
                        <small>Try adjusting your filters</small>
                    </div>
                )}
            </div>

            {/* DETAIL MODAL */}
            {showModal && selectedRecord && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Attendance Record Details</h2>
                            <button className="modal-close" onClick={closeModal}>
                                <i className="fas fa-times"></i>
                            </button>
                        </div>

                        <div className="modal-body">
                            {/* CAPTURED IMAGE */}
                            {selectedRecord.face_data && (
                                <div className="detail-section">
                                    <h3>Captured Image</h3>
                                    <div className="captured-image-container">
                                        <img
                                            src={selectedRecord.face_data}
                                            alt="Captured"
                                            className="captured-image-modal"
                                        />
                                    </div>
                                </div>
                            )}

                            {/* USER INFORMATION */}
                            <div className="detail-section">
                                <h3>User Information</h3>
                                <div className="detail-grid">
                                    <div className="detail-item">
                                        <label>Name</label>
                                        <p>{selectedRecord.user_name || 'Unknown'}</p>
                                    </div>
                                    <div className="detail-item">
                                        <label>User ID</label>
                                        <p>{selectedRecord.user_id}</p>
                                    </div>
                                    <div className="detail-item">
                                        <label>Role</label>
                                        <p><span className={`badge ${getRoleBadgeColor(selectedRecord.user_role)}`}>
                                            {selectedRecord.user_role || 'N/A'}
                                        </span></p>
                                    </div>
                                    <div className="detail-item">
                                        <label>Department</label>
                                        <p>{selectedRecord.department || 'N/A'}</p>
                                    </div>
                                </div>
                            </div>

                            {/* ATTENDANCE DETAILS */}
                            <div className="detail-section">
                                <h3>Attendance Details</h3>
                                <div className="detail-grid">
                                    <div className="detail-item">
                                        <label>Event Type</label>
                                        <p>
                                            <span className={`event-badge event-${getEventStyle(selectedRecord.event_type).color}`}>
                                                <i className={getEventStyle(selectedRecord.event_type).icon}></i>{' '}
                                                {getEventStyle(selectedRecord.event_type).label}
                                            </span>
                                        </p>
                                    </div>
                                    <div className="detail-item">
                                        <label>Timestamp</label>
                                        <p>{formatTime(selectedRecord.timestamp)}</p>
                                    </div>
                                    <div className="detail-item">
                                        <label>Course</label>
                                        <p>{selectedRecord.course_code || 'TBA'}</p>
                                    </div>
                                    <div className="detail-item">
                                        <label>Room</label>
                                        <p>{selectedRecord.room_name || 'TBA'}</p>
                                    </div>
                                    <div className="detail-item">
                                        <label>Confidence Score</label>
                                        <p>
                                            <span className={`confidence-badge ${selectedRecord.confidence_score >= 90 ? 'high' : selectedRecord.confidence_score >= 70 ? 'medium' : 'low'}`}>
                                                {selectedRecord.confidence_score || 0}%
                                            </span>
                                        </p>
                                    </div>
                                    <div className="detail-item">
                                        <label>Remarks</label>
                                        <p>{selectedRecord.remarks || 'No remarks'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="modal-footer">
                            <button className="btn-close" onClick={closeModal}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminAttendanceRecordsPage;
