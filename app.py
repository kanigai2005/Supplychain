import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, g, jsonify
from functools import wraps
import os

# Corrected the __name__ variable
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Correctly locate the database file in the same directory as the app
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(SCRIPT_DIR, 'supplychain.db')

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
                return redirect(url_for('login'))
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

# ----------------- Supplier Routes (RESTORED) -----------------
@app.route('/supplier/home')
@login_required
@supplier_required
def supplier_home():
    db = get_db()
    supplier_id = session['user_id']
    inventory_count = db.execute("SELECT COUNT(id) FROM inventory WHERE supplier_id=?", (supplier_id,)).fetchone()[0]
    pending_requests = db.execute("SELECT COUNT(id) FROM material_requests WHERE status='pending'").fetchone()[0]
    confirmed_orders = db.execute("SELECT COUNT(id) FROM material_requests WHERE status='confirmed'").fetchone()[0]
    return render_template('supplier_home.html', inventory_count=inventory_count, pending_requests=pending_requests, confirmed_orders=confirmed_orders)

@app.route('/supplier/inventory')
@login_required
@supplier_required
def supplier_inventory():
    db = get_db()
    items = db.execute("SELECT item_name, quantity_available FROM inventory WHERE supplier_id=?", (session['user_id'],)).fetchall()
    return render_template('supplier_inventory.html', items=items)

@app.route('/supplier/requests')
@login_required
@supplier_required
def supplier_requests():
    db = get_db()
    requests = db.execute("""
        SELECT mr.id, mr.item_name, mr.quantity, u.username AS vendor_name, mr.status
        FROM material_requests mr JOIN users u ON mr.vendor_id = u.id
        WHERE mr.status = 'pending'
    """).fetchall()
    return render_template('supplier_requests.html', requests=requests)

@app.route('/supplier/confirm_request/<int:request_id>')
@login_required
@supplier_required
def confirm_request(request_id):
    db = get_db()
    req_data = db.execute(
        """SELECT mr.item_name, mr.quantity, mr.delivery_type, mr.delivery_address, u.username AS vendor_name
           FROM material_requests mr JOIN users u ON mr.vendor_id = u.id
           WHERE mr.id = ?""",
        (request_id,)
    ).fetchone()

    if not req_data:
        return "Request not found", 404

    # NOTE: This creates a driver order. The vendor request now ALSO creates one.
    # In a real system, you would choose one of these two places to create the driver order.
    pickup_address = "Main Wholesale Market"
    is_quick = 1 if "urgent" in req_data['item_name'].lower() else 0
    
    db.execute(
        """INSERT INTO driver_orders 
           (vendor_name, pickup_address, delivery_address, delivery_type, is_quick, status)
           VALUES (?, ?, ?, ?, ?, 'available')""",
        (req_data['vendor_name'], pickup_address, req_data['delivery_address'], req_data['delivery_type'], is_quick)
    )
    
    db.execute("UPDATE material_requests SET status='confirmed' WHERE id=?", (request_id,))
    db.commit()
    return redirect(url_for('supplier_requests'))

@app.route('/supplier/reject_request/<int:request_id>')
@login_required
@supplier_required
def reject_request(request_id):
    db = get_db()
    db.execute("DELETE FROM material_requests WHERE id=?", (request_id,))
    db.commit()
    return redirect(url_for('supplier_requests'))

@app.route('/supplier/confirmed')
@login_required
@supplier_required
def supplier_confirmed():
    db = get_db()
    confirmed = db.execute("""
        SELECT mr.id, mr.item_name, mr.quantity, u.username AS vendor_name, mr.status 
        FROM material_requests mr JOIN users u ON mr.vendor_id = u.id
        WHERE mr.status = 'confirmed'
    """).fetchall()
    return render_template('supplier_confirmed.html', confirmed=confirmed)

@app.route('/supplier/complete_order/<int:order_id>')
@login_required
@supplier_required
def complete_order(order_id):
    db = get_db()
    db.execute("UPDATE material_requests SET status='completed' WHERE id=?", (order_id,))
    db.commit()
    return redirect(url_for('supplier_confirmed'))

@app.route('/supplier/add_item', methods=['POST'])
@login_required
@supplier_required
def add_item():
    item_name = request.form['item']
    quantity = int(request.form['quantity'])
    db = get_db()
    db.execute("INSERT INTO inventory (supplier_id, item_name, quantity_available) VALUES (?, ?, ?)", (session['user_id'], item_name, quantity))
    db.commit()
    return redirect(url_for('supplier_inventory'))

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

@app.route('/api/vendor/requests', methods=['POST'])
@login_required
@vendor_required
def create_vendor_request():
    data = request.get_json()
    vendor_id = session['user_id']
    delivery_type = data.get('delivery_type')
    delivery_address = data.get('delivery_address')

    if not all([data, data.get('items'), delivery_type, delivery_address]):
        return jsonify({"error": "Invalid request format."}), 400

    db = get_db()
    for item in data['items']:
        try:
            item_name, quantity_str = item.split(' - ')
            quantity = int(quantity_str.strip().replace('kg', ''))
            
            # Create the material request for the supplier
            db.execute(
                """INSERT INTO material_requests 
                   (item_name, quantity, vendor_id, status, delivery_type, delivery_address) 
                   VALUES (?, ?, ?, 'pending', ?, ?)
                """,
                (item_name.strip(), quantity, vendor_id, delivery_type, delivery_address)
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
    request_data = db.execute("SELECT * FROM material_requests WHERE id = ? AND vendor_id = ?", (request_id, session['user_id'])).fetchone()

    if request_data is None:
        return jsonify({"error": "Request not found"}), 404

    response = dict(request_data)
    response['items'] = [f"{response['item_name']} - {response['quantity']}"]
    response['supplier_name'] = "Supplier (TBD)"
    return jsonify(response)


# ----------------- Driver Routes -----------------
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


# ----------------- Driver API Routes -----------------
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
        if address not in grouped_orders:
            grouped_orders[address] = []
        grouped_orders[address].append(order)
    return jsonify(grouped_orders)

@app.route('/api/driver/orders/accept/<int:order_id>', methods=['POST'])
@login_required
@driver_required
def accept_driver_order(order_id):
    driver_id = session['user_id']
    delivery_time = request.json.get('delivery_time')
    if not delivery_time:
        return jsonify({"error": "Delivery time is required"}), 400
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
    allowed_statuses = ['out_for_delivery', 'delivery_complete']
    if new_status not in allowed_statuses:
        return jsonify({"error": "Invalid status update"}), 400
    db = get_db()
    cursor = db.execute("UPDATE driver_orders SET status=? WHERE id=? AND driver_id=?", (new_status, order_id, driver_id))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "Order not found or permission denied"}), 404
    return jsonify({"message": f"Status updated to {new_status}"})


# Corrected the __name__ variable for running the app
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found. Please run database_setup.py first.")
    else:
        app.run(debug=True)
