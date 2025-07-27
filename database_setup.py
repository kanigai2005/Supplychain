import sqlite3

# Connect to SQLite (this will create the database file if it doesn't exist)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# -- Create the 'requests' table --
# This table stores the main information for each request.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id_str TEXT NOT NULL UNIQUE,
        supplier_name TEXT NOT NULL,
        delivery_type TEXT NOT NULL,
        delivery_address TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# -- Create the 'items' table --
# This table stores the individual items, linked to a request by 'request_id'.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        quantity TEXT NOT NULL,
        FOREIGN KEY (request_id) REFERENCES requests (id)
    )
''')

print("Database and tables created successfully.")

# Commit changes and close the connection
conn.commit()
conn.close()