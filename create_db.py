import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    # This creates a fresh database file
    conn = sqlite3.connect('my_inventory.db')
    cursor = conn.cursor()
    
    # Create the IT Inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'Good'
        )
    ''')
    
    # Create the User table for Login
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Add an admin user (Password: admin123)
    # We use hashing for security, just like professional IT systems
    hashed_pw = generate_password_hash('admin123')
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_pw))
        print("Success: Admin user created!")
    except sqlite3.IntegrityError:
        print("Admin user already exists.")
        
    conn.commit()
    conn.close()
    print("Database 'my_inventory.db' is ready!")

if __name__ == '__main__':
    init_db()