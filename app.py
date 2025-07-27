from flask import Flask, render_template, request, redirect, session, url_for, g
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"
DATABASE = 'supplier.db'

# ----------------- Database Setup -----------------
def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );
    ''')

    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity_available INTEGER NOT NULL
        );
    ''')

    # Create material_request table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending'
        );
    ''')

    conn.commit()
    conn.close()

# Call table creation when the app starts
create_tables()

# ----------------- Database Connection -----------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()

# ----------------- Authentication Decorator -----------------
def supplier_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'supplier':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- Home & Auth -----------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        db = get_db()
        try:
            db.execute("INSERT INTO user (username, email, password, role) VALUES (?, ?, ?, ?)",
                      (username, email, password, role))
            db.commit()
        except sqlite3.IntegrityError:
            return "User already exists!"

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"\nLogin attempt - Username: '{username}', Password: '{password}'")
        
        db = get_db()
        # First check if username exists
        user = db.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()
        
        if user:
            print(f"User found - Stored password: '{user['password']}'")
            print(f"Input password matches: {password == user['password']}")
            
            if password == user['password']:
                session['user_id'] = user['id']
                session['role'] = user['role']
                print("Login successful!")
                if user['role'] == 'supplier':
                    return redirect(url_for('supplier_dashboard'))
                # other roles...
            else:
                print("Password mismatch")
        else:
            print("Username not found")
        
        return render_template('login.html', error="Invalid credentials!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------- Supplier Routes -----------------
@app.route('/supplier/dashboard')
@supplier_required
def supplier_dashboard():
    return render_template('supplier/home.html')

@app.route('/supplier/inventory')
@supplier_required
def supplier_inventory():
    supplier_id = session['user_id']
    db = get_db()
    items = db.execute("SELECT item_name, quantity_available FROM inventory WHERE supplier_id=?", 
                      (supplier_id,)).fetchall()
    return render_template('supplier/inventory.html', items=items)

@app.route('/supplier/requests')
@supplier_required
def supplier_requests():
    db = get_db()
    requests = db.execute("""
        SELECT mr.id, mr.item_name, mr.quantity, u.username AS vendor_name, mr.status 
        FROM material_request mr
        JOIN user u ON mr.vendor_id = u.id
        WHERE mr.status = 'pending'
    """).fetchall()
    return render_template('supplier/requests.html', requests=requests)

@app.route('/supplier/confirm_request/<int:request_id>')
@supplier_required
def confirm_request(request_id):
    db = get_db()
    db.execute("UPDATE material_request SET status='confirmed' WHERE id=?", (request_id,))
    db.commit()
    return redirect(url_for('supplier_requests'))

@app.route('/supplier/complete_order/<int:order_id>')
@supplier_required
def complete_order(order_id):
    db = get_db()
    db.execute("UPDATE material_request SET status='completed' WHERE id=?", (order_id,))
    db.commit()
    return redirect(url_for('supplier_confirmed'))

@app.route('/supplier/confirmed')
@supplier_required
def supplier_confirmed():
    db = get_db()
    confirmed = db.execute("""
        SELECT mr.id, mr.item_name, mr.quantity, u.username AS vendor_name, mr.status 
        FROM material_request mr
        JOIN user u ON mr.vendor_id = u.id
        WHERE mr.status = 'confirmed'
    """).fetchall()
    return render_template('supplier/confirmed.html', confirmed=confirmed)

@app.route('/supplier/add_item', methods=['POST'])
@supplier_required
def add_item():
    if request.method == 'POST':
        item_name = request.form['item']
        quantity = int(request.form['quantity'])
        supplier_id = session['user_id']
        
        db = get_db()
        db.execute(
            "INSERT INTO inventory (supplier_id, item_name, quantity_available) VALUES (?, ?, ?)",
            (supplier_id, item_name, quantity)
        )
        db.commit()
        
    return redirect(url_for('supplier_inventory'))
if __name__ == '__main__':
    app.run(debug=True)