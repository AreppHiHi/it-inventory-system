from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
import sqlite3
import pandas as pd
import serverless_wsgi

app = Flask(__name__)
app.secret_key = 'it_student_modern_ui_secret'

# --- Authentication Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('my_inventory.db')
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user: return User(user[0], user[1], user[3])
    return None

def get_db_connection():
    conn = sqlite3.connect('my_inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Security Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['role']))
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Main Dashboard ---
@app.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    conn = get_db_connection()
    
    total = conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    hw = conn.execute("SELECT COUNT(*) FROM items WHERE category = 'Hardware'").fetchone()[0]
    sw = conn.execute("SELECT COUNT(*) FROM items WHERE category = 'Software'").fetchone()[0]
    
    if search:
        items = conn.execute("SELECT * FROM items WHERE name LIKE ? OR category LIKE ?", ('%'+search+'%', '%'+search+'%')).fetchall()
    else:
        items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    
    stats = {'total': total, 'hardware': hw, 'software': sw}
    return render_template('index.html', items=items, search=search, stats=stats)

# --- Admin Only Routes ---
@app.route('/add', methods=['POST'])
@login_required
def add_item():
    if current_user.role != 'admin': return redirect(url_for('index'))
    name, cat, stat = request.form['name'], request.form['category'], request.form['status']
    if name:
        conn = get_db_connection()
        conn.execute('INSERT INTO items (name, category, status) VALUES (?, ?, ?)', (name, cat, stat))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>')
@login_required
def edit_item(id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', item=item)

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update_item(id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    name, cat, stat = request.form['name'], request.form['category'], request.form['status']
    conn = get_db_connection()
    conn.execute('UPDATE items SET name=?, category=?, status=? WHERE id=?', (name, cat, stat, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
@login_required
def delete_item(id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/export')
@login_required
def export_data():
    if current_user.role != 'admin': return redirect(url_for('index'))
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM items", conn)
    conn.close()
    # Save to a temporary directory that Netlify allows writing to
    file_path = "/tmp/it_inventory_report.csv"
    df.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True, download_name="it_inventory_report.csv")

# --- Netlify Serverless Wrapper ---
def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)

if __name__ == '__main__':
    app.run(debug=True)