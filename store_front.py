import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import datetime

# --- COLORS ---
BG_DARK = "#2d3436"
BG_LIGHT = "#dfe6e9"
ACCENT = "#00b894" # Mint Green
TEXT_COLOR = "#2d3436"

# --- PAGE 1: STORE GRID ---
class StorePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_refs = {} 

        # Header
        header = tk.Frame(self, bg=BG_DARK, height=80, padx=20)
        header.pack(fill="x")
        
        tk.Label(header, text="SMARTFIT", font=("Impact", 24), bg=BG_DARK, fg="white").pack(side="left")
        
        search_frm = tk.Frame(header, bg=BG_DARK)
        search_frm.pack(side="left", padx=40)
        self.search_var = tk.StringVar()
        entry = tk.Entry(search_frm, textvariable=self.search_var, width=30, bg="white", fg="black", font=("Arial", 12))
        entry.pack(side="left", ipady=5)
        tk.Button(search_frm, text="🔍", command=self.refresh, bg=ACCENT, fg="white", relief=tk.FLAT, font=("Arial", 10)).pack(side="left", padx=5)

        tk.Button(header, text="⟳ Refresh", command=self.refresh, bg="#636e72", fg="white", relief=tk.FLAT, font=("Arial", 10)).pack(side="right", padx=10)

        self.cart_btn = tk.Button(header, text="View Cart (0)", command=lambda: controller.show_frame("CartPage"), bg="white", fg=BG_DARK, font=("Arial", 10, "bold"))
        self.cart_btn.pack(side="right")

        # Main Content
        self.canvas = tk.Canvas(self, bg=BG_LIGHT)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=BG_LIGHT)
        
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        self.scrollbar.pack(side="right", fill="y")
        
        # Toast Notification
        self.toast = tk.Label(self, text="", bg=ACCENT, fg="white", padx=15, pady=8, font=("Arial", 10, "bold"))

    def refresh(self):
        qty_total = sum(self.controller.cart.values())
        self.cart_btn.config(text=f"View Cart ({qty_total})")

        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.image_refs = {}

        items = self.controller.db.fetch_inventory()
        query = self.search_var.get().lower()
        
        filtered = [i for i in items if query in i['item_name'].lower()]
        
        cols = 5 
        for idx, item in enumerate(filtered):
            r, c = divmod(idx, cols)
            self.create_card(item, r, c)

    def create_card(self, item, r, c):
        f = tk.Frame(self.scroll_frame, bg="white", padx=5, pady=5)
        f.grid(row=r, column=c, padx=10, pady=10, sticky="news")
        
        # Image
        path = item.get('image_path', '')
        if path and os.path.exists(path):
            try:
                pil_img = Image.open(path).resize((140, 140))
                tk_img = ImageTk.PhotoImage(pil_img)
                self.image_refs[item['sku']] = tk_img
                tk.Label(f, image=tk_img, bg="white").pack(pady=5)
            except: tk.Label(f, text="[Img]", bg="#eee", height=8, width=18).pack(pady=5)
        else:
            tk.Label(f, text="No Image", bg="#eee", height=8, width=18).pack(pady=5)

        tk.Label(f, text=item['item_name'], font=("Helvetica", 11, "bold"), bg="white", fg="#2d3436", wraplength=140).pack()
        tk.Label(f, text=f"${item['unit_price']}", font=("Arial", 10), fg=ACCENT, bg="white").pack()
        
        stk = item['qty_in_stock']
        if stk > 0:
            # SIZE SELECTION LOGIC
            cat = item['category']
            if cat == "Shoes":
                sizes = ["36", "38", "40", "42"]
            else: # Uppers, Lowers
                sizes = ["M", "L", "XL"]
            
            size_var = tk.StringVar(value=sizes[0])
            size_cb = ttk.Combobox(f, textvariable=size_var, values=sizes, state="readonly", width=5)
            size_cb.pack(pady=2)

            tk.Button(f, text="ADD +", bg=BG_DARK, fg="white", relief=tk.FLAT,
                      command=lambda s=size_var: self.add_to_cart(item, s.get())).pack(fill="x", pady=(5,0))
        else:
            tk.Label(f, text="SOLD OUT", fg="red", bg="white").pack(pady=5)

    def add_to_cart(self, item, size):
        sku = item['sku']
        # Composite Key for Cart: "SKU_SIZE"
        cart_key = f"{sku}_{size}"
        
        # Calculate total stock usage for this SKU across all sizes
        current_stock_usage = 0
        for k, v in self.controller.cart.items():
            if str(k).startswith(f"{sku}_") or str(k) == str(sku):
                current_stock_usage += v
        
        if current_stock_usage < item['qty_in_stock']:
            self.controller.cart[cart_key] = self.controller.cart.get(cart_key, 0) + 1
            self.refresh()
            self.show_toast(f"Added {item['item_name']} ({size})")
        else:
            messagebox.showwarning("Stock", "Max available stock reached for this item")

    def show_toast(self, msg):
        self.toast.config(text=msg)
        self.toast.place(relx=0.5, rely=0.05, anchor="center")
        self.after(2000, self.toast.place_forget)


