import pdfplumber
import re
import os
from datetime import datetime
import cv2
import mysql.connector
import numpy as np
import base64
import pickle
import json
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from db_config import DB_CONFIG
from deepface import DeepFace

# --- 🛠️ CRITICAL FIX FOR INTEL GPU CRASH ---
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# --- 1. SETUP MODELS ---
# Using SFace as it is faster and lightweight
MODEL_NAME = "SFace" 
DETECTOR_BACKEND = "opencv"

print("⏳ Initializing DeepFace Models...")
try:
    DeepFace.build_model(MODEL_NAME)
    print("✅ DeepFace models loaded successfully!")
except Exception as e:
    print(f"❌ Warning: Could not load DeepFace models: {e}")

app = Flask(__name__)
# Allow ALL routes
CORS(app, resources={r"/*": {"origins": "*"}}) 

# --- DB HELPER ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"❌ DB Error: {err}")
        return None

# --- FACE MATCHING/RECOGNITION ---
def find_matching_user(face_embedding_data):
    """
    Compare captured face embedding with all registered faces in database
    Uses Normalized Euclidean Distance
    """
    if not face_embedding_data:
        return None
    
    try:
        # 1. Load captured vector
        captured_vector = pickle.loads(face_embedding_data)[0]
        captured_vector = np.array(captured_vector)

        # 2. Normalize Captured Vector (Scale to length of 1.0)
        norm = np.linalg.norm(captured_vector)
        if norm != 0:
            captured_vector = captured_vector / norm
        
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        # 3. SELECT ONLY NEW DATA (Ignore old VGG columns)
        cursor.execute("""
            SELECT user_id, face_data 
            FROM User 
            WHERE face_data IS NOT NULL
        """)

        registered_users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        best_match_id = None
        best_distance = float('inf')
        threshold = 0.80  # Threshold for SFace/Normalized vectors
        
        print(f"\n🔍 Comparing against {len(registered_users)} registered users...")

        for user in registered_users:
            try:
                # 4. Load & Normalize Stored Vector
                if not user['face_data']: continue
                
                stored_vectors = pickle.loads(user['face_data'])
                stored_vector = np.array(stored_vectors[0])

                db_norm = np.linalg.norm(stored_vector)
                if db_norm != 0:
                    stored_vector = stored_vector / db_norm
                
                # 5. Calculate Euclidean Distance
                distance = np.linalg.norm(captured_vector - stored_vector)
                
                print(f"   User {user['user_id']}: Distance = {distance:.4f}")
                
                if distance < best_distance:
                    best_distance = distance
                    best_match_id = user['user_id']

            except Exception as e:
                # Skip corrupt data silently
                continue
        
        # 6. Final Match Decision
        if best_match_id and best_distance < threshold:
            print(f"✅ Face matched! User ID: {best_match_id} (Distance: {best_distance:.4f})")
            return best_match_id
        else:
            print(f"⚠️ No matching face found (Best distance: {best_distance:.4f})")
            return None
            
    except Exception as e:
        print(f"❌ Error in face matching: {e}")
        return None

# --- FACE PROCESSING ---
def process_face_embedding(face_capture_data_url):
    print("\n🔍 Processing Face Embedding...") 

    if not face_capture_data_url:
        print("⚠️ No face capture data received.")
        return None, "Pending"

    try:
        # Decode base64
        if ',' in face_capture_data_url:
            header, encoded_data = face_capture_data_url.split(',', 1)
        else:
            encoded_data = face_capture_data_url
            
        image_data = base64.b64decode(encoded_data)
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None: 
            print("❌ Error: Could not decode image.")
            return None, "Not Registered"

        # Generate Embedding
        embedding_objs = DeepFace.represent(
            img_path = frame, 
            model_name = MODEL_NAME,
            enforce_detection = False, 
            detector_backend = DETECTOR_BACKEND
        )
        
        if len(embedding_objs) >= 1:
            face_vector = embedding_objs[0]["embedding"]
            # Save as list [vector]
            data_to_save = pickle.dumps([face_vector]) 
            print("✅ Embedding generated successfully!")
            return data_to_save, "Registered"
        
        print("⚠️ DeepFace returned 0 embeddings.")
        return None, "Not Registered"

    except Exception as e:
        print(f"❌ CRITICAL ERROR in process_face_embedding: {e}")
        return None, "Not Registered"

