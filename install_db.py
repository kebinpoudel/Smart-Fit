import mysql.connector

# Database Config
DB_SETTINGS = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
}
DB_NAME = 'smartfit_apparel'

DDL_STATEMENTS = {}

# Users
DDL_STATEMENTS['staff_users'] = (
    "CREATE TABLE IF NOT EXISTS staff_users ("
    "  uid INT AUTO_INCREMENT PRIMARY KEY,"
    "  username VARCHAR(50) NOT NULL UNIQUE,"
    "  pass_hash VARCHAR(255) NOT NULL,"
    "  role VARCHAR(20) NOT NULL,"
    "  display_name VARCHAR(100)"
    ") ENGINE=InnoDB")

# Inventory - Generic Stock (No specific size column here)
DDL_STATEMENTS['inventory'] = (
    "CREATE TABLE IF NOT EXISTS inventory ("
    "  sku INT AUTO_INCREMENT PRIMARY KEY,"
    "  item_name VARCHAR(100) NOT NULL,"
    "  category VARCHAR(50) NOT NULL,"
    "  unit_price DECIMAL(10, 2) NOT NULL,"
    "  qty_in_stock INT NOT NULL,"
    "  image_path VARCHAR(255),"
    "  details TEXT"
    ") ENGINE=InnoDB")

# Clients
DDL_STATEMENTS['clients'] = (
    "CREATE TABLE IF NOT EXISTS clients ("
    "  client_id INT AUTO_INCREMENT PRIMARY KEY,"
    "  full_name VARCHAR(100) NOT NULL,"
    "  contact_no VARCHAR(20),"
    "  email_addr VARCHAR(100),"
    "  client_type VARCHAR(20) DEFAULT 'Regular'"
    ") ENGINE=InnoDB")

# Sales Log
DDL_STATEMENTS['sales_log'] = (
    "CREATE TABLE IF NOT EXISTS sales_log ("
    "  sale_id INT AUTO_INCREMENT PRIMARY KEY,"
    "  staff_id INT NOT NULL,"
    "  client_id INT,"
    "  subtotal DECIMAL(10, 2) NOT NULL,"
    "  discount_amount DECIMAL(10, 2) DEFAULT 0.00,"
    "  grand_total DECIMAL(10, 2) NOT NULL,"
    "  payment_method VARCHAR(50),"
    "  sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,"
    "  FOREIGN KEY (staff_id) REFERENCES staff_users(uid),"
    "  FOREIGN KEY (client_id) REFERENCES clients(client_id)"
    ") ENGINE=InnoDB")

# Sales Items - Added 'item_size' to record selection
DDL_STATEMENTS['sales_items'] = (
    "CREATE TABLE IF NOT EXISTS sales_items ("
    "  line_id INT AUTO_INCREMENT PRIMARY KEY,"
    "  sale_id INT NOT NULL,"
    "  sku INT NOT NULL,"
    "  qty INT NOT NULL,"
    "  item_size VARCHAR(10),"
    "  sold_at_price DECIMAL(10, 2) NOT NULL,"
    "  FOREIGN KEY (sale_id) REFERENCES sales_log(sale_id),"
    "  FOREIGN KEY (sku) REFERENCES inventory(sku)"
    ") ENGINE=InnoDB")

def init_system():
    conn = mysql.connector.connect(**DB_SETTINGS)
    cur = conn.cursor()
    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"[OK] Database '{DB_NAME}' checked.")
    except Exception as e:
        print(f"[ERR] {e}")
    finally:
        cur.close(); conn.close()

    conn = mysql.connector.connect(database=DB_NAME, **DB_SETTINGS)
    cur = conn.cursor()
    
    # Drop to reset schema
    tables_to_drop = ['sales_items', 'sales_log', 'inventory', 'clients', 'staff_users']
    for t in tables_to_drop:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {t}")
        except: pass

    for table_key, sql in DDL_STATEMENTS.items():
        try:
            cur.execute(sql)
            print(f" - Created new {table_key}")
        except Exception as e:
            print(f" - Error making {table_key}: {e}")

    # Seed Staff
    team = [
        ('nitesh', 'admin789', 'Manager', 'Nitesh (Lead)'),
        ('prajwal', 'staff1', 'Associate', 'Prajwal'),
        ('kebin', 'staff2', 'Associate', 'Kebin')
    ]
    cur.executemany("INSERT INTO staff_users (username, pass_hash, role, display_name) VALUES (%s, %s, %s, %s)", team)
    
    # Seed Inventory (Single card per product)
    clothes = [
        ('Urban Cargo Pants', 'Lowers', 45.00, 40, '', 'Olive Green'),
        ('Oversized Hoodie', 'Uppers', 65.50, 30, '', 'Beige Cotton'),
        ('Air Runners', 'Shoes', 89.99, 15, '', 'Sport Sneakers'),
        ('Floral Dress', 'Uppers', 39.99, 20, '', 'Red Print')
    ]
    cur.executemany("INSERT INTO inventory (item_name, category, unit_price, qty_in_stock, image_path, details) VALUES (%s, %s, %s, %s, %s, %s)", clothes)
    print(" + Stock added.")
    
    # Seed Clients
    clients = [
        ('John Doe', '021123456', 'john@test.com', 'Regular'),
        ('Jane Smith', '022987654', 'jane@test.com', 'Gold'),
        ('Mike Ross', '027555123', 'mike@test.com', 'Silver')
    ]
    cur.executemany("INSERT INTO clients (full_name, contact_no, email_addr, client_type) VALUES (%s, %s, %s, %s)", clients)

    conn.commit()
    cur.close(); conn.close()

if __name__ == "__main__":
    init_system()