import sqlite3
import random
import string
from flask import Flask, render_template, request, jsonify

# --- THE CORRECTED LINE ---
# The static_url_path='' tells Flask not to add a '/static' prefix to the URL.
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

# Helper function to get a database connection.
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# API endpoint to get all requests
@app.route('/api/requests', methods=['GET'])
def get_all_requests():
    conn = get_db_connection()
    requests_data = conn.execute('SELECT * FROM requests ORDER BY created_at DESC').fetchall()
    conn.close()
    requests_list = [dict(row) for row in requests_data]
    return jsonify(requests_list)

# API endpoint to get a single request's details
@app.route('/api/requests/<request_id_str>', methods=['GET'])
def get_single_request(request_id_str):
    conn = get_db_connection()
    request_data = conn.execute('SELECT * FROM requests WHERE request_id_str = ?', 
                                (request_id_str,)).fetchone()
    
    if request_data is None:
        return jsonify({"error": "Request not found"}), 404
        
    items_data = conn.execute('SELECT item_name, quantity FROM items WHERE request_id = ?', 
                              (request_data['id'],)).fetchall()
    conn.close()
    
    response = dict(request_data)
    response['items'] = [f"{item['item_name']} - {item['quantity']}" for item in items_data]
    
    return jsonify(response)


# API endpoint to create a new request
@app.route('/api/requests', methods=['POST'])
def create_request():
    data = request.get_json()
    request_id_str = f"SC-{''.join(random.choices(string.digits, k=4))}"

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO requests (request_id_str, supplier_name, delivery_type, delivery_address, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (request_id_str, data['supplier'], data['delivery']['type'], data['delivery']['address'], 'Pending'))
    
    new_request_id = cursor.lastrowid
    
    for item in data['items']:
        name, quantity = item.split(' - ')
        cursor.execute('''
            INSERT INTO items (request_id, item_name, quantity)
            VALUES (?, ?, ?)
        ''', (new_request_id, name, quantity))
        
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Request created successfully", "request_id": request_id_str}), 201


# Main route to serve the front-end HTML file
@app.route('/')
def index():
    return render_template('vendor.html')

if __name__ == '__main__':
    app.run(debug=True)