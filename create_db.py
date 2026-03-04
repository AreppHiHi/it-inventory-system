import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('my_inventory.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        status TEXT DEFAULT 'Good'
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )''')
    
    admin_pw = generate_password_hash('admin123')
    user_pw = generate_password_hash('user123')
    
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', admin_pw, 'admin'))
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('staff', user_pw, 'user'))
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()