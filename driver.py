import sqlite3
from flask import Flask, jsonify, request, render_template, g
from flask_cors import CORS

# --- App and DB Configuration ---
app = Flask(__name__)
CORS(app)
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    print("Database initialized.")

@app.cli.command('init-db')
def init_db_command():
    init_db()

# --- Page Routes (Serving HTML) ---
@app.route('/')
def driver_home():
    return render_template('driver_home.html') 

@app.route('/requested')
def requested_orders_page():
    return render_template('driver_requested.html')

@app.route('/accepted')
def accepted_orders_page():
    return render_template('driver_accepted.html')

# --- API Routes (Providing Data) ---

@app.route('/api/orders/available', methods=['GET'])
def get_available_orders():
    # Shows orders that have not been assigned to any driver yet
    db = get_db()
    cursor = db.execute("SELECT * FROM orders WHERE status = 'available' AND driver_id IS NULL ORDER BY is_quick DESC")
    orders = [dict(row) for row in cursor.fetchall()]
    return jsonify(orders)

@app.route('/api/orders/accepted/<int:driver_id>', methods=['GET'])
def get_accepted_orders(driver_id):
    # Gets all NON-AVAILABLE orders for a SPECIFIC driver
    db = get_db()
    cursor = db.execute("SELECT * FROM orders WHERE driver_id = ? AND status IN ('accepted', 'out_for_delivery') ORDER BY delivery_address, delivery_time", (driver_id,))
    orders = [dict(row) for row in cursor.fetchall()]

    # Group orders by delivery_address
    grouped_orders = {}
    for order in orders:
        address = order['delivery_address']
        if address not in grouped_orders:
            grouped_orders[address] = []
        grouped_orders[address].append(order)
        
    return jsonify(grouped_orders)

@app.route('/api/orders/accept/<int:order_id>/<int:driver_id>', methods=['POST'])
def accept_order(order_id, driver_id):
    # Assigns an order to a driver
    data = request.get_json()
    delivery_time = data.get('delivery_time')

    if not delivery_time:
        return jsonify({"error": "Delivery time is required"}), 400

    db = get_db()
    cursor = db.execute(
        "UPDATE orders SET status = 'accepted', delivery_time = ?, driver_id = ? WHERE id = ? AND driver_id IS NULL",
        (delivery_time, driver_id, order_id)
    )
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Order not found or was already accepted by another driver"}), 404

    return jsonify({"message": f"Order {order_id} accepted successfully by driver {driver_id}!"})

@app.route('/api/orders/update_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    # Updates the status of an already accepted order
    data = request.get_json()
    new_status = data.get('status')

    allowed_statuses = ['out_for_delivery', 'delivery_complete']
    if not new_status or new_status not in allowed_statuses:
        return jsonify({"error": "Invalid status update"}), 400

    db = get_db()
    cursor = db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({"message": f"Order {order_id} status updated to {new_status}"})

if __name__ == '__main__':
    app.run(debug=True)