# ==========================================
# API: CHECK FACE (For Validation Box)
# ==========================================
@app.route('/validate-face', methods=['POST'])
def validate_face():
    data = request.json
    face_capture = data.get('faceCapture')
    
    if not face_capture:
        return jsonify({"valid": False, "message": "No image data"}), 400

    try:
        if ',' in face_capture:
            header, encoded_data = face_capture.split(',', 1)
        else:
            encoded_data = face_capture
            
        image_data = base64.b64decode(encoded_data)
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        DeepFace.extract_faces(
            img_path=frame, 
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=True, 
            align=False
        )
        
        return jsonify({"valid": True, "message": "Face Detected!"}), 200

    except Exception as e:
        return jsonify({"valid": False, "message": "No face detected. Center your face."}), 200

# ==========================================
# API: LOGIN
# ==========================================
@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True) 

    try:
        sql = "SELECT * FROM User WHERE email = %s"
        cursor.execute(sql, (email,))
        user = cursor.fetchone()

        if user:
            stored_hash = user['password_hash']
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                del user['password_hash'] 
                # Remove heavy blobs from response
                del user['face_embedding_vgg'] 
                del user['face_data']
                
                # Fix Date formats
                for date_field in ['birthday', 'date_registered', 'last_active']:
                    if user.get(date_field): 
                        user[date_field] = str(user[date_field])

                print(f"✅ Login Successful for: {user['firstName']}")
                return jsonify({"message": "Login Successful", "user": user}), 200
            else:
                return jsonify({"error": "Invalid email or password"}), 401
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        print(f"❌ Login Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# API: GET USER PROFILE
# ==========================================
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True) 

    try:
        sql = "SELECT * FROM User WHERE user_id = %s"
        cursor.execute(sql, (user_id,))
        user = cursor.fetchone()

        if user:
            for key, value in user.items():
                if key in ['handled_sections', 'enrolled_courses', 'emergency_contact', 'preferences']:
                    if value and isinstance(value, str):
                        try:
                            user[key] = json.loads(value)
                        except:
                            user[key] = [] 
                    elif value is None:
                        user[key] = []

                if hasattr(value, 'isoformat'): 
                    user[key] = value.isoformat()
            
            user.pop('password_hash', None)
            user.pop('face_embedding_vgg', None)
            user.pop('face_data', None)
            
            return jsonify(user), 200
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# API: UPDATE PROFILE
# ==========================================
@app.route('/user/update/<int:user_id>', methods=['PUT'])
def update_user_profile(user_id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()

    try:
        emergency_contact = json.dumps(data.get('emergency_contact', {}))
        
        sql = """
            UPDATE User SET 
                firstName = %s, lastName = %s, contactNumber = %s, birthday = %s,
                homeAddress = %s, street_number = %s, street_name = %s,
                barangay = %s, city = %s, zip_code = %s, emergency_contact = %s
            WHERE user_id = %s
        """
        
        vals = (
            data.get('firstName'), data.get('lastName'), data.get('contactNumber'),
            data.get('birthday'), data.get('homeAddress'), data.get('street_number'),
            data.get('street_name'), data.get('barangay'), data.get('city'),
            data.get('zip_code'), emergency_contact, user_id
        )

        cursor.execute(sql, vals)
        conn.commit()

        print(f"✅ User {user_id} Updated Successfully")
        return jsonify({"message": "Profile updated successfully!"}), 200

    except Exception as e:
        print(f"❌ Update Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# API: PASSWORD MANAGEMENT
# ==========================================
@app.route('/user/verify-password', methods=['POST'])
def verify_password():
    data = request.json
    user_id = data.get('user_id')
    password_input = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT password_hash FROM User WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            stored_hash = user['password_hash']
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            
            if bcrypt.checkpw(password_input.encode('utf-8'), stored_hash):
                return jsonify({"valid": True}), 200
            else:
                return jsonify({"valid": False, "error": "Incorrect password"}), 401
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/user/change-password', methods=['PUT'])
def change_password():
    data = request.json
    user_id = data.get('user_id')
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({"error": "Password is required"}), 400

    hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE User SET password_hash = %s WHERE user_id = %s", (hashed_pw, user_id))
        conn.commit()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# API: REGISTER (FIXED: Saves to face_data)
# ==========================================
@app.route('/register', methods=['POST']) 
def register_user():
    data = request.json
    print(f"\n📩 Registering: {data.get('firstName')} {data.get('lastName')}")
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()

    try:
        role = data.get('role')
        email = data.get('email')
        password = data.get('password')
        
        tupm_id = f"TUPM-{data.get('tupmYear')}-{data.get('tupmSerial')}"
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Process face embedding
        face_blob, face_status = process_face_embedding(data.get('faceCapture'))

        # Auto-verify admins
        verification_status = 'Verified' if role == 'admin' else 'Pending'

        handled_sections = json.dumps(data.get('handledSections', []))
        enrolled_courses = json.dumps(data.get('selectedCourses', []))
        
        full_addr = f"{data.get('streetNumber')} {data.get('streetName')}, {data.get('barangay')}, {data.get('city')}, {data.get('zipCode')}"

        # FIX: Insert into `face_data` (new column) instead of `face_embedding_vgg`
        sql = """
            INSERT INTO User (
                email, password_hash, role, tupm_id,
                firstName, lastName, middleName, birthday, contactNumber,
                street_number, street_name, barangay, city, zip_code, homeAddress,
                college, course, year_level, section, student_status, term, faculty_status,
                handled_sections, enrolled_courses,
                face_data, face_status, verification_status, 
                last_active, date_registered
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, 
                NOW(), NOW()
            )
        """

        val = (
            email, hashed_pw, role, tupm_id,
            data.get('firstName'), data.get('lastName'), data.get('middleName'), data.get('birthday'), data.get('contactNumber'),
            data.get('streetNumber'), data.get('streetName'), data.get('barangay'), data.get('city'), data.get('zipCode'), full_addr,
            data.get('college'), data.get('courseCode'), data.get('year'), data.get('section'), 
            data.get('status'), data.get('term'), data.get('facultyStatus'),
            handled_sections, enrolled_courses,
            face_blob, face_status, verification_status  
        )

        cursor.execute(sql, val)
        conn.commit()
        user_id = cursor.lastrowid
        
        print(f"✅ Success! User {user_id} registered. Face saved to 'face_data'.")
        return jsonify({"message": "Registration Successful!", "user_id": user_id}), 201

    except mysql.connector.Error as err:
        if err.errno == 1062:
            return jsonify({"error": "Email or TUPM ID already exists."}), 409
        print(f"❌ SQL Error: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        print(f"❌ General Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# ADMIN VERIFICATION APIs
# ==========================================
@app.route('/admin/verification/list', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True) 

    try:
        sql = """
        SELECT user_id, firstName, lastName, email, role, 
               college, course, tupm_id, date_registered, verification_status 
        FROM User ORDER BY date_registered DESC
        """
        cursor.execute(sql)
        users = cursor.fetchall()
        for user in users:
            if user.get('date_registered'): user['date_registered'] = str(user['date_registered'])
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/verification/approve', methods=['POST'])
def approve_user_verification():
    data = request.json
    user_id = data.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE User SET verification_status = 'Verified' WHERE user_id = %s", (user_id,))
        conn.commit()
        return jsonify({"message": "User verified"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/verification/reject', methods=['POST'])
def reject_user_verification():
    data = request.json
    user_id = data.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE User SET verification_status = 'Rejected' WHERE user_id = %s", (user_id,))
        conn.commit()
        return jsonify({"message": "User rejected"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/user-delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM User WHERE user_id = %s", (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# STUDENT APIs
# ==========================================
@app.route('/api/student/dashboard/<int:user_id>', methods=['GET'])
def get_student_dashboard(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT enrolled_courses, verification_status FROM User WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        if not user_data or user_data.get('verification_status') != 'Verified':
             return jsonify({"attendance_rate": "N/A", "enrolled_courses": 0, "notifications": [], "recent_attendance": []})

        cursor.execute("SELECT COUNT(*) as count FROM EventLog WHERE user_id = %s AND event_type = 'attendance_in'", (user_id,))
        total_attendance = cursor.fetchone()['count']
        
        course_count = 0
        if user_data['enrolled_courses']:
            try:
                courses = json.loads(user_data['enrolled_courses'])
                course_count = len(courses)
            except: course_count = 0

        cursor.execute("SELECT * FROM Notification WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (user_id,))
        notifications = cursor.fetchall()
        
        # FIXED: CameraManagement table
        cursor.execute("""
            SELECT e.timestamp, s.subject_description as course_name, cm.room_name 
            FROM EventLog e 
            LEFT JOIN CameraManagement cm ON e.camera_id = cm.camera_id
            LEFT JOIN ClassSchedule c ON c.camera_id = e.camera_id 
            LEFT JOIN Subjects s ON c.course_code = s.subject_code
            WHERE e.user_id = %s AND e.event_type = 'attendance_in'
            ORDER BY e.timestamp DESC LIMIT 3
        """, (user_id,))
        recent_logs = cursor.fetchall()

        return jsonify({
            "attendance_rate": f"{min(total_attendance * 10, 100)}%",
            "enrolled_courses": course_count,
            "notifications": notifications,
            "recent_attendance": recent_logs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/schedule/<int:user_id>', methods=['GET'])
def get_student_schedule(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT section, enrolled_courses FROM User WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result or not result['enrolled_courses']: return jsonify([])

        section = result['section']
        enrolled_list = json.loads(result['enrolled_courses']) if isinstance(result['enrolled_courses'], str) else result['enrolled_courses']
        
        format_strings = ','.join(['%s'] * len(enrolled_list))
        # FIXED: CameraManagement table
        sql = f"""
            SELECT cs.day_of_week, cs.start_time, cs.end_time, s.subject_description as course_name, 
                   cs.course_code, cm.room_name
            FROM ClassSchedule cs
            LEFT JOIN CameraManagement cm ON cs.camera_id = cm.camera_id
            JOIN Subjects s ON cs.course_code = s.subject_code
            WHERE cs.section = %s AND cs.course_code IN ({format_strings})
            ORDER BY cs.start_time
        """
        params = [section] + enrolled_list
        cursor.execute(sql, tuple(params))
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/history/<int:user_id>', methods=['GET'])
def get_attendance_history(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # FIXED: CameraManagement table
        sql = """
            SELECT e.timestamp, e.event_type, e.confidence_score, cm.room_name, e.remarks, s.subject_description as course_name
            FROM EventLog e
            LEFT JOIN CameraManagement cm ON e.camera_id = cm.camera_id
            LEFT JOIN ClassSchedule cs ON e.camera_id = cs.camera_id
            LEFT JOIN Subjects s ON cs.course_code = s.subject_code
            WHERE e.user_id = %s
            ORDER BY e.timestamp DESC
        """
        cursor.execute(sql, (user_id,))
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# FACULTY & DEPT HEAD APIs
# ==========================================
@app.route('/api/dept/management-data', methods=['GET'])
def get_management_data():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # FIXED: CameraManagement table
        sql_courses = """
            SELECT s.subject_id, s.subject_code, s.subject_description as name, s.units,
                   cs.schedule_id, cs.section, cs.day_of_week, cs.start_time, cs.end_time, cm.room_name,
                   CONCAT(u.firstName, ' ', u.lastName) as assigned_faculty, u.user_id as faculty_id
            FROM Subjects s
            LEFT JOIN ClassSchedule cs ON s.subject_code = cs.course_code
            LEFT JOIN User u ON cs.faculty_id = u.user_id
            LEFT JOIN CameraManagement cm ON cs.camera_id = cm.camera_id
            ORDER BY s.created_at DESC
        """
        cursor.execute(sql_courses)
        courses = cursor.fetchall()
        for c in courses:
            c['schedule'] = f"{c['day_of_week']} {c['start_time']} - {c['end_time']}" if c['day_of_week'] else None

        cursor.execute("SELECT user_id, CONCAT(firstName, ' ', lastName) as name FROM User WHERE role = 'faculty'")
        faculty = cursor.fetchall()

        cursor.execute("SELECT camera_id, room_name FROM CameraManagement")
        rooms = cursor.fetchall()

        return jsonify({"courses": courses, "faculty": faculty, "rooms": rooms})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================================
# ATTENDANCE & RECORDING APIs (CRITICAL FIXES HERE)
# ==========================================
@app.route('/api/attendance/record', methods=['POST'])
def record_attendance():
    """
    Record attendance with automatic face recognition
    """
    try:
        face_capture = request.form.get('face_capture')
        user_id = request.form.get('user_id')
        event_type = request.form.get('event_type', 'attendance_in')
        timestamp_str = request.form.get('timestamp')
        schedule_id = request.form.get('schedule_id')

        if not face_capture:
            return jsonify({"error": "Missing face_capture"}), 400

        try:
            event_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.now()
        except:
            event_timestamp = datetime.now()

        print(f"\n📸 Recording Attendance via Face Recognition...")

        # Process face embedding
        face_embedding, face_status = process_face_embedding(face_capture)

        # 🔍 FIX: Check matched_user_id correctly
        if not user_id and face_embedding:
            print("🔍 Matching face against registered users...")
            # FIXED: Was 'face_embedding_vgg' (undefined), changed to 'face_embedding'
            matched_user_id = find_matching_user(face_embedding)
            if matched_user_id:
                user_id = matched_user_id
            else:
                return jsonify({"error": "Face not recognized. Please register first."}), 404

        if not user_id:
            return jsonify({"error": "Could not identify user"}), 400

        conn = get_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("SELECT user_id, firstName, lastName, role FROM User WHERE user_id = %s", (user_id,))
            user_info = cursor.fetchone()
            
            if not user_info:
                return jsonify({"error": "User not found"}), 404

            room_name = "TBA"
            course_code = "TBA"
            camera_id = None
            
            if schedule_id:
                # FIXED: Changed 'ClassRoom' to 'CameraManagement'
                cursor.execute("""
                    SELECT cs.course_code, cm.room_name, cs.camera_id 
                    FROM ClassSchedule cs
                    LEFT JOIN CameraManagement cm ON cs.camera_id = cm.camera_id
                    WHERE cs.schedule_id = %s
                """, (schedule_id,))
                schedule_info = cursor.fetchone()
                if schedule_info:
                    course_code = schedule_info['course_code'] or course_code
                    room_name = schedule_info['room_name'] or room_name
                    camera_id = schedule_info['camera_id']

            # Insert event log
            confidence_score = 95.0 if face_embedding else 0.0
            remarks = "On Time" if event_type == "attendance_in" else "Noted"
            
            cursor.execute("""
                INSERT INTO EventLog 
                (user_id, event_type, timestamp, camera_id, confidence_score, remarks)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, event_type, event_timestamp, camera_id, confidence_score, remarks))

            conn.commit()

            # Notification
            user_name = f"{user_info['firstName']} {user_info['lastName']}"
            notif_msg = f"Attendance {event_type} recorded for {course_code} at {event_timestamp.strftime('%H:%M')}"
            cursor.execute("INSERT INTO Notification (user_id, icon, message, is_read) VALUES (%s, 'fas fa-check-circle', %s, FALSE)", (user_id, notif_msg))
            conn.commit()

            print(f"✅ Attendance recorded for {user_name}")
            return jsonify({
                "message": f"✅ Attendance recorded for {user_name}",
                "user_id": user_id,
                "user_name": user_name,
                "event_type": event_type,
                "room_name": room_name
            }), 200

        except Exception as e:
            conn.rollback()
            print(f"❌ Error recording attendance: {e}")
            return jsonify({"error": f"Failed to record: {str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/attendance/live-status/<int:user_id>', methods=['GET'])
def get_live_attendance_status(user_id):
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # FIXED: Changed 'ClassRoom' to 'CameraManagement'
        cursor.execute("""
            SELECT e.event_type, e.timestamp, e.confidence_score, cs.course_code, cm.room_name
            FROM EventLog e
            LEFT JOIN ClassSchedule cs ON e.camera_id = cs.camera_id
            LEFT JOIN CameraManagement cm ON cs.camera_id = cm.camera_id
            WHERE e.user_id = %s 
            AND e.timestamp >= DATE_SUB(NOW(), INTERVAL 4 HOUR)
            ORDER BY e.timestamp DESC LIMIT 1
        """, (user_id,))

        latest_event = cursor.fetchone()
        cursor.close()
        conn.close()

        if not latest_event:
            return jsonify({"status": "IDLE", "message": "No recent activity"}), 200

        return jsonify({
            "status": latest_event['event_type'],
            "timestamp": latest_event['timestamp'].isoformat() if latest_event['timestamp'] else None,
            "room_name": latest_event['room_name'],
            "message": f"Last recorded: {latest_event['event_type']}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/attendance-records', methods=['GET'])
def get_all_attendance_records():
    try:
        days = request.args.get('days', 30, type=int)
        conn = get_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # FIXED: Changed 'ClassRoom' to 'CameraManagement' AND event_id to log_id
        # FIXED: Removed u.department (column doesn't exist)
        query = """
            SELECT e.log_id, e.user_id, e.event_type, e.timestamp, e.confidence_score, e.remarks,
                   u.firstName, u.lastName, u.role as user_role, u.college,
                   cs.course_code, cm.room_name
            FROM EventLog e
            LEFT JOIN User u ON e.user_id = u.user_id
            LEFT JOIN ClassSchedule cs ON e.camera_id = cs.camera_id
            LEFT JOIN CameraManagement cm ON e.camera_id = cm.camera_id
            WHERE e.timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY e.timestamp DESC
        """
        cursor.execute(query, (days,))
        records = cursor.fetchall()
        
        processed_records = []
        for record in records:
            processed_record = {
                "log_id": record['log_id'],
                "user_id": record['user_id'],
                "user_name": f"{record['firstName'] or ''} {record['lastName'] or ''}".strip() or "Unknown",
                "user_role": record['user_role'],
                "college": record.get('college', 'N/A'),
                "event_type": record['event_type'],
                "timestamp": record['timestamp'].isoformat() if record['timestamp'] else None,
                "confidence_score": int(record['confidence_score']) if record['confidence_score'] else 0,
                "remarks": record['remarks'],
                "course_code": record['course_code'],
                "room_name": record['room_name'],
                "face_data": None  # We'll set this below if face_data exists in EventLog
            }
            processed_records.append(processed_record)

        cursor.close()
        conn.close()
        
        print(f"✅ Retrieved {len(processed_records)} attendance records")
        if len(processed_records) > 0:
            print(f"   Latest: {processed_records[0]['user_name']} at {processed_records[0]['timestamp']}")
        
        return jsonify(processed_records), 200

    except Exception as e:
        print(f"❌ Error retrieving attendance records: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)