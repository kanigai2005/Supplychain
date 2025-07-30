import sqlite3
import os

# Correctly locate the database file in the same directory as the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(SCRIPT_DIR, 'supplychain.db')

def setup_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    print("Creating tables...")

    # 1. Users Table (for login/roles)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('supplier', 'vendor', 'driver'))
        );
    ''')

    # 2. Supplier's Inventory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity_available INTEGER NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES users(id)
        );
    ''')

    # 3. Vendor's Material Requests Table -- THIS IS THE CORRECTED VERSION
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'completed')),
            delivery_type TEXT,      -- WAS MISSING
            delivery_address TEXT,   -- WAS MISSING
            FOREIGN KEY (vendor_id) REFERENCES users(id)
        );
    ''')

    # 4. Driver's Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS driver_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT NOT NULL,
            pickup_address TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            delivery_type TEXT NOT NULL,
            is_quick INTEGER NOT NULL,
            status TEXT NOT NULL,
            driver_id INTEGER,
            delivery_time TEXT,
            FOREIGN KEY (driver_id) REFERENCES users(id)
        );
    ''')
    
    # Add some sample users for testing
    print("Inserting sample users...")
    try:
        cursor.execute("INSERT INTO users (username, email, password, role) VALUES ('supplier1', 's@s.com', 'pass', 'supplier')")
        cursor.execute("INSERT INTO users (username, email, password, role) VALUES ('vendor1', 'v@v.com', 'pass', 'vendor')")
        cursor.execute("INSERT INTO users (username, email, password, role) VALUES ('driver1', 'd@d.com', 'pass', 'driver')")
    except sqlite3.IntegrityError:
        print("Sample users already exist.")

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == '__main__':
    setup_database()