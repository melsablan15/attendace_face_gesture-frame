"""
🔍 DIAGNOSTIC SCRIPT - Check Face Recognition Setup
Run this in your backend folder: python diagnostic_check.py
"""

import mysql.connector
from db_config import DB_CONFIG

def check_database():
    print("\n" + "="*60)
    print("🔍 CHECKING DATABASE SETUP")
    print("="*60)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Check 1: Does face_data column exist?
        print("\n📋 Step 1: Checking table structure...")
        cursor.execute("DESCRIBE User")
        columns = cursor.fetchall()
        
        face_columns = [col for col in columns if 'face' in col['Field'].lower()]
        print(f"✅ Found {len(face_columns)} face-related columns:")
        for col in face_columns:
            print(f"   - {col['Field']} ({col['Type']})")
        
        # Check 2: Which column has face data?
        print("\n📊 Step 2: Checking which column has face data...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN face_embedding_vgg IS NOT NULL THEN 1 ELSE 0 END) as has_vgg,
                SUM(CASE WHEN face_data IS NOT NULL THEN 1 ELSE 0 END) as has_face_data
            FROM User
            WHERE verification_status = 'Verified'
        """)
        result = cursor.fetchone()
        
        print(f"   Total verified users: {result['total_users']}")
        print(f"   Users with face_embedding_vgg: {result['has_vgg']}")
        print(f"   Users with face_data: {result['has_face_data']}")
        
        # Check 3: Show actual users with face data
        print("\n👥 Step 3: Users with face data:")
        cursor.execute("""
            SELECT 
                user_id,
                firstName,
                lastName,
                face_embedding_vgg IS NOT NULL as has_vgg,
                face_data IS NOT NULL as has_face_data,
                verification_status
            FROM User 
            WHERE verification_status = 'Verified'
            LIMIT 5
        """)
        users = cursor.fetchall()
        
        if len(users) == 0:
            print("   ⚠️ No verified users found!")
        else:
            for user in users:
                vgg = "✅" if user['has_vgg'] else "❌"
                data = "✅" if user['has_face_data'] else "❌"
                print(f"   {user['user_id']}: {user['firstName']} {user['lastName']}")
                print(f"      face_embedding_vgg: {vgg}")
                print(f"      face_data: {data}")
        
        # Check 4: Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if result['has_vgg'] > 0 and result['has_face_data'] == 0:
            print("   ⚠️ Face data is in 'face_embedding_vgg', not 'face_data'!")
            print("   🔧 FIX: Update backend/app.py line ~60:")
            print("      Change: cursor.execute(\"SELECT user_id, face_data FROM User...\")")
            print("      To: cursor.execute(\"SELECT user_id, face_embedding_vgg as face_data FROM User...\")")
            print("\n   OR run this SQL to copy data:")
            print("      UPDATE User SET face_data = face_embedding_vgg WHERE face_embedding_vgg IS NOT NULL;")
        elif result['has_face_data'] > 0:
            print("   ✅ Face data is properly stored in 'face_data' column")
        else:
            print("   ⚠️ No users have face data!")
            print("   🔧 FIX: Register users with face capture enabled")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ DIAGNOSTIC COMPLETE")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Make sure your database credentials in db_config.py are correct!")

if __name__ == "__main__":
    check_database()
