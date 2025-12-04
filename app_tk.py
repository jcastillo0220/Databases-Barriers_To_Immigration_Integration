import os
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector as mysql

# Optional .env support
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DB_CFG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "4421"),
    "database": os.getenv("DB_NAME", "Immigrant_Integration"),
    "autocommit": True,
}

def get_conn():
    return mysql.connect(**DB_CFG)

def run_select(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        conn.close()

def run_exec(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def fill_tree(tree: ttk.Treeview, rows):
    tree.delete(*tree.get_children())
    if not rows:
        tree["columns"] = []
        tree["show"] = "tree"
        return
    cols = list(rows[0].keys())
    tree["columns"] = cols
    tree["show"] = "headings"
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="w", width=140)
    for r in rows:
        tree.insert("", "end", values=[r.get(c, "") for c in cols])

# --------------------------------------------------------------------

# Able to add hints to entries
def add_hint(entry_widget, hint_text):
    entry_widget.insert(0, hint_text)
    entry_widget.config(foreground="gray")

    def on_focus_in(event):
        if entry_widget.get() == hint_text:
            entry_widget.delete(0, tk.END)
            entry_widget.config(foreground="black")

    def on_focus_out(event):
        if not entry_widget.get():
            entry_widget.insert(0, hint_text)
            entry_widget.config(foreground="gray")

    entry_widget.bind("<FocusIn>", on_focus_in)
    entry_widget.bind("<FocusOut>", on_focus_out)

# Validating that all fields are filled in
def validate_fields(fields):
    for label, value in fields.items():
        if not value.strip() or value.strip().startswith("e.g.") or value.strip().startswith("Select") or value.strip().startswith("i.e."):
            messagebox.showerror("Missing Input", f"Please enter a valid value for '{label}'.")
            return False
    return True

# For dates that have None into Null
def sanitize_date(value):
    value = value.strip()
    return None if value.lower() in ("none", "") else value

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Immigrant Integration Database")
        self.geometry("1200x750")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.tab_imm = ttk.Frame(nb)
        self.tab_custody = ttk.Frame(nb)
        self.tab_legal = ttk.Frame(nb)
        self.tab_country = ttk.Frame(nb)
        self.tab_analytics = ttk.Frame(nb)

        nb.add(self.tab_imm, text="👤 Immigrants (CRUD)")
        nb.add(self.tab_custody, text="⚖️ Custody Status (CRUD)")
        nb.add(self.tab_legal, text="📑 Legal Representation (CRUD)")
        nb.add(self.tab_country, text="🌎 Country of Origin (CRUD)")
        nb.add(self.tab_analytics, text="📊 Analytics")

        self.build_immigrants()
        self.build_custody()
        self.build_legal()
        self.build_country()
        self.build_analytics()

    # ----------------------------------------------------------------
    # 1️⃣ Immigrants CRUD
    def build_immigrants(self):
        frm = ttk.Frame(self.tab_imm, padding=8)
        frm.pack(fill="both", expand=True)

        lf = ttk.LabelFrame(frm, text="Add / Update Immigrant")
        lf.pack(fill="x", pady=6)

        self.i_id = tk.StringVar()
        self.i_case = tk.StringVar()
        self.i_age = tk.StringVar()
        self.i_gender = tk.StringVar()
        self.i_arrival = tk.StringVar()
        self.cmb_country = ttk.Combobox(lf, state="readonly", width=30)
        self.cmb_custody = ttk.Combobox(lf, state="readonly", width=30)
        self.cmb_legal = ttk.Combobox(lf, state="readonly", width=30)

        ttk.Label(lf, text="Case ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(lf, textvariable=self.i_case, width=20).grid(row=0, column=1, padx=5)
        ttk.Label(lf, text="Age").grid(row=0, column=2, sticky="w")
        ttk.Entry(lf, textvariable=self.i_age, width=8).grid(row=0, column=3, padx=5)
        ttk.Label(lf, text="Gender").grid(row=0, column=4, sticky="w")
        ttk.Entry(lf, textvariable=self.i_gender, width=10).grid(row=0, column=5, padx=5)
        ttk.Label(lf, text="Arrival Year").grid(row=0, column=6, sticky="w")
        ttk.Entry(lf, textvariable=self.i_arrival, width=10).grid(row=0, column=7, padx=5)

        ttk.Label(lf, text="Country").grid(row=1, column=0, sticky="w")
        self.cmb_country.grid(row=1, column=1, padx=5)
        ttk.Label(lf, text="Custody").grid(row=1, column=2, sticky="w")
        self.cmb_custody.grid(row=1, column=3, padx=5)
        ttk.Label(lf, text="Legal").grid(row=1, column=4, sticky="w")
        self.cmb_legal.grid(row=1, column=5, padx=5)

        btns = ttk.Frame(lf); btns.grid(row=2, column=0, columnspan=8, pady=5, sticky="w")
        ttk.Button(btns, text="Create", command=self.imm_create).pack(side="left", padx=4)
        ttk.Button(btns, text="Update Selected", command=self.imm_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete Selected", command=self.imm_delete).pack(side="left", padx=4)
        ttk.Button(btns, text="Refresh", command=self.imm_refresh).pack(side="left", padx=4)

        self.tree_imm = ttk.Treeview(frm, height=18)
        self.tree_imm.pack(fill="both", expand=True)
        self.tree_imm.bind("<<TreeviewSelect>>", self.imm_on_select)

        self._reload_dropdowns()
        self.imm_refresh()

    def _reload_dropdowns(self):
        # Reload data for combo boxes
        countries = run_select("SELECT country_id, country_name FROM CountryOfOrigin ORDER BY country_name")
        custodies = run_select("SELECT custody_id, custody_type FROM CustodyStatus ORDER BY custody_id")
        legals = run_select("SELECT legal_id, representation_status FROM LegalRepresentation ORDER BY legal_id")

        self._country_lookup = {f"{r['country_name']}": r['country_id'] for r in countries}
        self._custody_lookup = {f"{r['custody_type']}": r['custody_id'] for r in custodies}
        self._legal_lookup = {f"{r['representation_status']}": r['legal_id'] for r in legals}

        self.cmb_country["values"] = list(self._country_lookup.keys())
        self.cmb_custody["values"] = list(self._custody_lookup.keys())
        self.cmb_legal["values"] = list(self._legal_lookup.keys())

    def imm_refresh(self):
        rows = run_select("""
            SELECT i.immigrant_id, i.case_id, i.age, i.gender, 
                   c.country_name, cs.custody_type, l.representation_status, i.arrival_year
            FROM Immigrants i
            LEFT JOIN CountryOfOrigin c ON c.country_id=i.country_id
            LEFT JOIN CustodyStatus cs ON cs.custody_id=i.custody_id
            LEFT JOIN LegalRepresentation l ON l.legal_id=i.legal_id
            ORDER BY i.immigrant_id
        """)
        fill_tree(self.tree_imm, rows)

        max_id = run_select("SELECT MAX(immigrant_id) AS max_id FROM Immigrants")[0]["max_id"] or 0
        run_exec("ALTER TABLE Immigrants AUTO_INCREMENT = %s", (max_id + 1,))

    def imm_on_select(self, _=None):
        sel = self.tree_imm.selection()
        if not sel: return
        vals = self.tree_imm.item(sel[0], "values")
        cols = self.tree_imm["columns"]
        row = dict(zip(cols, vals))
        self.i_id.set(row.get("immigrant_id", ""))
        self.i_case.set(row.get("case_id", ""))
        self.i_age.set(str(row.get("age", "")))
        self.i_gender.set(row.get("gender", ""))
        self.i_arrival.set(str(row.get("arrival_year", "")))
        self.cmb_country.set(row.get("country_name", ""))
        self.cmb_custody.set(row.get("custody_type", ""))
        self.cmb_legal.set(row.get("representation_status", ""))

    def imm_create(self):
        fields = {
            "Case ID": self.i_case.get(),
            "Age": self.i_age.get(),
            "Gender": self.i_gender.get(),
            "Arrival Year": self.i_arrival.get(),
            "Country": self.cmb_country.get(),
            "Custody": self.cmb_custody.get(),
            "Legal": self.cmb_legal.get()
        }
        if not validate_fields(fields):
            return
        try:
            existing = run_select("SELECT 1 FROM Immigrants WHERE case_id=%s", (self.i_case.get(),))
            if existing:
                messagebox.showerror("Duplicate Case", "This case ID already exists.")
                return
            # Creating immigrant
            run_exec("""INSERT INTO immigrants (case_id, age, gender, country_id, custody_id, legal_id, arrival_year)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                     (self.i_case.get(), int(self.i_age.get() or 0), self.i_gender.get(),
                      self._country_lookup.get(self.cmb_country.get()),
                      self._custody_lookup.get(self.cmb_custody.get()),
                      self._legal_lookup.get(self.cmb_legal.get()),
                      int(self.i_arrival.get() or 0)))
            messagebox.showinfo("Success", "Immigrant added.")

            self.show_custody_popup(self.i_case.get(), self.cmb_custody.get())
            self.show_lawyer_popup(self.i_case.get(), self.cmb_legal.get())

            self.imm_refresh()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Allowing user to populate custody status table when creating an immigrant
    def show_custody_popup(self, case_id, custody_type):
        popup = tk.Toplevel(self)
        popup.title("Enter Custody Details (2)")
        popup.geometry("400x250")
        popup.columnconfigure(1, weight=1)
        popup.grab_set()

        # For Dropdown
        custody_outcome = ["Pending", "Resolved", "Awaiting Hearing", "Asylum Granted", "Removed"]

        c_type = tk.StringVar(value=custody_type)
        c_fac = tk.StringVar()
        c_rel = tk.StringVar()
        c_out = tk.StringVar()

        ttk.Label(popup, text="Custody Type").grid(row=0, column=0)
        ttk.Entry(popup, textvariable=c_type, state="readonly").grid(row=0, column=1)

        ttk.Label(popup, text="Facility").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        entry_fac = ttk.Entry(popup, textvariable=c_fac)
        entry_fac.grid(row=1, column=1, sticky="ew", padx=10, pady=6)
        add_hint(entry_fac, "e.g. Houston SPC")

        ttk.Label(popup, text="Release Date (YYYY-MM-DD)").grid(row=2, column=0, sticky="w", padx=10, pady=6)
        entry_rel = ttk.Entry(popup, textvariable=c_rel)
        entry_rel.grid(row=2, column=1, sticky="ew", padx=10, pady=6)
        add_hint(entry_rel, "e.g. 2025-11-30 or None")

        ttk.Label(popup, text="Outcome").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        cmb_outcome = ttk.Combobox(popup, textvariable=c_out, values=custody_outcome, state="readonly")
        cmb_outcome.grid(row=3, column=1, sticky="ew", padx=10, pady=6)

        def save():
            fields = {
                "Custody Type": c_type.get(),
                "Facility": c_fac.get(),
                "Release Date": c_rel.get(),
                "Outcome": c_out.get()
            }
            if not validate_fields(fields):
                return

            try:
                run_exec("""INSERT INTO CustodyStatus (case_id, custody_type, detention_facility, release_date, custody_outcome)
                            VALUES (%s, %s, %s, %s, %s)""",
                         (case_id, c_type.get(), c_fac.get(), sanitize_date(c_rel.get()), c_out.get()))
                self.cust_refresh()
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(popup, text="Save", command=save).grid(row=4, column=0, columnspan=2, pady=10)

    # Allowing user to populate legal representation table when creating an immigrant
    def show_lawyer_popup(self, case_id, lawyer_status):
        popup = tk.Toplevel(self)
        popup.title("Enter Legal Representation (1)")
        popup.geometry("400x250")
        popup.columnconfigure(1, weight=1)
        popup.grab_set()

        l_status = tk.StringVar(value=lawyer_status)
        l_att = tk.StringVar()
        l_org = tk.StringVar()
        l_date = tk.StringVar()

        ttk.Label(popup, text="Status").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(popup, textvariable=l_status, state="readonly").grid(row=0, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(popup, text="Attorney").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        entry_att = ttk.Entry(popup, textvariable=l_att)
        entry_att.grid(row=1, column=1, sticky="ew", padx=10, pady=6)
        add_hint(entry_att, "e.g. Thomas J. Henry")

        ttk.Label(popup, text="Organization").grid(row=2, column=0, sticky="w", padx=10, pady=6)
        entry_org = ttk.Entry(popup, textvariable=l_org)
        entry_org.grid(row=2, column=1, sticky="ew", padx=10, pady=6)
        add_hint(entry_org, "e.g. Catholic Charities")

        ttk.Label(popup, text="Hearing Date (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        entry_date = ttk.Entry(popup, textvariable=l_date)
        entry_date.grid(row=3, column=1, sticky="ew", padx=10, pady=6)
        add_hint(entry_date, "e.g. 2027-12-15")

        def save():
            fields = {
                "Status": l_status.get(),
                "Attorney": l_att.get(),
                "Organization": l_org.get(),
                "Hearing Date": l_date.get()
            }
            if not validate_fields(fields):
                return

            try:
                run_exec("""INSERT INTO LegalRepresentation (case_id, representation_status, attorney_name, organization, hearing_date)
                            VALUES (%s, %s, %s, %s, %s)""",
                         (case_id, l_status.get(), l_att.get(), l_org.get(), l_date.get() or None))
                self.legal_refresh()
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(popup, text="Save", command=save).grid(row=4, column=0, columnspan=2, pady=10)

    def imm_update(self):
        sel = self.tree_imm.selection()
        if not sel:
            messagebox.showwarning("Select row", "Pick a row first.")
            return
        imm_id = self.tree_imm.item(sel[0], "values")[0]

        fields = {
            "Case ID": self.i_case.get(),
            "Age": self.i_age.get(),
            "Gender": self.i_gender.get(),
            "Arrival Year": self.i_arrival.get(),
            "Country": self.cmb_country.get(),
            "Custody": self.cmb_custody.get(),
            "Legal": self.cmb_legal.get()
        }
        if not validate_fields(fields):
            return

        try:
            run_exec("""UPDATE Immigrants
                        SET age=%s, gender=%s, arrival_year=%s
                        WHERE immigrant_id=%s""",
                     (int(self.i_age.get() or 0), self.i_gender.get(), int(self.i_arrival.get() or 0), imm_id))
            messagebox.showinfo("Updated", "Record updated.")
            self.imm_refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def imm_delete(self):
        sel = self.tree_imm.selection()
        if not sel: return
        case_id = self.tree_imm.item(sel[0], "values")[1]
        try:
            run_exec("DELETE FROM CustodyStatus WHERE case_id=%s", (case_id,))
            run_exec("DELETE FROM LegalRepresentation WHERE case_id=%s", (case_id,))
            run_exec("DELETE FROM Immigrants WHERE case_id=%s", (case_id,))
            messagebox.showinfo("Deleted", "Record deleted across all tables.")

            self.imm_refresh()
            self.cust_refresh()
            self.legal_refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----------------------------------------------------------------
    # 2️⃣ Custody CRUD
    def build_custody(self):
        frm = ttk.Frame(self.tab_custody, padding=8)
        frm.pack(fill="both", expand=True)

        lf = ttk.LabelFrame(frm, text="Custody Record")
        lf.pack(fill="x", pady=6)

        # Dropdown menus
        custody_outcome = ["Pending", "Resolved", "Awaiting Hearing", "Asylum Granted", "Removed"]
        custody_type = ["Detained", "Never Detained", "Released"]

        self.c_case = tk.StringVar()
        self.c_type = tk.StringVar()
        self.c_fac = tk.StringVar()
        self.c_rel = tk.StringVar()
        self.c_outcome = tk.StringVar()

        ttk.Label(lf, text="Case ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(lf, textvariable=self.c_case, width=15).grid(row=0, column=1, padx=5)
        ttk.Label(lf, text="Custody Type").grid(row=0, column=2, sticky="w")
        ttk.Combobox(lf, textvariable=self.c_type, width=15, values=custody_type, state="readonly").grid(row=0, column=3, padx=5)
        ttk.Label(lf, text="Facility").grid(row=0, column=4, sticky="w")
        ttk.Entry(lf, textvariable=self.c_fac, width=20).grid(row=0, column=5, padx=5)
        ttk.Label(lf, text="Release Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w")
        ttk.Entry(lf, textvariable=self.c_rel, width=15).grid(row=1, column=1, padx=5)
        ttk.Label(lf, text="Outcome").grid(row=1, column=2, sticky="w")
        ttk.Combobox(lf, textvariable=self.c_outcome, width=20, values=custody_outcome, state="readonly").grid(row=1, column=3, padx=5)

        btns = ttk.Frame(lf); btns.grid(row=2, column=0, columnspan=8, pady=5)
        ttk.Button(btns, text="Create", command=self.cust_create).pack(side="left", padx=4)
        ttk.Button(btns, text="Refresh", command=self.cust_refresh).pack(side="left", padx=4)

        self.tree_cust = ttk.Treeview(frm, height=18)
        self.tree_cust.pack(fill="both", expand=True)
        self.cust_refresh()

    def cust_refresh(self):
        rows = run_select("SELECT * FROM CustodyStatus ORDER BY custody_id")
        fill_tree(self.tree_cust, rows)

        max_id = run_select("SELECT MAX(custody_id) AS max_id FROM CustodyStatus")[0]["max_id"] or 0
        run_exec("ALTER TABLE CustodyStatus AUTO_INCREMENT = %s", (max_id + 1,))

    def cust_create(self):
        fields = {
            "Case ID": self.c_case.get(),
            "Custody Type": self.c_type.get(),
            "Facility": self.c_fac.get(),
            "Release Date (YYYY-MM-DD)": self.c_rel.get(),
            "Outcome": self.c_outcome.get()
        }
        if not validate_fields(fields):
            return
        try:
            run_exec("""INSERT INTO CustodyStatus (case_id, custody_type, detention_facility, release_date, custody_outcome)
                        VALUES (%s,%s,%s,%s,%s)""",
                     (self.c_case.get(), self.c_type.get(), self.c_fac.get(),
                      sanitize_date(self.c_rel.get()), self.c_outcome.get()))
            messagebox.showinfo("Added", "Custody record added.")
            self.cust_refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----------------------------------------------------------------
    # 3️⃣ Legal Representation CRUD
    def build_legal(self):
        frm = ttk.Frame(self.tab_legal, padding=8)
        frm.pack(fill="both", expand=True)

        lf = ttk.LabelFrame(frm, text="Legal Representation")
        lf.pack(fill="x", pady=6)

        # Dropdown box
        legal_status = ["Has a lawyer", "No lawyer"]

        self.l_case = tk.StringVar()
        self.l_status = tk.StringVar()
        self.l_att = tk.StringVar()
        self.l_org = tk.StringVar()
        self.l_date = tk.StringVar()

        ttk.Label(lf, text="Case ID").grid(row=0, column=0)
        ttk.Entry(lf, textvariable=self.l_case, width=15).grid(row=0, column=1, padx=5)
        ttk.Label(lf, text="Status").grid(row=0, column=2)
        ttk.Combobox(lf, textvariable=self.l_status, width=15, values=legal_status, state="readonly").grid(row=0, column=3, padx=5)
        ttk.Label(lf, text="Attorney").grid(row=0, column=4)
        ttk.Entry(lf, textvariable=self.l_att, width=20).grid(row=0, column=5, padx=5)
        ttk.Label(lf, text="Organization").grid(row=1, column=0)
        ttk.Entry(lf, textvariable=self.l_org, width=20).grid(row=1, column=1, padx=5)
        ttk.Label(lf, text="Hearing Date (YYYY-MM-DD)").grid(row=1, column=2)
        ttk.Entry(lf, textvariable=self.l_date, width=15).grid(row=1, column=3, padx=5)

        btns = ttk.Frame(lf); btns.grid(row=2, column=0, columnspan=6, pady=5)
        ttk.Button(btns, text="Create", command=self.legal_create).pack(side="left", padx=4)
        ttk.Button(btns, text="Refresh", command=self.legal_refresh).pack(side="left", padx=4)

        self.tree_legal = ttk.Treeview(frm, height=18)
        self.tree_legal.pack(fill="both", expand=True)
        self.legal_refresh()

    def legal_refresh(self):
        rows = run_select("SELECT * FROM LegalRepresentation ORDER BY legal_id")
        fill_tree(self.tree_legal, rows)

        max_id = run_select("SELECT MAX(legal_id) AS max_id FROM LegalRepresentation")[0]["max_id"] or 0
        run_exec("ALTER TABLE LegalRepresentation AUTO_INCREMENT = %s", (max_id + 1,))

    def legal_create(self):
        fields = {
            "Case ID": self.l_case.get(),
            "Satus": self.l_status.get(),
            "Attorney": self.l_att.get(),
            "Organization": self.l_org.get(),
            "Hearing Date (YYYY-MM-DD)": self.l_date.get()
        }
        if not validate_fields(fields):
            return
        try:
            run_exec("""INSERT INTO LegalRepresentation (case_id, representation_status, attorney_name, organization, hearing_date)
                        VALUES (%s,%s,%s,%s,%s)""",
                     (self.l_case.get(), self.l_status.get(), self.l_att.get(), self.l_org.get(), self.l_date.get()))
            messagebox.showinfo("Added", "Legal record added.")
            self.legal_refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----------------------------------------------------------------
    # 4️⃣ Country CRUD
    def build_country(self):
        frm = ttk.Frame(self.tab_country, padding=8)
        frm.pack(fill="both", expand=True)

        lf = ttk.LabelFrame(frm, text="Country of Origin")
        lf.pack(fill="x", pady=6)

        self.co_id = tk.StringVar()
        self.co_name = tk.StringVar()
        self.co_region = tk.StringVar()
        self.co_migrants = tk.StringVar()
        self.co_language = tk.StringVar()

        ttk.Label(lf, text="Country Name").grid(row=0, column=0)
        ttk.Entry(lf, textvariable=self.co_name, width=20).grid(row=0, column=1)
        ttk.Label(lf, text="Region").grid(row=1, column=0)
        ttk.Entry(lf, textvariable=self.co_region, width=20).grid(row=1, column=1, padx=5)
        ttk.Label(lf, text="Migrants").grid(row=1, column=2)
        ttk.Entry(lf, textvariable=self.co_migrants, width=10).grid(row=1, column=3, padx=5)
        ttk.Label(lf, text="Language").grid(row=0, column=2)
        ttk.Entry(lf, textvariable=self.co_language, width=15).grid(row=0, column=3, padx=5)
        ttk.Label(lf, text="Country ID").grid(row=0, column=4)
        ttk.Entry(lf, textvariable=self.co_id, state="readonly").grid(row=0, column=5)


        btns = ttk.Frame(lf); btns.grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(btns, text="Create", command=self.co_create).pack(side="left", padx=4)
        ttk.Button(btns, text="Update", command=self.co_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete", command=self.co_delete).pack(side="left", padx=4)
        ttk.Button(btns, text="Refresh", command=self.co_refresh).pack(side="left", padx=4)

        self.tree_country = ttk.Treeview(frm, height=18)
        self.tree_country.pack(fill="both", expand=True)
        self.tree_country.bind("<<TreeviewSelect>>", self.co_on_select)

        self.co_refresh()

    def co_create(self):
        fields = {
            "Country Name": self.co_name.get(),
            "Region": self.co_region.get(),
            "Migrants": self.co_migrants.get(),
            "Language": self.co_language.get()
        }
        if not validate_fields(fields):
            return
        try:
            run_exec("""INSERT INTO CountryOfOrigin (country_name, region, population_migrants, major_language)
                    VALUES (%s, %s, %s, %s)""",
                     (self.co_name.get(), self.co_region.get(), int(self.co_migrants.get() or 0), self.co_language.get()))
            messagebox.showinfo("Success", "Country added.")
            self.co_refresh()
            self._reload_dropdowns()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def co_refresh(self):
        rows = run_select("""SELECT country_id, country_name, region, population_migrants, major_language
                         FROM CountryOfOrigin ORDER BY country_id""")
        fill_tree(self.tree_country, rows)

        max_id = run_select("SELECT MAX(country_id) AS max_id FROM CountryOfOrigin")[0]["max_id"] or 0
        run_exec("ALTER TABLE CountryOfOrigin AUTO_INCREMENT = %s", (max_id + 1,))

    def co_update(self):
        fields = {
            "Country Name": self.co_name.get(),
            "Region": self.co_region.get(),
            "Migrants": self.co_migrants.get(),
            "Language": self.co_language.get()
        }
        if not validate_fields(fields):
            return
        try:
            run_exec("""UPDATE CountryOfOrigin
                    SET country_name=%s, region=%s, population_migrants=%s, major_language=%s
                    WHERE country_id=%s""",
                     (self.co_name.get(), self.co_region.get(), int(self.co_migrants.get() or 0),
                      self.co_language.get(), self.co_id.get()))
            messagebox.showinfo("Updated", "Country updated.")
            self.co_refresh()
            self._reload_dropdowns()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def co_delete(self):
        sel = self.tree_country.selection()
        if not sel:
            messagebox.showwarning("Select row", "Pick a row first.")
            return

        country_id = self.tree_country.item(sel[0], "values")[0]

        # Check for linked immigrants
        linked = run_select("SELECT 1 FROM Immigrants WHERE country_id=%s LIMIT 1", (country_id,))
        if linked:
            messagebox.showerror("Blocked", "Cannot delete: immigrants are linked to this country.")
            return

        try:
            run_exec("DELETE FROM CountryOfOrigin WHERE country_id=%s", (country_id,))
            messagebox.showinfo("Deleted", "Country deleted.")
            self.co_refresh()
            self._reload_dropdowns()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def co_on_select(self, _=None):
        sel = self.tree_country.selection()
        if not sel: return
        vals = self.tree_country.item(sel[0], "values")
        self.co_id.set(vals[0])
        self.co_name.set(vals[1])
        self.co_region.set(vals[2])
        self.co_migrants.set(str(vals[3]))
        self.co_language.set(vals[4])

    # ----------------------------------------------------------------
    # 5️⃣ Analytics
    def build_analytics(self):
        frm = ttk.Frame(self.tab_analytics, padding=8)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Analytics Queries", font=("Segoe UI", 12, "bold")).pack(pady=5)
        ttk.Button(frm, text="(1) Percentage With Lawyers By Custody Type", command=self.q1).pack(pady=5)
        ttk.Button(frm, text="(2) Top 5 Countries By Detention Rate", command=self.q2).pack(pady=5)
        ttk.Button(frm, text="(3) Average Age By Custody Outcome", command=self.q3).pack(pady=5)
        ttk.Button(frm, text="(4) Top 5 Countries With Immigrants That Have Lawyers", command=self.q4).pack(pady=5)
        ttk.Button(frm, text="(5) Percentage Of Immigrants By Arrival Year", command=self.q5).pack(pady=5)

        # Description Box
        self.desc_box = tk.Text(frm, height=4, wrap="word", font=("Segoe UI", 10))
        self.desc_box.pack(fill="x", pady=(10, 0))
        self.desc_box.insert("1.0", "Select a query above to view its results. Description will appear here.")
        self.desc_box.config(state="disabled")

        self.tree_ana = ttk.Treeview(frm, height=18)
        self.tree_ana.pack(fill="both", expand=True)

    def q1(self):
        rows = run_select("""
            SELECT cs.custody_type AS 'Custody Type',
                   ROUND(SUM(l.representation_status='Has a lawyer')/COUNT(*)*100,1) AS 'Percentage(%) With Lawyer'
            FROM Immigrants i
            JOIN CustodyStatus cs ON i.custody_id=cs.custody_id
            JOIN LegalRepresentation l ON i.legal_id=l.legal_id
            GROUP BY cs.custody_type
            ORDER BY 'Percentage With Lawyer' DESC
        """)
        fill_tree(self.tree_ana, rows)
        self.update_description("Displaying percentage of immigrants that do have lawyers. "
                                "Categorized into their Custody Type: Detained, Released, and Never Detained.")

    def q2(self):
        rows = run_select("""
            SELECT 
                c.country_name AS 'Country Name',
                COUNT(*) AS 'Total Immigrants',
                SUM(cs.custody_type = 'Detained') AS 'Total Detained',
                ROUND(SUM(cs.custody_type = 'Detained') / COUNT(*) * 100, 1) AS 'Detention Rate'
            FROM Immigrants i
            JOIN CountryOfOrigin c ON i.country_id = c.country_id
            JOIN CustodyStatus cs ON i.custody_id = cs.custody_id
            GROUP BY c.country_name
            ORDER BY SUM(cs.custody_type = 'Detained') DESC
            LIMIT 5;
        """)
        fill_tree(self.tree_ana, rows)
        self.update_description("Displaying the top 5 countries that have the highest detention rate.")

    def q3(self):
        rows = run_select("""
            SELECT cs.custody_outcome AS 'Custody Outcome', ROUND(AVG(i.age),1) AS 'Average Age'
            FROM Immigrants i
            JOIN CustodyStatus cs ON i.custody_id=cs.custody_id
            GROUP BY cs.custody_outcome
            ORDER BY 'Average Age' DESC
        """)
        fill_tree(self.tree_ana, rows)
        self.update_description("Displays the immigrants' custody outcome and the average age per category. "
                                "The outcome is based on the outcome of the custody.")

    def q4(self):
        rows = run_select("""
            SELECT 
                c.country_name AS 'Country Name',
                COUNT(*) AS 'Total Immigrants',
                SUM(l.representation_status = 'Has a lawyer') AS 'With Lawyer',
                ROUND(SUM(l.representation_status = 'Has a lawyer') / COUNT(*) * 100, 1) AS 'Lawyer Rate'
            FROM Immigrants i
            JOIN CountryOfOrigin c ON i.country_id = c.country_id
            JOIN LegalRepresentation l ON i.legal_id = l.legal_id
            GROUP BY c.country_name
            ORDER BY `With Lawyer` DESC
            LIMIT 5;
        """)
        fill_tree(self.tree_ana, rows)
        self.update_description("Displaying the top 5 countries with the highest percentage of immigrants who have lawyers.")

    def q5(self):
        rows = run_select("""
            SELECT 
                arrival_year AS 'Arrival Year',
                COUNT(*) AS 'Total Arrivals',
                ROUND(COUNT(*) / (SELECT COUNT(*) FROM Immigrants) * 100, 1) AS 'Arrival %'
            FROM Immigrants
            GROUP BY arrival_year
            ORDER BY arrival_year;
        """)
        fill_tree(self.tree_ana, rows)
        self.update_description("Displaying the percentage of immigrants' arrival by the year.")

    def update_description(self, text):
        self.desc_box.config(state="normal")
        self.desc_box.delete("1.0", "end")
        self.desc_box.insert("1.0", text)
        self.desc_box.config(state="disabled")

# --------------------------------------------------------------------

if __name__ == "__main__":
    try:
        App().mainloop()
    except mysql.Error as e:
        messagebox.showerror("DB connection failed", str(e))