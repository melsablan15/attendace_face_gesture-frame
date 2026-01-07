# 🗄️ DATABASE FIX - Add face_data Column

## 📋 SQL Commands to Run

### Step 1: Check Current Table Structure

First, let's see what columns exist in the User table:

```sql
DESCRIBE User;
```

Or:

```sql
SHOW COLUMNS FROM User;
```

### Step 2: Add face_data Column to User Table

If `face_data` column doesn't exist, add it:

```sql
ALTER TABLE User 
ADD COLUMN face_data LONGBLOB AFTER face_embedding_vgg;
```

### Step 3: Check EventLog Table (Optional)

Check if EventLog needs face_data column:

```sql
DESCRIBE EventLog;
```

If you want to store face images in EventLog too:

```sql
ALTER TABLE EventLog 
ADD COLUMN face_data LONGTEXT AFTER remarks;
```

### Step 4: Verify Changes

```sql
DESCRIBE User;
DESCRIBE EventLog;
```

---

## 🔧 Complete Database Setup Script

Run this complete script to ensure all tables are properly configured:

```sql
-- =============================================
-- FRAMES ATTENDANCE SYSTEM - DATABASE SETUP
-- =============================================

-- 1. ADD FACE_DATA TO USER TABLE
-- This stores the face embedding for recognition
ALTER TABLE User 
ADD COLUMN IF NOT EXISTS face_data LONGBLOB COMMENT 'Face embedding data for recognition';

-- 2. ADD FACE_DATA TO EVENTLOG (Optional - for storing captured images)
-- This stores the actual captured image when attendance is recorded
ALTER TABLE EventLog 
ADD COLUMN IF NOT EXISTS face_data LONGTEXT COMMENT 'Captured face image (base64)';

-- 3. ADD INDEX FOR FASTER FACE MATCHING
ALTER TABLE User 
ADD INDEX idx_face_data (face_data(100));

-- 4. VERIFY CHANGES
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'User' 
AND COLUMN_NAME LIKE '%face%';

SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'EventLog' 
AND COLUMN_NAME = 'face_data';
```

---

## 📊 Expected Table Structures

### User Table Should Have:
```
+----------------------+---------------+------+
| Column               | Type          | Null |
+----------------------+---------------+------+
| user_id              | int           | NO   |
| email                | varchar(255)  | NO   |
| firstName            | varchar(100)  | YES  |
| lastName             | varchar(100)  | YES  |
| face_embedding_vgg   | longblob      | YES  |
| face_data            | longblob      | YES  | ← NEW
| face_status          | varchar(50)   | YES  |
| verification_status  | varchar(50)   | YES  |
| ...                  | ...           | ...  |
+----------------------+---------------+------+
```

### EventLog Table Should Have:
```
+------------------+---------------+------+
| Column           | Type          | Null |
+------------------+---------------+------+
| event_id         | int           | NO   |
| user_id          | int           | YES  |
| event_type       | varchar(50)   | YES  |
| timestamp        | datetime      | YES  |
| camera_id        | int           | YES  |
| confidence_score | float         | YES  |
| remarks          | text          | YES  |
| face_data        | longtext      | YES  | ← NEW (optional)
+------------------+---------------+------+
```

---

## 🔓 After Adding Columns - Uncomment Backend Code

Once you've added the `face_data` column, go back to your backend and uncomment the code:

### File: `backend/app.py` (around line 1326)

**Change FROM:**
```python
# Store face embedding if available (REMOVED face_data to avoid column error)
# if face_embedding:
#     cursor.execute("""
#         UPDATE User 
#         SET face_data = %s, face_registration_status = 'Registered'
#         WHERE user_id = %s
#     """, (face_embedding, user_id))
```

**Change TO:**
```python
# Store face embedding if available
if face_embedding:
    cursor.execute("""
        UPDATE User 
        SET face_data = %s, face_registration_status = 'Registered'
        WHERE user_id = %s
    """, (face_embedding, user_id))
```

---

## 🚀 Quick Setup Commands

Copy and paste these commands one by one in your MySQL client:

```sql
-- Select your database
USE your_database_name;

-- Add face_data to User table
ALTER TABLE User 
ADD COLUMN face_data LONGBLOB;

-- Optional: Add face_data to EventLog table
ALTER TABLE EventLog 
ADD COLUMN face_data LONGTEXT;

-- Verify it worked
DESCRIBE User;
DESCRIBE EventLog;
```

---

## 🔍 Troubleshooting

### If you get "column already exists" error:
```sql
-- Check if column exists first
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'User' 
AND COLUMN_NAME = 'face_data';

-- If it exists but has wrong type, modify it:
ALTER TABLE User 
MODIFY COLUMN face_data LONGBLOB;
```

### If you want to remove and re-add:
```sql
-- Drop the column
ALTER TABLE User 
DROP COLUMN face_data;

-- Add it fresh
ALTER TABLE User 
ADD COLUMN face_data LONGBLOB;
```

---

## ✅ Testing After Database Update

1. **Restart your backend:**
   ```bash
   cd backend
   python app.py
   ```

2. **Register a new user with face:**
   - Go to registration page
   - Capture face
   - Check database: `SELECT user_id, firstName, face_data IS NOT NULL as has_face FROM User;`

3. **Test attendance capture:**
   - Go to attendance page
   - Stand in front of camera
   - Should work without errors now!

4. **Check stored data:**
   ```sql
   -- See which users have face data
   SELECT 
       user_id, 
       firstName, 
       lastName,
       CASE 
           WHEN face_data IS NOT NULL THEN 'Yes' 
           ELSE 'No' 
       END as has_face_data,
       LENGTH(face_data) as data_size
   FROM User;
   ```

---

## 📈 Benefits of Adding face_data Column

✅ Proper storage of face embeddings
✅ Better face matching accuracy
✅ Can update face data when needed
✅ Can store multiple face angles (future)
✅ Better database organization
✅ No more workarounds needed

---

## 🎓 For Your Database Documentation

Include this in your capstone documentation:

**Database Schema:**
- **User.face_data** - Stores face embedding (LONGBLOB)
- **EventLog.face_data** - Stores captured image (LONGTEXT, optional)
- **Purpose** - Enable face recognition and attendance tracking
- **Size** - ~100KB per face embedding

---

Let me know when you've run the SQL commands and I'll help you uncomment the backend code!
