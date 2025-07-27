import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, g, jsonify
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'supplychain.db'

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

# ----------------- Authentication Decorators -----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                return redirect(url_for('login')) # Or show an error
            return f(*args, **kwargs)
        return decorated_function
    return decorator

supplier_required = role_required('supplier')
vendor_required = role_required('vendor')
driver_required = role_required('driver')

# ----------------- Home & Auth Routes -----------------
@app.route('/')
def index():
    if 'user_id' in session:
        role = session['role']
        if role == 'supplier':
            return redirect(url_for('supplier_home'))
        elif role == 'vendor':
            return redirect(url_for('vendor_home'))
        elif role == 'driver':
            return redirect(url_for('driver_home'))
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
            db.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                      (username, email, password, role))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('signup.html', error="Username or email already exists!")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------- Supplier Routes (No Changes) -----------------
@app.route('/supplier/home')
@login_required
@supplier_required
def supplier_home():
    return "Supplier Home Page - Not Implemented"

# ----------------- Vendor Routes -----------------
@app.route('/vendor/home')
@login_required
@vendor_required
def vendor_home():
    return render_template('vendor.html')

# ----------------- Vendor API Routes -----------------
@app.route('/api/vendor/requests', methods=['GET'])
@login_required
@vendor_required
def get_vendor_requests():
    vendor_id = session['user_id']
    db = get_db()
    requests = db.execute("SELECT id, item_name, quantity, status FROM material_requests WHERE vendor_id = ? ORDER BY id DESC", (vendor_id,)).fetchall()
    return jsonify([dict(row) for row in requests])

# MODIFIED: This function now creates a driver order for every item requested.
@app.route('/api/vendor/requests', methods=['POST'])
@login_required
@vendor_required
def create_vendor_request():
    data = request.get_json()
    vendor_id = session['user_id']
    vendor_name = session['username']
    delivery_type = data.get('delivery_type')
    delivery_address = data.get('delivery_address')

    if not all([data, data.get('items'), delivery_type, delivery_address]):
        return jsonify({"error": "Invalid request format."}), 400

    db = get_db()
    for item in data['items']:
        try:
            item_name, quantity_str = item.split(' - ')
            # Create the material request for tracking
            cursor = db.execute(
                """INSERT INTO material_requests 
                   (item_name, quantity, vendor_id, status, delivery_type, delivery_address) 
                   VALUES (?, ?, ?, 'pending', ?, ?)""",
                (item_name.strip(), int(quantity_str.strip().replace('kg','')), vendor_id, delivery_type, delivery_address)
            )
            # Create a corresponding order for drivers
            is_quick = 1 if "urgent" in item_name.lower() else 0
            db.execute(
                """INSERT INTO driver_orders 
                   (vendor_name, pickup_address, delivery_address, delivery_type, is_quick, status)
                   VALUES (?, ?, ?, ?, ?, 'available')""",
                (vendor_name, "Main Wholesale Market", delivery_address, delivery_type, is_quick)
            )
        except (ValueError, IndexError):
            continue
    db.commit()
    return jsonify({"message": "Request created successfully"}), 201
    
@app.route('/api/vendor/requests/<int:request_id>', methods=['GET'])
@login_required
@vendor_required
def get_single_vendor_request(request_id):
    db = get_db()
    req = db.execute("SELECT * FROM material_requests WHERE id = ? AND vendor_id = ?", (request_id, session['user_id'])).fetchone()
    if not req: return jsonify({"error": "Request not found"}), 404
    
    response = dict(req)
    response['items'] = [f"{req['item_name']} - {req['quantity']}kg"] # Simulate items list
    response['supplier_name'] = "Any Available Supplier"
    return jsonify(response)

# ----------------- Driver Routes (NEWLY INTEGRATED) -----------------
@app.route('/driver/home')
@login_required
@driver_required
def driver_home():
    return render_template('driver_home.html')

@app.route('/driver/requested')
@login_required
@driver_required
def driver_requested_page():
    return render_template('driver_requested.html')

@app.route('/driver/accepted')
@login_required
@driver_required
def driver_accepted_page():
    return render_template('driver_accepted.html')


# ----------------- Driver API Routes (NEWLY INTEGRATED) -----------------
@app.route('/api/driver/orders/available', methods=['GET'])
@login_required
@driver_required
def get_available_driver_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM driver_orders WHERE status = 'available' ORDER BY is_quick DESC, id DESC").fetchall()
    return jsonify([dict(row) for row in orders])

@app.route('/api/driver/orders/accepted', methods=['GET'])
@login_required
@driver_required
def get_accepted_driver_orders():
    driver_id = session['user_id']
    db = get_db()
    orders = db.execute("SELECT * FROM driver_orders WHERE driver_id = ? AND status IN ('accepted', 'out_for_delivery') ORDER BY delivery_address, delivery_time", (driver_id,)).fetchall()
    
    grouped_orders = {}
    for order in [dict(row) for row in orders]:
        address = order['delivery_address']
        if address not in grouped_orders: grouped_orders[address] = []
        grouped_orders[address].append(order)
    return jsonify(grouped_orders)

@app.route('/api/driver/orders/accept/<int:order_id>', methods=['POST'])
@login_required
@driver_required
def accept_driver_order(order_id):
    driver_id = session['user_id']
    delivery_time = request.json.get('delivery_time')
    if not delivery_time: return jsonify({"error": "Delivery time is required"}), 400
    
    db = get_db()
    cursor = db.execute("UPDATE driver_orders SET status='accepted', driver_id=?, delivery_time=? WHERE id=? AND status='available'", (driver_id, delivery_time, order_id))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "Order not found or was already taken"}), 404
    return jsonify({"message": "Order accepted successfully"})

@app.route('/api/driver/orders/update_status/<int:order_id>', methods=['POST'])
@login_required
@driver_required
def update_driver_order_status(order_id):
    new_status = request.json.get('status')
    driver_id = session['user_id']
    if new_status not in ['out_for_delivery', 'delivery_complete']:
        return jsonify({"error": "Invalid status update"}), 400
    
    db = get_db()
    cursor = db.execute("UPDATE driver_orders SET status=? WHERE id=? AND driver_id=?", (new_status, order_id, driver_id))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "Order not found or permission denied"}), 404
    return jsonify({"message": f"Status updated to {new_status}"})


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found. Please run database_setup.py first.")
    else:
        app.run(debug=True)
