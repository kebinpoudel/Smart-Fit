import tkinter as tk
from tkinter import messagebox
from db_manager import SmartFitDB
from store_front import StorePage, CartPage, CheckoutPage, ReceiptPage
from stock_admin import InventoryWindow
from crm_admin import ClientWindow

class SmartFitLauncher(tk.Tk):
    def __init__(self):
        # FIX: Removed 'parent=None' here. This was causing your crash.
        super().__init__()
        self.title("SmartFit - Retail System v4.0")
        self.geometry("1200x800")
        
        self.db = SmartFitDB()
        self.active_user = None 
        self.cart = {} # {sku: qty}
        self.last_order_id = None
        
        # Navigation Container
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        # Init Login
        self.render_login()

    def render_login(self):
        for w in self.container.winfo_children(): w.destroy()
        
        # Login Design: Minimalist Dark
        bg_frame = tk.Frame(self.container, bg="#2d3436")
        bg_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        box = tk.Frame(bg_frame, padx=40, pady=40, bg="white", relief=tk.FLAT)
        box.place(relx=0.5, rely=0.5, anchor="center")
        
        # CHANGED: Login Title is now just "SMARTFIT"
        tk.Label(box, text="SMARTFIT", font=("Helvetica", 24, "bold"), bg="white", fg="#2d3436").pack(pady=(0, 20))
        
        tk.Label(box, text="Username", bg="white", fg="gray").pack(anchor="w")
        u = tk.Entry(box, font=("Arial", 12), bg="#f1f2f6", relief=tk.FLAT)
        u.pack(pady=(0, 10), fill="x", ipadx=5, ipady=5)
        
        tk.Label(box, text="Password", bg="white", fg="gray").pack(anchor="w")
        p = tk.Entry(box, show="*", font=("Arial", 12), bg="#f1f2f6", relief=tk.FLAT)
        p.pack(pady=(0, 20), fill="x", ipadx=5, ipady=5)
        
        def auth():
            usr = self.db.verify_login(u.get(), p.get())
            if usr:
                self.active_user = usr
                self.init_dashboard()
            else:
                messagebox.showerror("Access Denied", "Invalid Username or Password")

        tk.Button(box, text="LOGIN", command=auth, bg="#00b894", fg="white", font=("Arial", 11, "bold"), relief=tk.FLAT, cursor="hand2").pack(fill="x", pady=10)

    def init_dashboard(self):
        # Create all pages
        for F in (StorePage, CartPage, CheckoutPage, ReceiptPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame("StorePage")
        
        # Admin Menu Bar
        if self.active_user['role'] == 'Manager':
            menubar = tk.Menu(self)
            admin_menu = tk.Menu(menubar, tearoff=0)
            admin_menu.add_command(label="Inventory Manager", command=lambda: InventoryWindow(self, self.db))
            admin_menu.add_command(label="Client Manager", command=lambda: ClientWindow(self, self.db))
            admin_menu.add_separator()
            admin_menu.add_command(label="Logout", command=self.logout)
            menubar.add_cascade(label="Admin", menu=admin_menu)
            self.config(menu=menubar)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'refresh'):
            frame.refresh()

    def logout(self):
        self.active_user = None
        self.cart = {}
        self.config(menu=None) # clear menu
        self.render_login()

if __name__ == "__main__":
    app = SmartFitLauncher()
    app.mainloop()
