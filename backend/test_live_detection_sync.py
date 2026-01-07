"""
Quick Test Script - Verify Live Detection MySQL Sync
Run this to check if your EventLog data is accessible
"""

import mysql.connector
from db_config import DB_CONFIG
from datetime import datetime, timedelta

def test_connection():
    print("\n" + "="*60)
    print("🔍 TESTING MYSQL → LIVE DETECTION SYNC")
    print("="*60 + "\n")
    
    try:
        # 1. Connect to database
        print("📡 Connecting to MySQL...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        print("✅ Connection successful!\n")
        
        # 2. Check EventLog table
        print("📊 Checking EventLog table...")
        cursor.execute("SELECT COUNT(*) as count FROM EventLog")
        total_records = cursor.fetchone()['count']
        print(f"✅ Total records in EventLog: {total_records}\n")
        
        if total_records == 0:
            print("⚠️  WARNING: No records found in EventLog table!")
            print("   Make sure attendance has been recorded first.\n")
            return
        
        # 3. Get recent records (last 7 days)
        print("🕐 Fetching recent attendance records (last 7 days)...")
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        query = """
            SELECT e.log_id, e.user_id, e.event_type, e.timestamp, 
                   e.confidence_score, e.remarks,
                   u.firstName, u.lastName, u.role
            FROM EventLog e
            LEFT JOIN User u ON e.user_id = u.user_id
            WHERE e.timestamp >= %s
            ORDER BY e.timestamp DESC
            LIMIT 10
        """
        
        cursor.execute(query, (seven_days_ago,))
        recent_records = cursor.fetchall()
        
        print(f"✅ Found {len(recent_records)} recent records\n")
        
        # 4. Display records
        if recent_records:
            print("📋 LATEST ATTENDANCE RECORDS:")
            print("-" * 100)
            print(f"{'ID':<6} {'Name':<25} {'Role':<12} {'Event':<18} {'Time':<20} {'Score':<8} {'Remarks'}")
            print("-" * 100)
            
            for record in recent_records:
                name = f"{record.get('firstName', 'N/A')} {record.get('lastName', 'N/A')}"
                role = record.get('role', 'N/A')
                event_type = record.get('event_type', 'N/A')
                timestamp = record.get('timestamp', 'N/A')
                score = record.get('confidence_score', 0)
                remarks = record.get('remarks', 'N/A')
                log_id = record.get('log_id', 'N/A')
                
                print(f"{log_id:<6} {name:<25} {role:<12} {event_type:<18} {str(timestamp):<20} {score}%{'':<5} {remarks}")
            
            print("-" * 100 + "\n")
        
        # 5. Check time distribution
        print("📅 Record Distribution by Day:")
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM EventLog
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)
        
        distribution = cursor.fetchall()
        for row in distribution:
            date = row['date']
            count = row['count']
            today = "← TODAY" if date == datetime.now().date() else ""
            print(f"  {date}: {count} record(s) {today}")
        
        print("\n")
        
        # 6. Test the API endpoint query
        print("🔍 Testing Live Detection API Query...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM EventLog e
            WHERE e.timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        last_24h = cursor.fetchone()['count']
        print(f"✅ Records in last 24 hours: {last_24h}")
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM EventLog e
            WHERE e.timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        """)
        last_2h = cursor.fetchone()['count']
        print(f"✅ Records in last 2 hours: {last_2h}\n")
        
        # 7. Recommendations
        print("💡 RECOMMENDATIONS:")
        if last_2h > 0:
            print("   ✅ You have recent records! They should appear in Live Detection.")
        elif last_24h > 0:
            print("   ⚠️  Records are older than 2 hours. Set time filter to '24 Hours' in Live Detection.")
        else:
            print("   ⚠️  No records in last 24 hours. Set time filter to 'Last Week' to see older data.")
        
        print("\n" + "="*60)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
        print("🚀 NEXT STEPS:")
        print("   1. Start backend: cd backend && python app.py")
        print("   2. Start frontend: cd frontend && npm start")
        print("   3. Go to Live Detection page")
        print("   4. Adjust time filter if needed to see your records\n")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        print("\n💡 Check your db_config.py settings:")
        print("   - Host, port, username, password")
        print("   - SSL certificate (ca.pem)")
        print("   - Database name (defaultdb)\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    test_connection()
