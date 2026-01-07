"""
FRAMES Attendance Kiosk - Backend API
Lightweight backend for standalone attendance capture
"""

import os
from datetime import datetime
import cv2
import mysql.connector
import numpy as np
import base64
import pickle
from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable GPU to avoid crashes
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Initialize DeepFace
MODEL_NAME = "SFace"
DETECTOR_BACKEND = "opencv"

print("⏳ Initializing DeepFace Models...")
try:
    DeepFace.build_model(MODEL_NAME)
    print("✅ DeepFace models loaded successfully!")
except Exception as e:
    print(f"⚠️ Warning: Could not load DeepFace models: {e}")

# Initialize Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'frames_db'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# Add SSL if specified
if os.getenv('DB_SSL_CA'):
    DB_CONFIG['ssl_ca'] = os.getenv('DB_SSL_CA')

# Database Helper
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"❌ DB Error: {err}")
        return None

# Face Processing
def process_face_embedding(face_capture_data_url):
    print("\n🔍 Processing Face Embedding...")
    
    if not face_capture_data_url:
        print("⚠️ No face capture data received.")
        return None

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
            return None

        # Generate Embedding
        embedding_objs = DeepFace.represent(
            img_path=frame,
            model_name=MODEL_NAME,
            enforce_detection=False,
            detector_backend=DETECTOR_BACKEND
        )
        
        if len(embedding_objs) >= 1:
            face_vector = embedding_objs[0]["embedding"]
            data_to_save = pickle.dumps([face_vector])
            print("✅ Embedding generated successfully!")
            return data_to_save
        
        print("⚠️ DeepFace returned 0 embeddings.")
        return None

    except Exception as e:
        print(f"❌ Error in process_face_embedding: {e}")
        return None

# Face Matching
def find_matching_user(face_embedding_data):
    if not face_embedding_data:
        return None
    
    try:
        captured_vector = pickle.loads(face_embedding_data)[0]
        
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        # Check both face_data and face_embedding_vgg columns
        cursor.execute("""
            SELECT user_id,
                   COALESCE(face_data, face_embedding_vgg) as face_data
            FROM User
            WHERE COALESCE(face_data, face_embedding_vgg) IS NOT NULL
        """)
        registered_users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"📊 Found {len(registered_users)} registered users")
        
        best_match_id = None
        best_distance = float('inf')
        threshold = 0.6
        
        for user in registered_users:
            try:
                stored_vectors = pickle.loads(user['face_data'])
                stored_vector = stored_vectors[0]
                
                distance = np.linalg.norm(np.array(captured_vector) - np.array(stored_vector))
                print(f"   User {user['user_id']}: Distance = {distance:.4f}")
                
                if distance < best_distance:
                    best_distance = distance
                    best_match_id = user['user_id']
            except Exception as e:
                print(f"   ⚠️ Error comparing user {user['user_id']}: {e}")
                continue
        
        if best_match_id and best_distance < threshold:
            print(f"✅ Face matched! User ID: {best_match_id} (Distance: {best_distance:.4f})")
            return best_match_id
        else:
            print(f"⚠️ No matching face found (Best distance: {best_distance:.4f})")
            return None
            
    except Exception as e:
        print(f"❌ Error in face matching: {e}")
        return None

# ==========================================
# API: RECORD ATTENDANCE
# ==========================================
@app.route('/api/attendance/record', methods=['POST'])
def record_attendance():
    """
    Record attendance with face recognition
    Expected form data:
    - face_capture: Base64 encoded image
    - event_type: attendance_in, attendance_out, break_in, break_out
    - timestamp: ISO format timestamp (optional)
    - schedule_id: Class schedule ID (optional)
    """
    try:
        face_capture = request.form.get('face_capture')
        event_type = request.form.get('event_type', 'attendance_in')
        timestamp_str = request.form.get('timestamp')
        schedule_id = request.form.get('schedule_id')

        if not face_capture:
            return jsonify({"error": "Missing face_capture"}), 400

        # Parse timestamp
        try:
            event_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.now()
        except:
            event_timestamp = datetime.now()

        print(f"\n📸 Recording Attendance via Face Recognition...")
        print(f"   Event Type: {event_type}")
        print(f"   Timestamp: {event_timestamp}")

        # Process face embedding
        face_embedding = process_face_embedding(face_capture)

        if not face_embedding:
            return jsonify({"error": "Could not process face"}), 400

        # Match face
        user_id = find_matching_user(face_embedding)

        if not user_id:
            return jsonify({"error": "Face not recognized. Please register first."}), 404

        # Get database connection
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        try:
            # Get user info
            cursor.execute(
                "SELECT user_id, firstName, lastName, role FROM User WHERE user_id = %s",
                (user_id,)
            )
            user_info = cursor.fetchone()
            
            if not user_info:
                return jsonify({"error": "User not found"}), 404

            # Get room/course info if schedule_id provided
            room_name = "TBA"
            course_code = "TBA"
            camera_id = None
            
            if schedule_id:
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
            confidence_score = 95.0
            remarks = "On Time" if event_type == "attendance_in" else "Noted"
            
            cursor.execute("""
                INSERT INTO EventLog
                (user_id, event_type, timestamp, camera_id, confidence_score, remarks)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, event_type, event_timestamp, camera_id, confidence_score, remarks))

            conn.commit()

            # Create notification
            user_name = f"{user_info['firstName']} {user_info['lastName']}"
            notif_msg = f"Attendance {event_type.replace('_', ' ')} recorded at {event_timestamp.strftime('%H:%M')}"
            
            cursor.execute("""
                INSERT INTO Notification
                (user_id, icon, message, is_read)
                VALUES (%s, 'fas fa-check-circle', %s, FALSE)
            """, (user_id, notif_msg))
            
            conn.commit()

            print(f"✅ Attendance recorded for {user_name}")
            
            return jsonify({
                "message": f"✅ Attendance recorded for {user_name}",
                "user_id": user_id,
                "user_name": user_name,
                "event_type": event_type,
                "timestamp": event_timestamp.isoformat(),
                "course_code": course_code,
                "room_name": room_name,
                "confidence_score": confidence_score
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

# ==========================================
# API: HEALTH CHECK
# ==========================================
@app.route('/health', methods=['GET'])
def health_check():
    """Check if API is running"""
    return jsonify({
        "status": "running",
        "message": "FRAMES Kiosk Backend is operational",
        "timestamp": datetime.now().isoformat()
    }), 200

# ==========================================
# API: DATABASE CHECK
# ==========================================
@app.route('/api/test/connection', methods=['GET'])
def test_connection():
    """Test database connection"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM User WHERE COALESCE(face_data, face_embedding_vgg) IS NOT NULL")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return jsonify({
                "status": "connected",
                "registered_users": result['count'],
                "message": "Database connection successful"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    else:
        return jsonify({
            "status": "error",
            "message": "Could not connect to database"
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎥 FRAMES ATTENDANCE KIOSK - BACKEND")
    print("="*60)
    print(f"📊 Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"🗄️ Database Name: {DB_CONFIG['database']}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
