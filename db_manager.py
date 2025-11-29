import mysql.connector
from mysql.connector import Error

class SmartFitDB:
    def __init__(self):
        self.config = {
            'user': 'root',
            'password': '',
            'host': 'localhost',
            'database': 'smartfit_apparel',
            'raise_on_warnings': True
        }

    def _connect(self):
        return mysql.connector.connect(**self.config)

    def verify_login(self, u, p):
        conn = self._connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM staff_users WHERE username = %s AND pass_hash = %s", (u, p))
            return cur.fetchone()
        except Error:
            return None
        finally:
            cur.close(); conn.close()

    def fetch_inventory(self):
        conn = self._connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM inventory ORDER BY item_name")
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    def fetch_clients(self):
        conn = self._connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM clients")
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    # --- INVENTORY OPS ---
    def add_product(self, name, cat, price, qty, img, desc):
        conn = self._connect()
        cur = conn.cursor()
        try:
            sql = "INSERT INTO inventory (item_name, category, unit_price, qty_in_stock, image_path, details) VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (name, cat, round(float(price), 2), int(qty), img, desc))
            conn.commit()
            return True
        except Error as e:
            print(e); return False
        finally:
            cur.close(); conn.close()

    def update_product(self, sku, name, cat, price, qty, img, desc):
        conn = self._connect()
        cur = conn.cursor()
        try:
            sql = "UPDATE inventory SET item_name=%s, category=%s, unit_price=%s, qty_in_stock=%s, image_path=%s, details=%s WHERE sku=%s"
            cur.execute(sql, (name, cat, round(float(price), 2), int(qty), img, desc, int(sku)))
            conn.commit()
            return True
        except Error as e:
            print(e); return False
        finally:
            cur.close(); conn.close()

    def remove_item(self, sku):
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM inventory WHERE sku = %s", (int(sku),))
            conn.commit()
            return True
        except Error: return False
        finally:
            cur.close(); conn.close()

    # --- CRM OPS ---
    def register_client(self, name, phone, email, c_type='Regular'):
        conn = self._connect()
        cur = conn.cursor()
        try:
            sql = "INSERT INTO clients (full_name, contact_no, email_addr, client_type) VALUES (%s, %s, %s, %s)"
            cur.execute(sql, (name, phone, email, c_type))
            conn.commit()
            return True, cur.lastrowid
        except Error as e: return False, str(e)
        finally:
            cur.close(); conn.close()

    # --- CHECKOUT OPS ---
    def process_transaction(self, staff_id, client_id, cart, subtotal, discount, total, pay_method):
        """
        Cart Keys are now 'SKU_SIZE' (e.g. '5_M', '12_42')
        """
        conn = self._connect()
        cur = conn.cursor()
        try:
            conn.start_transaction()
            
            safe_sub = round(float(subtotal), 2)
            safe_disc = round(float(discount), 2)
            safe_tot = round(float(total), 2)

            # 1. Log Sale
            sql_head = "INSERT INTO sales_log (staff_id, client_id, subtotal, discount_amount, grand_total, payment_method) VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(sql_head, (staff_id, client_id, safe_sub, safe_disc, safe_tot, pay_method))
            sale_id = cur.lastrowid

            # 2. Items
            for key, qty in cart.items():
                # Parse "SKU_SIZE" -> SKU, SIZE
                if "_" in str(key):
                    sku_str, size_val = str(key).split("_", 1)
                    sku = int(sku_str)
                else:
                    sku = int(key)
                    size_val = "N/A"

                cur.execute("SELECT unit_price, qty_in_stock FROM inventory WHERE sku = %s", (sku,))
                res = cur.fetchone()
                if not res: raise Exception("Product not found")
                price, stock = res
                
                if stock < qty: raise Exception(f"Insufficient stock for SKU {sku}")

                # Deduct Stock (Overall)
                cur.execute("UPDATE inventory SET qty_in_stock = qty_in_stock - %s WHERE sku = %s", (qty, sku))
                
                # Insert Line Item with Size
                sql_line = "INSERT INTO sales_items (sale_id, sku, qty, item_size, sold_at_price) VALUES (%s, %s, %s, %s, %s)"
                cur.execute(sql_line, (sale_id, sku, qty, size_val, price))

            conn.commit()
            return True, sale_id
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            cur.close(); conn.close()

    def get_order_details(self, sale_id):
        conn = self._connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT s.*, u.display_name as staff_name, c.full_name as client_name 
                FROM sales_log s 
                LEFT JOIN staff_users u ON s.staff_id = u.uid
                LEFT JOIN clients c ON s.client_id = c.client_id
                WHERE s.sale_id = %s
            """, (sale_id,))
            header = cur.fetchone()
            
            cur.execute("""
                SELECT i.*, p.item_name 
                FROM sales_items i 
                JOIN inventory p ON i.sku = p.sku 
                WHERE i.sale_id = %s
            """, (sale_id,))
            items = cur.fetchall()
            
            return header, items
        finally:
            cur.close(); conn.close()