# --- PAGE 2: CART ---
class CartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=BG_LIGHT)
        
        tk.Label(self, text="Shopping Bag", font=("Helvetica", 24), bg=BG_LIGHT).pack(pady=20)
        
        self.list_frame = tk.Frame(self, bg="white")
        self.list_frame.pack(fill="both", expand=True, padx=100, pady=10)
        
        btns = tk.Frame(self, bg=BG_LIGHT)
        btns.pack(pady=20)
        tk.Button(btns, text="Back to Store", command=lambda: controller.show_frame("StorePage"), bg="white", fg="black", relief=tk.FLAT, padx=20, pady=10).pack(side="left", padx=10)
        tk.Button(btns, text="Secure Checkout", bg=ACCENT, fg="white", font=("bold"), relief=tk.FLAT, padx=20, pady=10,
                  command=lambda: controller.show_frame("CheckoutPage")).pack(side="left", padx=10)

    def refresh(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        
        cart = self.controller.cart
        if not cart:
            tk.Label(self.list_frame, text="Your bag is empty.", bg="white", font=("Arial", 14)).pack(pady=50)
            return

        inventory = {i['sku']: i for i in self.controller.db.fetch_inventory()}
        
        h_frm = tk.Frame(self.list_frame, bg="#f1f2f6")
        h_frm.pack(fill="x")
        headers = ["Item Name", "Size", "Price", "Quantity", "Total", ""]
        widths = [30, 10, 15, 15, 15, 10]
        for h, w in zip(headers, widths):
            tk.Label(h_frm, text=h, bg="#f1f2f6", font=("Arial", 10, "bold"), width=w, anchor="w").pack(side="left", padx=5, pady=10)

        total = 0
        for key, qty in cart.items():
            # Parse Key
            if "_" in str(key):
                sku_str, size = str(key).split("_", 1)
                sku = int(sku_str)
            else:
                sku = int(key); size="-"

            if sku not in inventory: continue
            item = inventory[sku]
            price = float(item['unit_price'])
            line_tot = price * qty
            total += line_tot
            
            row = tk.Frame(self.list_frame, bg="white", borderwidth=0)
            row.pack(fill="x", pady=2)
            
            tk.Label(row, text=item['item_name'], bg="white", width=30, anchor="w").pack(side="left", padx=5)
            tk.Label(row, text=size, bg="white", width=10, anchor="w", font=("bold")).pack(side="left", padx=5)
            tk.Label(row, text=f"${price:.2f}", bg="white", width=15, anchor="w").pack(side="left", padx=5)
            
            q_frm = tk.Frame(row, bg="white", width=15)
            q_frm.pack(side="left", padx=5)
            tk.Button(q_frm, text="-", command=lambda k=key: self.mod_qty(k, -1)).pack(side="left")
            tk.Label(q_frm, text=qty, bg="white", width=3).pack(side="left")
            # For adding, we need to check overall stock again
            tk.Button(q_frm, text="+", command=lambda k=key, s=sku, m=item['qty_in_stock']: self.mod_qty(k, 1, m, s)).pack(side="left")
            
            tk.Label(row, text=f"${line_tot:.2f}", bg="white", width=15, anchor="w").pack(side="left", padx=20)
            tk.Button(row, text="×", bg="white", fg="red", relief=tk.FLAT, command=lambda k=key: self.mod_qty(k, -999)).pack(side="left")

        tk.Label(self.list_frame, text=f"Total: ${total:.2f}", font=("Arial", 18, "bold"), bg="white", fg=ACCENT).pack(pady=20, anchor="e", padx=50)

    def mod_qty(self, key, delta, max_s=100, sku=None):
        curr = self.controller.cart.get(key, 0)
        new_q = curr + delta
        
        if delta > 0 and sku:
            # Check overall stock usage for this SKU
            usage = 0
            for k, v in self.controller.cart.items():
                if str(k).startswith(f"{sku}_") or str(k) == str(sku):
                    usage += v
            if usage + delta > max_s:
                messagebox.showwarning("Stock", "Limit reached")
                return

        if delta == -999 or new_q <= 0:
            del self.controller.cart[key]
        else:
            self.controller.cart[key] = new_q
        self.refresh()


# --- PAGE 3: CHECKOUT ---
class CheckoutPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f5f6fa")
        self.voucher_active = False 
        
        tk.Label(self, text="Checkout", font=("Helvetica", 22), bg="#f5f6fa", fg=BG_DARK).pack(pady=15, anchor="w", padx=40)
        
        main_content = tk.Frame(self, bg="#f5f6fa")
        main_content.pack(fill="both", expand=True, padx=40, pady=10)
        
        # --- LEFT SIDE ---
        left_panel = tk.Frame(main_content, bg="#f5f6fa")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # 1. Customer Selection
        tk.Label(left_panel, text="1. Select Customer", font=("Arial", 12, "bold"), bg="#f5f6fa").pack(anchor="w", pady=(0, 5))
        cust_frm = tk.Frame(left_panel, bg="white", padx=15, pady=15, relief=tk.FLAT)
        cust_frm.pack(fill="x", pady=(0, 20))
        
        self.c_var = tk.StringVar()
        self.c_box = ttk.Combobox(cust_frm, textvariable=self.c_var, state="readonly", font=("Arial", 11))
        self.c_box.pack(fill="x", pady=5)
        self.c_box.bind("<<ComboboxSelected>>", self.on_cust_select)
        
        self.lbl_cust_info = tk.Label(cust_frm, text="No customer selected", bg="white", fg="gray")
        self.lbl_cust_info.pack(anchor="w")
        
        tk.Button(cust_frm, text="+ Create New Profile", bg="#dfe6e9", relief=tk.FLAT, command=self.quick_add).pack(anchor="e", pady=5)

        # 2. Payment Method
        tk.Label(left_panel, text="2. Payment Details", font=("Arial", 12, "bold"), bg="#f5f6fa").pack(anchor="w", pady=(0, 5))
        pay_frm = tk.Frame(left_panel, bg="white", padx=15, pady=15)
        pay_frm.pack(fill="x")
        
        tk.Label(pay_frm, text="Method:", bg="white").pack(anchor="w")
        self.pay_method = ttk.Combobox(pay_frm, values=["Cash", "Credit Card", "EFTPOS"], state="readonly")
        self.pay_method.current(0)
        self.pay_method.pack(fill="x", pady=5)

        # 3. Voucher
        tk.Label(left_panel, text="3. Voucher Code", font=("Arial", 12, "bold"), bg="#f5f6fa").pack(anchor="w", pady=(0, 5))
        v_frm = tk.Frame(left_panel, bg="white", padx=15, pady=15)
        v_frm.pack(fill="x")
        
        self.v_var = tk.StringVar()
        tk.Entry(v_frm, textvariable=self.v_var, width=20, font=("Arial", 11)).pack(side="left", padx=(0, 10))
        tk.Button(v_frm, text="Apply", command=self.apply_voucher, bg=BG_DARK, fg="white", relief=tk.FLAT).pack(side="left")

        # --- RIGHT SIDE: SUMMARY ---
        right_panel = tk.Frame(main_content, bg="white", width=300, padx=20, pady=20)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)
        
        tk.Label(right_panel, text="Order Summary", font=("Arial", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 20))
        
        self.lbl_sub = tk.Label(right_panel, text="Subtotal: $0.00", bg="white", font=("Arial", 10))
        self.lbl_sub.pack(anchor="w", pady=2)
        
        self.lbl_disc = tk.Label(right_panel, text="Discounts: -$0.00", bg="white", fg=ACCENT, font=("Arial", 10))
        self.lbl_disc.pack(anchor="w", pady=2)
        
        tk.Frame(right_panel, height=2, bg="#eee").pack(fill="x", pady=15)
        
        self.lbl_tot = tk.Label(right_panel, text="$0.00", font=("Arial", 24, "bold"), bg="white", fg=BG_DARK)
        self.lbl_tot.pack(pady=10)
        
        tk.Button(right_panel, text="CONFIRM ORDER", bg=ACCENT, fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT, height=2, command=self.process).pack(fill="x", pady=20)
        
        tk.Button(right_panel, text="Cancel", bg="white", fg="red", relief=tk.FLAT, command=lambda: controller.show_frame("CartPage")).pack()

    def refresh(self):
        self.voucher_active = False 
        self.v_var.set("")
        self.clients = self.controller.db.fetch_clients()
        self.c_box['values'] = [f"{c['client_id']} - {c['full_name']}" for c in self.clients]
        if self.c_box['values']: self.c_box.current(0)
        self.on_cust_select()

    def on_cust_select(self, e=None):
        if not self.c_box.get(): return
        idx = self.c_box.current()
        client = self.clients[idx]
        self.selected_client = client
        self.lbl_cust_info.config(text=f"Status: {client['client_type']}")
        self.calc_totals()

    def apply_voucher(self):
        code = self.v_var.get().strip()
        if code == "Jhapa5":
            if not self.voucher_active:
                self.voucher_active = True
                messagebox.showinfo("Voucher", "Jhapa5 Applied: 5% Discount!")
                self.calc_totals()
            else:
                messagebox.showinfo("Info", "Voucher already active")
        else:
            self.voucher_active = False
            messagebox.showerror("Error", "Invalid Code")
            self.calc_totals()

    def calc_totals(self):
        inventory = {i['sku']: i for i in self.controller.db.fetch_inventory()}
        sub = 0
        for k, qty in self.controller.cart.items():
            if "_" in str(k): sku = int(str(k).split("_")[0])
            else: sku = int(k)
            
            if sku in inventory: sub += float(inventory[sku]['unit_price']) * qty
        
        disc = 0
        
        # New Tiered Discount Logic
        if hasattr(self, 'selected_client'):
            c_type = self.selected_client['client_type']
            if c_type == 'Gold': disc += sub * 0.15
            elif c_type == 'Silver': disc += sub * 0.10
            elif c_type == 'Bronze': disc += sub * 0.05
        
        if self.voucher_active:
            disc += sub * 0.05
        
        self.final_total = sub - disc
        self.subtotal = sub
        self.discount_val = disc
        
        self.lbl_sub.config(text=f"Subtotal: ${sub:.2f}")
        self.lbl_disc.config(text=f"Total Discounts: -${disc:.2f}")
        self.lbl_tot.config(text=f"${self.final_total:.2f}")

    def quick_add(self):
        top = tk.Toplevel(self)
        top.title("New Client Profile")
        top.geometry("300x300")
        tk.Label(top, text="Name").pack(anchor="w", padx=10); e1 = tk.Entry(top); e1.pack(fill="x", padx=10)
        tk.Label(top, text="Phone").pack(anchor="w", padx=10); e2 = tk.Entry(top); e2.pack(fill="x", padx=10)
        tk.Label(top, text="Type").pack(anchor="w", padx=10)
        # Updated Dropdown
        cb = ttk.Combobox(top, values=["Regular", "Gold", "Silver", "Bronze"]); cb.current(0); cb.pack(fill="x", padx=10)
        def save():
            self.controller.db.register_client(e1.get(), e2.get(), "N/A", cb.get())
            top.destroy()
            self.refresh()
        tk.Button(top, text="Save Profile", command=save, bg=BG_DARK, fg="white").pack(pady=20)

    def process(self):
        if not self.controller.cart: 
            messagebox.showerror("Error", "Cart is empty")
            return
        if not hasattr(self, 'selected_client'):
            messagebox.showerror("Error", "Please select a customer")
            return

        cid = self.selected_client['client_id']
        sid = self.controller.active_user['uid']
        
        ok, oid = self.controller.db.process_transaction(
            sid, cid, self.controller.cart, self.subtotal, self.discount_val, self.final_total, self.pay_method.get()
        )
        
        if ok:
            self.controller.last_order_id = oid
            self.controller.cart = {}
            self.controller.show_frame("ReceiptPage")
        else:
            messagebox.showerror("Transaction Failed", oid)


