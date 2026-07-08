# migrate_2fa.py - Run this to add 2FA fields to existing database
import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add 2FA columns to existing User table and create OTPCode table"""
    
    # Path to your database file
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'settle_space.db')
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        print("Looking for database in current directory...")
        
        # Try different common paths
        possible_paths = [
            'settle_space.db',
            'app.db',
            'housing3.db',
            'instance/settle_space.db',
            'app/settle_space.db'
        ]
        
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                found = True
                print(f"Found database at: {db_path}")
                break
        
        if not found:
            print("Could not find database file. Please check your database path.")
            return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Connected to database successfully.")
        
        # Check if 2FA columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current user table columns: {columns}")
        
        # Add 2FA columns to user table if they don't exist
        if 'two_factor_enabled' not in columns:
            print("Adding two_factor_enabled column...")
            cursor.execute("ALTER TABLE user ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0")
        
        if 'two_factor_method' not in columns:
            print("Adding two_factor_method column...")
            cursor.execute("ALTER TABLE user ADD COLUMN two_factor_method VARCHAR(10) DEFAULT 'email'")
        
        # Check if otp_code table exists and if it has is_used column
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='otp_code'")
        otp_table_exists = cursor.fetchone() is not None
        
        if otp_table_exists:
            cursor.execute("PRAGMA table_info(otp_code)")
            otp_columns = [column[1] for column in cursor.fetchall()]
            if 'is_used' in otp_columns:
                print("Old otp_code table with 'is_used' column detected. Dropping it to recreate with 'used'...")
                cursor.execute("DROP TABLE otp_code")
                otp_table_exists = False
        
        # Create OTPCode table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_code (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code VARCHAR(10) NOT NULL,
                method VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
            )
        """)
        
        print("OTPCode table created/verified.")
        
        # Create index on user_id for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_otp_user_id ON otp_code(user_id)
        """)
        
        # Create index on expires_at for cleanup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_otp_expires_at ON otp_code(expires_at)
        """)
        
        print("Indexes created.")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(user)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated user table columns: {new_columns}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='otp_code'")
        otp_table_exists = cursor.fetchone() is not None
        print(f"OTPCode table exists: {otp_table_exists}")
        
        conn.close()
        
        print("\n[SUCCESS] Database migration completed successfully!")
        print("You can now run your Flask app with 2FA support.")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("[MIGRATE] Starting database migration for 2FA...")
    success = migrate_database()
    
    if success:
        print("\n[SUCCESS] Migration completed! You can now run: python run.py")
    else:
        print("\n[ERROR] Migration failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure your database file exists")
        print("2. Check file permissions")
        print("3. Make sure no other process is using the database")