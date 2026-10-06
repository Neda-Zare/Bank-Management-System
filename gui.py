import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation

from bank_cli import (
    get_connection,
    call_function,
    call_procedure,
    hash_password,
    verify_password,
)


BG = "#f4f7fb"
SIDEBAR = "#172033"
SIDEBAR_ACTIVE = "#263653"
ACCENT = "#2563eb"
TEXT = "#172033"
MUTED = "#64748b"
WHITE = "#ffffff"
SUCCESS = "#16a34a"
DANGER = "#dc2626"


class BankGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bank Management System")
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(bg=BG)

        self.conn = None
        self.session = None
        self.current_content = None

        self.setup_styles()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_auth()

    def setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("Primary.TButton", background=ACCENT, foreground=WHITE,
                        font=("Segoe UI", 10, "bold"), padding=(14, 9))
        style.map("Primary.TButton", background=[("active", "#1d4ed8")])
        style.configure("Danger.TButton", background=DANGER, foreground=WHITE,
                        font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.configure("TEntry", padding=8, font=("Segoe UI", 10))
        style.configure("TCombobox", padding=7, font=("Segoe UI", 10))
        style.configure("Treeview", rowheight=32, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=8)
        style.map("Treeview", background=[("selected", "#dbeafe")],
                  foreground=[("selected", TEXT)])

    # ---------- Connection ----------
    def ensure_connection(self):
        if self.conn is not None:
            return True
        try:
            self.conn = get_connection()
            return True
        except Exception as exc:
            messagebox.showerror("Database Error", f"Could not connect to the database.\n\n{exc}")
            return False

    # ---------- General UI ----------
    def clear_window(self):
        for child in self.winfo_children():
            child.destroy()

    def card(self, parent, **kwargs):
        return tk.Frame(parent, bg=WHITE, highlightthickness=1,
                        highlightbackground="#e2e8f0", **kwargs)

    def label(self, parent, text, size=10, bold=False, color=TEXT, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def entry(self, parent, show=None):
        return ttk.Entry(parent, show=show, width=34)

    def add_field(self, parent, row, title, show=None):
        self.label(parent, title, 10, True).grid(row=row, column=0, sticky="w", pady=(10, 5))
        ent = self.entry(parent, show=show)
        ent.grid(row=row + 1, column=0, sticky="ew", pady=(0, 4))
        return ent

    def show_auth(self):
        self.clear_window()
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        left = tk.Frame(outer, bg=SIDEBAR, width=430)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="BANK", bg=SIDEBAR, fg="#93c5fd",
                 font=("Segoe UI", 13, "bold")).pack(pady=(110, 8))
        tk.Label(left, text="Bank Management\nSystem", bg=SIDEBAR, fg=WHITE,
                 font=("Segoe UI", 26, "bold"), justify="left", wraplength=330).pack(anchor="w", padx=55)
        tk.Label(left, text="Secure • Simple • Professional", bg=SIDEBAR, fg="#94a3b8",
                 font=("Segoe UI", 11)).pack(anchor="w", padx=58, pady=(18, 20))

        right = tk.Frame(outer, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        card = self.card(right, width=450, height=500)
        card.place(relx=.5, rely=.5, anchor="center")
        card.pack_propagate(False)

        tk.Label(card, text="Welcome back", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 23, "bold")).pack(anchor="w", padx=45, pady=(48, 4))
        tk.Label(card, text="Sign in to your banking dashboard", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=45, pady=(0, 22))

        form = tk.Frame(card, bg=WHITE)
        form.pack(fill="x", padx=45)
        username = self.add_field(form, 0, "Username")
        password = self.add_field(form, 2, "Password", show="•")

        def do_login():
            u = username.get().strip()
            p = password.get()
            if not u or not p:
                messagebox.showwarning("Login", "Please enter username and password.")
                return
            if not self.ensure_connection():
                return
            try:
                _, rows = call_function(self.conn, "SELECT * FROM get_login_credentials(%s)", (u,))
                if not rows or rows[0][0] is None:
                    messagebox.showerror("Login failed", "Username was not found.")
                    return
                user_id, role, password_hash = rows[0]
                if not verify_password(p, password_hash):
                    messagebox.showerror("Login failed", "Incorrect password.")
                    return
                self.session = {"user_id": user_id, "role": role, "username": u}
                self.show_dashboard()
            except Exception as exc:
                self.handle_db_error(exc)

        ttk.Button(card, text="Sign In", style="Primary.TButton", command=do_login).pack(
            fill="x", padx=45, pady=(20, 10))
        ttk.Button(card, text="Create a new account", command=self.show_register).pack(
            fill="x", padx=45)

        password.bind("<Return>", lambda _e: do_login())
        username.focus_set()

    def show_register(self):
        self.clear_window()
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        card = self.card(outer, width=540, height=650)
        card.place(relx=.5, rely=.5, anchor="center")
        card.pack_propagate(False)

        tk.Label(card, text="Create Account", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 23, "bold")).pack(anchor="w", padx=48, pady=(35, 3))
        tk.Label(card, text="Register as a new bank customer", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=48, pady=(0, 15))

        form = tk.Frame(card, bg=WHITE)
        form.pack(fill="x", padx=48)
        fields = {}
        labels = [("username", "Username"), ("password", "Password"),
                  ("first_name", "First name"), ("last_name", "Last name"),
                  ("birth_date", "Birth date (YYYY-MM-DD)"), ("phone", "Phone number")]
        for i, (key, title) in enumerate(labels):
            fields[key] = self.add_field(form, i * 2, title, show="•" if key == "password" else None)

        def register():
            vals = {k: v.get().strip() for k, v in fields.items()}
            if not all(vals.values()):
                messagebox.showwarning("Registration", "Please fill in all fields.")
                return
            try:
                birth = datetime.strptime(vals["birth_date"], "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Registration", "Birth date must be YYYY-MM-DD.")
                return
            if not self.ensure_connection():
                return
            try:
                call_function(self.conn, "SELECT create_user(%s, %s, %s, %s, %s, %s)",
                              (vals["username"], hash_password(vals["password"]),
                               vals["first_name"], vals["last_name"], birth, vals["phone"]))
                messagebox.showinfo("Success", "Account created successfully. You can now sign in.")
                self.show_auth()
            except Exception as exc:
                self.handle_db_error(exc)

        ttk.Button(card, text="Create Account", style="Primary.TButton", command=register).pack(
            fill="x", padx=48, pady=(18, 8))
        ttk.Button(card, text="Back to login", command=self.show_auth).pack(fill="x", padx=48)

    # ---------- Dashboard ----------
    def show_dashboard(self):
        self.clear_window()
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=245)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="BANK.", bg=SIDEBAR, fg=WHITE,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=25, pady=(30, 5))
        tk.Label(self.sidebar, text=self.session["role"].upper(), bg=SIDEBAR, fg="#93c5fd",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=27, pady=(0, 25))

        self.nav_frame = tk.Frame(self.sidebar, bg=SIDEBAR)
        self.nav_frame.pack(fill="both", expand=True)
        self.build_navigation()

        ttk.Button(self.sidebar, text="Sign out", command=self.logout).pack(fill="x", padx=22, pady=(10, 25))

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self.show_home()

    def nav_button(self, text, command):
        btn = tk.Button(self.nav_frame, text=text, command=command, anchor="w",
                        bg=SIDEBAR, fg="#cbd5e1", activebackground=SIDEBAR_ACTIVE,
                        activeforeground=WHITE, relief="flat", bd=0,
                        font=("Segoe UI", 10), padx=25, pady=11, cursor="hand2")
        btn.pack(fill="x")

    def build_navigation(self):
        role = self.session["role"]
        self.nav_button("⌂   Dashboard", self.show_home)
        if role == "User":
            self.nav_button("▣   My Accounts", self.user_accounts)
            self.nav_button("↕   Transactions", self.transaction_form)
            self.nav_button("$   Request Loan", self.loan_request)
            self.nav_button("▤   My Loans", self.user_loans)
            self.nav_button("✓   Loan Payment", self.loan_payment)
        else:
            self.nav_button("👥   Manage Users", self.manage_users)
            self.nav_button("▣   Manage Accounts", self.manage_accounts)
            self.nav_button("$   Manage Loans", self.manage_loans)
            self.nav_button("✓   Loan Payments", self.manage_payments)
            if role == "Admin":
                self.nav_button("★   Manage Employees", self.manage_employees)

    def clear_main(self):
        for child in self.main.winfo_children():
            child.destroy()

    def page_header(self, title, subtitle=""):
        self.clear_main()
        top = tk.Frame(self.main, bg=BG)
        top.pack(fill="x", padx=35, pady=(30, 15))
        tk.Label(top, text=title, bg=BG, fg=TEXT,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(top, text=subtitle, bg=BG, fg=MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))
        return top

    def show_home(self):
        self.page_header(f"Hello, {self.session['username']} 👋", "Welcome to your banking dashboard.")
        body = tk.Frame(self.main, bg=BG)
        body.pack(fill="both", expand=True, padx=35, pady=10)

        role = self.session["role"]
        cards = [
            ("Account", "Manage banking accounts"),
            ("Transactions", "Deposit or withdraw money"),
            ("Loans", "View and manage loans"),
        ]
        if role != "User":
            cards = [
                ("Users", "Manage bank customers"),
                ("Accounts", "Manage all accounts"),
                ("Loans", "Manage bank loans"),
                ("Payments", "Manage loan payments"),
            ]
            if role == "Admin":
                cards.append(("Employees", "Create bank employees"))

        for i, (title, desc) in enumerate(cards):
            c = self.card(body, width=220, height=125)
            c.grid(row=0, column=i, padx=(0, 15), sticky="nsew")
            c.grid_propagate(False)
            tk.Label(c, text=title, bg=WHITE, fg=TEXT,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
            tk.Label(c, text=desc, bg=WHITE, fg=MUTED,
                     font=("Segoe UI", 9), wraplength=180, justify="left").pack(anchor="w", padx=20)

    # ---------- Table helpers ----------
    def show_table(self, columns, rows, title="Results"):
        self.page_header(title, f"{len(rows)} record(s) found")
        frame = self.card(self.main)
        frame.pack(fill="both", expand=True, padx=35, pady=(0, 30))

        table = ttk.Treeview(frame, columns=list(range(len(columns))), show="headings")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        table.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 0))
        vsb.grid(row=0, column=1, sticky="ns", pady=(12, 0))
        hsb.grid(row=1, column=0, sticky="ew", padx=12)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        for i, col in enumerate(columns):
            table.heading(i, text=str(col))
            table.column(i, width=max(110, min(220, len(str(col)) * 12 + 50)), anchor="center")
        for row in rows:
            table.insert("", "end", values=[str(v) if v is not None else "" for v in row])

        if not rows:
            tk.Label(frame, text="No records found.", bg=WHITE, fg=MUTED,
                     font=("Segoe UI", 11)).place(relx=.5, rely=.5, anchor="center")

        return table

    def run_query(self, sql, params=(), title="Results"):
        try:
            cols, rows = call_function(self.conn, sql, params)
            self.show_table(cols, rows, title)
        except Exception as exc:
            self.handle_db_error(exc)

    # ---------- User ----------
    def user_accounts(self):
        self.run_query("SELECT * FROM search_account_by_user_id(%s)",
                       (self.session["user_id"],), "My Accounts")

    def user_loans(self):
        self.page_header("My Loans", "Enter an account number to view its loans.")
        form = self.form_card()
        num = self.form_entry(form, "Account number")
        ttk.Button(form, text="Search", style="Primary.TButton",
                    command=lambda: self.run_query("SELECT * FROM loans WHERE account_number = %s",
                                                   (num.get().strip(),), "My Loans")).pack(pady=15)

    def transaction_form(self):
        self.page_header("Transaction", "Deposit or withdraw money from an account.")
        form = self.form_card()
        account = self.form_entry(form, "Account number")
        typ = self.form_combo(form, "Transaction type", ["income", "withdraw"])
        amount = self.form_entry(form, "Amount")
        ttk.Button(form, text="Submit Transaction", style="Primary.TButton",
                    command=lambda: self.do_transaction(account, typ, amount)).pack(pady=18)

    def do_transaction(self, account, typ, amount):
        try:
            value = self.decimal_value(amount.get())
            call_function(self.conn, "SELECT make_transaction(%s, %s, %s)",
                          (account.get().strip(), value, typ.get()))
            messagebox.showinfo("Success", "Transaction completed successfully.")
        except Exception as exc:
            self.handle_db_error(exc)

    def loan_request(self):
        self.page_header("Request Loan", "Submit a new loan request.")
        form = self.form_card()
        account = self.form_entry(form, "Account number")
        amount = self.form_entry(form, "Requested amount")
        req_date = self.form_entry(form, "Request date (YYYY-MM-DD)")
        ttk.Button(form, text="Check Approval", style="Primary.TButton",
                    command=lambda: self.do_loan_request(account, amount, req_date)).pack(pady=18)

    def do_loan_request(self, account, amount, req_date):
        try:
            value = self.decimal_value(amount.get())
            dt = self.date_value(req_date.get())
            _, rows = call_function(self.conn, "SELECT check_loan_approval(%s, %s, %s)",
                                    (dt, account.get().strip(), value))
            approved = bool(rows[0][0])
            messagebox.showinfo("Loan decision", "Loan request approved ✓" if approved else "Loan request rejected ✕")
        except Exception as exc:
            self.handle_db_error(exc)

    def loan_payment(self):
        self.page_header("Loan Payment", "Pay an installment for one of your loans.")
        form = self.form_card()
        loan = self.form_entry(form, "Loan ID")
        amount = self.form_entry(form, "Payment amount")
        ttk.Button(form, text="Pay Installment", style="Primary.TButton",
                    command=lambda: self.do_loan_payment(loan, amount)).pack(pady=18)

    def do_loan_payment(self, loan, amount):
        try:
            value = self.decimal_value(amount.get())
            call_procedure(self.conn, "CALL make_loan_payment(%s, %s)", (loan.get().strip(), value))
            messagebox.showinfo("Success", "Loan payment completed successfully.")
        except Exception as exc:
            self.handle_db_error(exc)

    # ---------- Employee/Admin ----------
    def manage_users(self):
        self.page_header("User Management", "Search, create, update or delete users.")
        self.action_bar([
            ("All Users", lambda: self.run_query("SELECT * FROM read_users()", title="All Users")),
            ("Search Phone", self.search_user_phone),
            ("Search Username", self.search_username),
            ("Create User", self.register_admin_user),
            ("Update User", self.update_user),
            ("Delete User", self.delete_user),
        ])

    def manage_accounts(self):
        self.page_header("Account Management", "Manage all bank accounts.")
        self.action_bar([
            ("All Accounts", lambda: self.run_query("SELECT * FROM read_accounts()", title="All Accounts")),
            ("Search Account", self.search_account),
            ("Search User", self.search_accounts_user),
            ("Create Account", self.create_account),
            ("Update Account", self.update_account),
            ("Delete Account", self.delete_account),
        ])

    def manage_loans(self):
        self.page_header("Loan Management", "Manage bank loans.")
        self.action_bar([
            ("All Loans", lambda: self.run_query("SELECT * FROM read_loans()", title="All Loans")),
            ("Create Loan", self.create_loan),
            ("Update Loan", self.update_loan),
            ("Delete Loan", self.delete_loan),
        ])

    def manage_payments(self):
        self.page_header("Loan Payments", "Manage loan installments.")
        self.action_bar([
            ("All Payments", lambda: self.run_query("SELECT * FROM read_loan_payments()", title="All Payments")),
            ("Sort by Date", lambda: self.run_query("SELECT * FROM sort_loan_payments_by_date()", title="Payments by Date")),
            ("Create Payment", self.create_payment),
            ("Update Payment", self.update_payment),
            ("Delete Payment", self.delete_payment),
        ])

    def action_bar(self, actions):
        holder = self.card(self.main)
        holder.pack(fill="x", padx=35, pady=10)
        for i, (text, cmd) in enumerate(actions):
            ttk.Button(holder, text=text, command=cmd).grid(row=i // 3, column=i % 3,
                                                             padx=12, pady=12, sticky="ew")
        for i in range(3):
            holder.grid_columnconfigure(i, weight=1)

    def popup_form(self, title, fields, submit_text, submit):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("480x560")
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()
        card = self.card(win)
        card.pack(fill="both", expand=True, padx=25, pady=25)
        tk.Label(card, text=title, bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=28, pady=(25, 15))
        entries = {}
        for key, label_text, show in fields:
            holder = tk.Frame(card, bg=WHITE)
            holder.pack(fill="x", padx=28, pady=5)
            tk.Label(holder, text=label_text, bg=WHITE, fg=TEXT,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
            ent = ttk.Entry(holder, show=show if show else None)
            ent.pack(fill="x")
            entries[key] = ent
        ttk.Button(card, text=submit_text, style="Primary.TButton",
                    command=lambda: submit(entries, win)).pack(fill="x", padx=28, pady=22)
        return win

    def form_card(self):
        c = self.card(self.main)
        c.pack(fill="x", padx=35, pady=10)
        inner = tk.Frame(c, bg=WHITE)
        inner.pack(fill="x", padx=30, pady=25)
        return inner

    def form_entry(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 4))
        e = ttk.Entry(parent, width=45)
        e.pack(fill="x")
        return e

    def form_combo(self, parent, text, values):
        tk.Label(parent, text=text, bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 4))
        c = ttk.Combobox(parent, values=values, state="readonly", width=42)
        c.current(0)
        c.pack(fill="x")
        return c

    def search_user_phone(self):
        self.simple_query_popup("Search User by Phone", "Phone number", "SELECT * FROM search_users_by_phone_number(%s)", "Users")

    def search_username(self):
        self.simple_query_popup("Search User", "Username contains", "SELECT * FROM filter_users_by_username(%s)", "Users")

    def search_account(self):
        self.simple_query_popup("Search Account", "Account number", "SELECT * FROM search_account_by_account_number(%s)", "Accounts")

    def search_accounts_user(self):
        self.simple_query_popup("Search Accounts by User", "User ID", "SELECT * FROM search_account_by_user_id(%s)", "Accounts")

    def simple_query_popup(self, title, field, sql, result_title):
        def submit(e, win):
            value = e["value"].get().strip()
            if not value:
                messagebox.showwarning("Input", "Please enter a value.", parent=win)
                return
            win.destroy()
            self.run_query(sql, (value,), result_title)
        self.popup_form(title, [("value", field, None)], "Search", submit)

    def register_admin_user(self):
        fields = [("username", "Username", None), ("password", "Password", "•"),
                  ("first", "First name", None), ("last", "Last name", None),
                  ("birth", "Birth date (YYYY-MM-DD)", None), ("phone", "Phone", None)]
        def submit(e, win):
            try:
                dt = self.date_value(e["birth"].get())
                call_function(self.conn, "SELECT create_user(%s, %s, %s, %s, %s, %s)",
                              (e["username"].get().strip(), hash_password(e["password"].get()),
                               e["first"].get().strip(), e["last"].get().strip(), dt, e["phone"].get().strip()))
                win.destroy(); messagebox.showinfo("Success", "User created successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Create User", fields, "Create", submit)

    def update_user(self):
        fields = [("id", "User ID", None), ("username", "New username", None), ("password", "New password", "•")]
        def submit(e, win):
            try:
                call_function(self.conn, "SELECT update_user(%s, %s, %s)",
                              (e["id"].get().strip(), e["username"].get().strip(), hash_password(e["password"].get())))
                win.destroy(); messagebox.showinfo("Success", "User updated successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Update User", fields, "Update", submit)

    def delete_user(self):
        self.confirm_delete("Delete User", "User ID", "SELECT delete_user(%s)", "User deleted successfully.")

    def create_account(self):
        if not self.ensure_connection():
            return

        # Load existing users so the employee does not have to enter a user ID manually.
        try:
            _, rows = call_function(
                self.conn,
                "SELECT user_id, username, first_name, last_name FROM users ORDER BY user_id"
            )
        except Exception as exc:
            self.handle_db_error(exc)
            return

        if not rows:
            messagebox.showwarning(
                "Create Account",
                "There are no users available. Create a user first."
            )
            return

        win = tk.Toplevel(self)
        win.title("Create Account")
        win.geometry("480x590")
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()

        card = self.card(win)
        card.pack(fill="both", expand=True, padx=25, pady=25)

        tk.Label(card, text="Create Account", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(
                     anchor="w", padx=28, pady=(25, 15))

        # Account number
        tk.Label(card, text="Account number", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(5, 4))
        account_entry = ttk.Entry(card)
        account_entry.pack(fill="x", padx=28)

        # Initial balance
        tk.Label(card, text="Initial balance", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(12, 4))
        balance_entry = ttk.Entry(card)
        balance_entry.pack(fill="x", padx=28)

        # Account name
        tk.Label(card, text="Account name", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(12, 4))
        name_entry = ttk.Entry(card)
        name_entry.pack(fill="x", padx=28)

        # User dropdown
        tk.Label(card, text="Owner user", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(12, 4))

        user_map = {}
        user_options = []
        for row in rows:
            user_id, username, first_name, last_name = row
            display_name = f"{first_name} {last_name} ({username})".strip()
            user_map[display_name] = user_id
            user_options.append(display_name)

        user_combo = ttk.Combobox(
            card, values=user_options, state="readonly", width=42
        )
        user_combo.pack(fill="x", padx=28)
        user_combo.current(0)

        tk.Label(
            card,
            text="Select the customer who will own this account.",
            bg=WHITE, fg=MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w", padx=28, pady=(4, 0))

        def submit():
            account_number = account_entry.get().strip()
            balance = balance_entry.get().strip()
            account_name = name_entry.get().strip()
            selected_user = user_combo.get()

            if not account_number or not balance or not account_name or not selected_user:
                messagebox.showwarning(
                    "Input", "Please fill in all fields.", parent=win
                )
                return

            try:
                user_id = user_map[selected_user]
                call_function(
                    self.conn,
                    "SELECT create_account(%s, %s, %s, %s)",
                    (account_number, self.decimal_value(balance), account_name, user_id)
                )
                win.destroy()
                messagebox.showinfo(
                    "Success", "Account created successfully."
                )
            except Exception as exc:
                self.handle_db_error(exc, win)

        ttk.Button(
            card, text="Create", style="Primary.TButton", command=submit
        ).pack(fill="x", padx=28, pady=22)

    def update_account(self):
        fields = [("num", "Account number", None), ("balance", "New balance", None), ("name", "New name", None)]
        def submit(e, win):
            try:
                call_function(self.conn, "SELECT update_account(%s, %s, %s)",
                              (e["num"].get().strip(), self.decimal_value(e["balance"].get()), e["name"].get().strip()))
                win.destroy(); messagebox.showinfo("Success", "Account updated successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Update Account", fields, "Update", submit)

    def delete_account(self):
        self.confirm_delete("Delete Account", "Account number", "SELECT delete_account(%s)", "Account deleted successfully.")

    def create_loan(self):
        fields = [("num", "Account number", None), ("paid", "Paid amount", None),
                  ("start", "Start date (YYYY-MM-DD)", None), ("due", "Due date (YYYY-MM-DD)", None),
                  ("total", "Total loan", None), ("ret", "Repayment amount", None)]
        def submit(e, win):
            try:
                call_function(self.conn, "SELECT create_loan(%s, %s, %s, %s, %s, %s)",
                              (e["num"].get().strip(), self.decimal_value(e["paid"].get()),
                               self.date_value(e["start"].get()), self.date_value(e["due"].get()),
                               self.decimal_value(e["total"].get()), self.decimal_value(e["ret"].get())))
                win.destroy(); messagebox.showinfo("Success", "Loan created successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Create Loan", fields, "Create", submit)

    def update_loan(self):
        fields = [("id", "Loan ID", None), ("num", "Account number", None), ("paid", "Paid amount", None),
                  ("start", "Start date (YYYY-MM-DD)", None), ("due", "Due date (YYYY-MM-DD)", None),
                  ("total", "Total loan", None), ("ret", "Repayment amount", None)]
        def submit(e, win):
            try:
                call_function(self.conn, "SELECT update_loan(%s, %s, %s, %s, %s, %s, %s)",
                              (e["id"].get().strip(), e["num"].get().strip(), self.decimal_value(e["paid"].get()),
                               self.date_value(e["start"].get()), self.date_value(e["due"].get()),
                               self.decimal_value(e["total"].get()), self.decimal_value(e["ret"].get())))
                win.destroy(); messagebox.showinfo("Success", "Loan updated successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Update Loan", fields, "Update", submit)

    def delete_loan(self):
        self.confirm_delete("Delete Loan", "Loan ID", "SELECT delete_loan(%s)", "Loan deleted successfully.")

    def create_payment(self):
        fields = [("lid", "Loan ID", None), ("month", "Payment month (YYYY-MM-DD)", None), ("amount", "Amount", None)]
        def submit(e, win):
            try:
                call_function(self.conn, "SELECT create_loan_payment(%s, %s, %s)",
                              (e["lid"].get().strip(), self.date_value(e["month"].get()), self.decimal_value(e["amount"].get())))
                win.destroy(); messagebox.showinfo("Success", "Payment created successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Create Payment", fields, "Create", submit)

    def update_payment(self):
        fields = [("id", "Payment ID", None), ("month", "Payment month (YYYY-MM-DD)", None), ("amount", "Amount", None)]
        def submit(e, win):
            try:
                call_function(self.conn, "SELECT update_loan_payment(%s, %s, %s)",
                              (e["id"].get().strip(), self.date_value(e["month"].get()), self.decimal_value(e["amount"].get())))
                win.destroy(); messagebox.showinfo("Success", "Payment updated successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Update Payment", fields, "Update", submit)

    def delete_payment(self):
        self.confirm_delete("Delete Payment", "Payment ID", "SELECT delete_loan_payment(%s)", "Payment deleted successfully.")

    def confirm_delete(self, title, field, sql, success):
        def submit(e, win):
            value = e["value"].get().strip()
            if not value:
                messagebox.showwarning("Input", "Please enter a value.", parent=win); return
            if not messagebox.askyesno("Confirm deletion", f"Delete {value}?", parent=win): return
            try:
                call_function(self.conn, sql, (value,))
                win.destroy(); messagebox.showinfo("Success", success)
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form(title, [("value", field, None)], "Delete", submit)

    def manage_employees(self):
        self.page_header("Employee Management", "Create a new employee account.")
        self.action_bar([("Create Employee", self.create_employee)])

    def create_employee(self):
        fields = [("username", "Username", None), ("password", "Password", "•"),
                  ("first", "First name", None), ("middle", "Middle initial (optional)", None),
                  ("last", "Last name", None), ("admin", "Admin? (yes/no)", None)]
        def submit(e, win):
            try:
                admin = e["admin"].get().strip().lower() in ("yes", "y", "true", "1")
                call_function(self.conn, "SELECT create_employee(%s, %s, %s, %s, %s, %s)",
                              (e["username"].get().strip(), hash_password(e["password"].get()),
                               e["first"].get().strip(), (e["middle"].get().strip()[:1] or None),
                               e["last"].get().strip(), admin))
                win.destroy(); messagebox.showinfo("Success", "Employee created successfully.")
            except Exception as exc: self.handle_db_error(exc, win)
        self.popup_form("Create Employee", fields, "Create", submit)

    # ---------- Validation / errors ----------
    @staticmethod
    def decimal_value(raw):
        try:
            value = Decimal(raw.strip())
            if value < 0:
                raise ValueError("Amount cannot be negative.")
            return value
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(str(exc) or "Invalid number.")

    @staticmethod
    def date_value(raw):
        try:
            return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD.")

    def handle_db_error(self, exc, parent=None):
        text = getattr(exc, "pgerror", None) or str(exc)
        messagebox.showerror("Error", text, parent=parent)

    def logout(self):
        self.session = None
        self.show_auth()

    def on_close(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = BankGUI()
    app.mainloop()