# --- PAGE 4: RECEIPT ---
class ReceiptPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="PAYMENT SUCCESSFUL", fg=ACCENT, font=("Arial", 20, "bold")).pack(pady=30)
        
        self.txt = tk.Text(self, font=("Courier New", 10), width=45, height=20, bd=1, relief=tk.SOLID)
        self.txt.pack(pady=10)
        
        btn_frm = tk.Frame(self)
        btn_frm.pack(pady=10)
        tk.Button(btn_frm, text="Download Receipt (.txt)", bg=BG_DARK, fg="white", command=self.save_text_receipt).pack(side="left", padx=5)
        tk.Button(btn_frm, text="Next Sale", bg=ACCENT, fg="white", command=lambda: controller.show_frame("StorePage")).pack(side="left", padx=5)

    def refresh(self):
        oid = self.controller.last_order_id
        if not oid: return
        
        head, items = self.controller.db.get_order_details(oid)
        if not head: return
        
        self.receipt_content = f"""
==========================================
           SMARTFIT POS SYSTEM
==========================================
Receipt ID: {oid}
Date:       {head['sale_date']}
Staff:      {head['staff_name']}
Client:     {head['client_name']}
Payment:    {head['payment_method']}
------------------------------------------
ITEM                QTY     PRICE
------------------------------------------
"""
        for i in items:
            name_display = f"{i['item_name']} ({i['item_size']})"
            self.receipt_content += f"{name_display[:25]:<25} x{i['qty']:<3} ${i['sold_at_price']}\n"
            
        self.receipt_content += f"""------------------------------------------
Subtotal:   ${head['subtotal']}
Discount:  -${head['discount_amount']}
------------------------------------------
TOTAL:      ${head['grand_total']}
==========================================
Thank you for shopping!
"""
        
        self.txt.delete("1.0", tk.END)
        self.txt.insert("1.0", self.receipt_content)

    def save_text_receipt(self):
        filename = filedialog.asksaveasfilename(
            initialfile=f"Receipt_{self.controller.last_order_id}.txt",
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt")]
        )
        if filename:
            with open(filename, "w") as f:
                f.write(self.receipt_content)
            messagebox.showinfo("Saved", "Receipt saved successfully!")
