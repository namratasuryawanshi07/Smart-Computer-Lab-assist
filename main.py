import os
import io
import base64
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from models import LabAssistant, Asset, Complaint
from db import get_connection
import pandas as pd

try:
    from logo_data import LOGO_B64
except ImportError:
    LOGO_B64 = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- COLORS ----------
SIDEBAR_BG = "#1e293b"
SIDEBAR_ACCENT = "#38bdf8"
SIDEBAR_ITEM_ACTIVE = "#334155"
SIDEBAR_HOVER = "#2b3a4f"
CONTENT_BG = "#f4f6f9"
CARD_BG = "#ffffff"
BTN_BLUE = "#38bdf8"
BTN_GREEN = "#16a34a"
BTN_RED = "#ef4444"
TEXT_DARK = "#1e293b"
COLLEGE_BLUE = "#1a6fc4"

COLLEGE_NAME = "Annasaheb Dange College of Engineering and Technology, Ashta"
FONT_LABEL = ("Segoe UI", 13)
FONT_FIELD = ("Segoe UI", 13)
NAV_ICONS = {
    "report": "📝",
    "dashboard": "📊",
    "assets": "🖥️",
    "complaints": "📋",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Lab Asset Manager - ADCET")
        self.geometry("1100x700")
        self.configure(bg=CONTENT_BG)
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 12))
        self.setup_styles()
        try:
            self.state("zoomed")  # open maximized (Windows)
        except tk.TclError:
            pass

        self.session = {"assistant_id": None, "full_name": None}
        self.nav_buttons = {}
        self.current_screen = None

        # ---------- SIDEBAR ----------
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="Lab Asset", font=("Segoe UI", 18, "bold"),
                 bg=SIDEBAR_BG, fg=SIDEBAR_ACCENT).pack(pady=(30, 20))

        self.public_nav_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        self.public_nav_frame.pack(fill="x")
        self.add_nav_item(self.public_nav_frame, "Report Issue", "report")

        self.assistant_label = tk.Label(self.sidebar, text="LAB ASSISTANT", font=("Segoe UI", 8),
                                         bg=SIDEBAR_BG, fg="#64748b")
        self.assistant_nav_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)

        self.login_area = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        self.login_area.pack(side="bottom", fill="x", pady=20, padx=15)
        self.render_login_area()

        # ---------- RIGHT SIDE (header + content + footer) ----------
        self.main_area = tk.Frame(self, bg=CONTENT_BG)
        self.main_area.pack(side="left", fill="both", expand=True)

        # Footer (packed first with side="bottom" so it stays pinned at the bottom)
        footer = tk.Frame(self.main_area, bg=SIDEBAR_BG, height=32)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)
        tk.Label(footer, text=f"© 2026 {COLLEGE_NAME} — Smart Lab Asset Management System",
                 bg=SIDEBAR_BG, fg="#94a3b8", font=("Segoe UI", 9)).pack(pady=6)

        # College header: logo + name, centered at the top of every page
        self.header = tk.Frame(self.main_area, bg=CARD_BG)
        self.header.pack(side="top", fill="x")
        header_inner = tk.Frame(self.header, bg=CARD_BG)
        header_inner.pack(pady=10)  # no fill => centered horizontally

        self.logo_img = self.load_logo("college_logo.png", 80)  # keep reference on self!
        if self.logo_img:
            tk.Label(header_inner, image=self.logo_img, bg=CARD_BG).pack(side="left", padx=(0, 15))
            self.iconphoto(True, self.logo_img)  # window/taskbar icon
        tk.Label(header_inner, text=COLLEGE_NAME, font=("Segoe UI", 17, "bold"),
                 bg=CARD_BG, fg=COLLEGE_BLUE, wraplength=850, justify="center").pack(side="left")

        tk.Frame(self.main_area, bg=BTN_BLUE, height=3).pack(side="top", fill="x")

        # Screens are drawn inside this frame
        self.content = tk.Frame(self.main_area, bg=CONTENT_BG)
        self.content.pack(side="top", fill="both", expand=True)

        self.show_screen("report")

    # ---------- STYLES ----------
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")  # needed so custom colors actually apply on Windows

        style.configure("Treeview",
                         background="white",
                         foreground=TEXT_DARK,
                         fieldbackground="white",
                         rowheight=32,
                         font=("Segoe UI", 10))

        style.configure("Treeview.Heading",
                         background=SIDEBAR_BG,
                         foreground="white",
                         font=("Segoe UI", 10, "bold"),
                         relief="flat")
        style.map("Treeview.Heading",
                  background=[("active", SIDEBAR_ITEM_ACTIVE)])

        style.map("Treeview",
                  background=[("selected", BTN_BLUE)],
                  foreground=[("selected", "white")])

    # ---------- LOGO HELPER ----------
    def load_logo(self, filename, height):
        img = None
        for folder in ("assets", "assest"):
            folder_path = os.path.join(BASE_DIR, folder)
            if not os.path.isdir(folder_path):
                continue
            lower = {f.lower(): f for f in os.listdir(folder_path)}
            for cand in (filename, filename + ".png"):
                if cand.lower() in lower:
                    try:
                        img = Image.open(os.path.join(folder_path, lower[cand.lower()])).convert("RGBA")
                    except Exception as e:
                        print(f"Could not open logo file: {e}")
                    break
            if img:
                break
        if img is None and LOGO_B64:
            try:
                img = Image.open(io.BytesIO(base64.b64decode(LOGO_B64))).convert("RGBA")
            except Exception as e:
                print(f"Could not decode embedded logo: {e}")
        if img is None:
            print("No logo found: put logo_data.py next to main.py or college_logo.png in assets/")
            return None
        ratio = height / img.height
        img = img.resize((int(img.width * ratio), height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    # ---------- NAV HELPERS ----------
    def add_nav_item(self, parent, label, screen_name):
        icon = NAV_ICONS.get(screen_name, "")
        text = f"{icon}   {label}" if icon else label
        btn = tk.Label(parent, text=text, font=("Segoe UI", 12), bg=SIDEBAR_BG, fg="white",
                        anchor="w", padx=25, pady=12, cursor="hand2")
        btn.pack(fill="x")
        btn.bind("<Button-1>", lambda e: self.show_screen(screen_name))
        btn.bind("<Enter>", lambda e: self.on_nav_hover(screen_name, True))
        btn.bind("<Leave>", lambda e: self.on_nav_hover(screen_name, False))
        self.nav_buttons[screen_name] = btn

    def on_nav_hover(self, screen_name, entering):
        btn = self.nav_buttons.get(screen_name)
        if not btn:
            return
        if screen_name == self.current_screen:
            return  # don't override the active highlight
        btn.configure(bg=SIDEBAR_HOVER if entering else SIDEBAR_BG)

    def highlight_nav(self, screen_name):
        self.current_screen = screen_name
        for name, btn in self.nav_buttons.items():
            if name == screen_name:
                btn.configure(bg=SIDEBAR_ITEM_ACTIVE, fg=SIDEBAR_ACCENT)
            else:
                btn.configure(bg=SIDEBAR_BG, fg="white")

    def render_login_area(self):
        for w in self.login_area.winfo_children():
            w.destroy()
        if self.session["assistant_id"]:
            tk.Label(self.login_area, text=self.session["full_name"], font=("Segoe UI", 11, "bold"),
                      bg=SIDEBAR_BG, fg=SIDEBAR_ACCENT).pack(pady=(0, 8))
            tk.Button(self.login_area, text="Logout", bg="#475569", fg="white", relief="flat",
                       command=self.logout).pack(fill="x", ipady=6)
        else:
            tk.Button(self.login_area, text="Lab Assistant Login", bg=BTN_BLUE, fg="white",
                       font=("Segoe UI", 11, "bold"), relief="flat",
                       command=self.open_login_modal).pack(fill="x", ipady=8)

    def logout(self):
        self.session = {"assistant_id": None, "full_name": None}
        self.assistant_nav_frame.pack_forget()
        self.assistant_label.pack_forget()
        self.render_login_area()
        self.show_screen("report")

    def open_login_modal(self):
        LoginModal(self)

    def on_login_success(self, assistant_id, full_name):
        self.session["assistant_id"] = assistant_id
        self.session["full_name"] = full_name
        self.render_login_area()
        self.assistant_label.pack(anchor="w", padx=25, pady=(15, 5), before=self.login_area)
        self.assistant_nav_frame.pack(fill="x", before=self.login_area)
        for w in self.assistant_nav_frame.winfo_children():
            w.destroy()
        self.nav_buttons.pop("dashboard", None)
        self.nav_buttons.pop("assets", None)
        self.nav_buttons.pop("complaints", None)
        self.add_nav_item(self.assistant_nav_frame, "Dashboard", "dashboard")
        self.add_nav_item(self.assistant_nav_frame, "Assets", "assets")
        self.add_nav_item(self.assistant_nav_frame, "Complaints", "complaints")
        self.show_screen("dashboard")

    # ---------- SCREEN SWITCHING ----------
    def show_screen(self, name):
        for w in self.content.winfo_children():
            w.destroy()

        if name in ("dashboard", "assets", "complaints") and not self.session["assistant_id"]:
            messagebox.showerror("Login required", "Please log in as a Lab Assistant first.")
            return

        self.highlight_nav(name)

        if name == "report":
            ReportIssueScreen(self.content, self)
        elif name == "dashboard":
            DashboardScreen(self.content, self)
        elif name == "assets":
            AssetsScreen(self.content, self)
        elif name == "complaints":
            ComplaintsScreen(self.content, self)


# ---------- LOGIN MODAL ----------
class LoginModal(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Lab Assistant Login")
        self.geometry("420x480")
        self.configure(bg=CARD_BG)
        self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text="Lab Assistant Login", font=("Segoe UI", 18, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(pady=(30, 5))

        tk.Label(self, text="Enter your credentials to continue", font=("Segoe UI", 10),
                 bg=CARD_BG, fg="#64748b").pack(pady=(0, 15))

        self.error_label = tk.Label(self, text="", fg="#dc2626", bg=CARD_BG,
                                     font=("Segoe UI", 10, "bold"), wraplength=360)
        self.error_label.pack()

        form = tk.Frame(self, bg=CARD_BG)
        form.pack(pady=10, padx=35, fill="x")

        tk.Label(form, text="Username", bg=CARD_BG, font=("Segoe UI", 11),
                 fg=TEXT_DARK, anchor="w").pack(fill="x")
        self.username_entry = tk.Entry(form, font=("Segoe UI", 13), relief="solid", bd=1)
        self.username_entry.pack(fill="x", pady=(2, 16), ipady=8)

        tk.Label(form, text="Password", bg=CARD_BG, font=("Segoe UI", 11),
                 fg=TEXT_DARK, anchor="w").pack(fill="x")
        self.password_entry = tk.Entry(form, font=("Segoe UI", 13), show="*", relief="solid", bd=1)
        self.password_entry.pack(fill="x", pady=(2, 10), ipady=8)
        self.password_entry.bind("<Return>", lambda e: self.attempt_login())

        btns = tk.Frame(self, bg=CARD_BG)
        btns.pack(pady=25)
        tk.Button(btns, text="Cancel", font=("Segoe UI", 12, "bold"),
                  bg="#e5e7eb", fg=TEXT_DARK, relief="flat",
                  command=self.destroy).pack(side="left", padx=8, ipadx=18, ipady=10)
        tk.Button(btns, text="Login", bg=BTN_BLUE, fg="white", font=("Segoe UI", 12, "bold"),
                  relief="flat", command=self.attempt_login).pack(side="left", padx=8, ipadx=30, ipady=10)

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.config(text="Username and password are required")
            return

        row, error = LabAssistant.authenticate(username, password)
        if error:
            self.error_label.config(text=error)
            return
        if row:
            self.app.on_login_success(row["assistant_id"], row["full_name"])
            self.destroy()
        else:
            self.error_label.config(text="Invalid username or password")


# ---------- REPORT ISSUE SCREEN ----------
class ReportIssueScreen(tk.Frame):
    ISSUE_TYPES = ["Monitor Issue", "Keyboard/Mouse Issue", "Not Powering On",
                   "Slow Performance", "Internet/Network Issue", "Software Error", "Other"]

    def __init__(self, parent, app):
        super().__init__(parent, bg=CONTENT_BG)
        self.app = app
        self.pack(fill="both", expand=True)

        # ---- Scrollable container ----
        canvas = tk.Canvas(self, bg=CONTENT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=CONTENT_BG)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        def center_frame(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", center_frame)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ---- Everything below goes INSIDE scroll_frame, not self ----
        wrap = tk.Frame(scroll_frame, bg=CONTENT_BG)
        wrap.pack(pady=(30, 30))

        tk.Label(wrap, text="Report Issue", font=("Segoe UI", 26, "bold"),
                 bg=CONTENT_BG, fg=TEXT_DARK).pack(pady=(0, 20))

        card = tk.Frame(wrap, bg=CARD_BG, padx=70, pady=40)
        card.pack()

        LBL = FONT_LABEL
        FLD = FONT_FIELD

        tk.Label(card, text="Report a Computer Issue", font=("Segoe UI", 18, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, sticky="w", pady=(0, 20))

        self.msg_label = tk.Label(card, text="", bg=CARD_BG, font=("Segoe UI", 10), wraplength=640, justify="left")
        self.msg_label.grid(row=1, column=0, sticky="w", pady=(0, 10))

        tk.Label(card, text="Select Lab", bg=CARD_BG, fg=TEXT_DARK, font=LBL).grid(row=2, column=0, sticky="w")
        self.lab_var = tk.StringVar()
        self.lab_dropdown = ttk.Combobox(card, textvariable=self.lab_var, state="readonly", width=60, font=FLD)
        self.lab_dropdown.grid(row=3, column=0, sticky="w", pady=(4, 16), ipady=4)
        self.lab_dropdown.bind("<<ComboboxSelected>>", self.on_lab_selected)

        tk.Label(card, text="Select PC", bg=CARD_BG, fg=TEXT_DARK, font=LBL).grid(row=4, column=0, sticky="w")
        self.pc_var = tk.StringVar()
        self.pc_dropdown = ttk.Combobox(card, textvariable=self.pc_var, state="readonly", width=60, font=FLD)
        self.pc_dropdown.grid(row=5, column=0, sticky="w", pady=(4, 16), ipady=4)
        self.pc_map = {}

        tk.Label(card, text="Issue Type", bg=CARD_BG, fg=TEXT_DARK, font=LBL).grid(row=6, column=0, sticky="w")
        self.issue_var = tk.StringVar(value=self.ISSUE_TYPES[0])
        ttk.Combobox(card, textvariable=self.issue_var, state="readonly", font=FLD,
                     values=self.ISSUE_TYPES, width=60).grid(row=7, column=0, sticky="w", pady=(4, 16), ipady=4)

        tk.Label(card, text="Describe the Issue", bg=CARD_BG, fg=TEXT_DARK, font=LBL).grid(row=8, column=0, sticky="w")
        self.description_text = tk.Text(card, width=66, height=6, font=("Segoe UI", 11),
                                         relief="solid", bd=1)
        self.description_text.grid(row=9, column=0, sticky="w", pady=(4, 22))

        tk.Button(card, text="Submit Complaint", bg=BTN_BLUE, fg="white", font=("Segoe UI", 13, "bold"),
                  relief="flat", command=self.submit_complaint).grid(row=10, column=0, sticky="w", ipadx=16, ipady=8)

        self.load_labs()

    def load_labs(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT location FROM assets ORDER BY location")
            labs = [r[0] for r in cursor.fetchall()]
            conn.close()
            self.lab_dropdown["values"] = labs
        except Exception as e:
            messagebox.showerror("Error", f"Could not load labs: {e}")

    def on_lab_selected(self, event):
        lab = self.lab_var.get()
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT asset_id, asset_name, pc_number FROM assets WHERE location = %s ORDER BY pc_number", (lab,))
            rows = cursor.fetchall()
            conn.close()
            self.pc_map = {}
            values = []
            for r in rows:
                label = f"{r['pc_number']} ({r['asset_name']})"
                values.append(label)
                self.pc_map[label] = r["asset_id"]
            self.pc_dropdown["values"] = values
            self.pc_var.set("")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load PCs: {e}")

    def submit_complaint(self):
        pc_display = self.pc_var.get()
        if pc_display not in self.pc_map:
            self.msg_label.config(text="Please select a PC.", fg="#991b1b")
            return

        asset_id = self.pc_map[pc_display]
        issue_category = self.issue_var.get()
        issue_description = self.description_text.get("1.0", tk.END).strip()

        complaint = Complaint(asset_id=asset_id, issue_category=issue_category, issue_description=issue_description)

        duplicate, error = complaint.find_duplicate()
        if error:
            self.msg_label.config(text=error, fg="#991b1b")
            return
        if duplicate:
            self.msg_label.config(text="This exact issue is already reported and pending resolution.", fg="#854d0e")
            return

        other_open, error = complaint.has_other_open()
        if error:
            self.msg_label.config(text=error, fg="#991b1b")
            return

        success, error = complaint.save()
        if not success:
            self.msg_label.config(text=error, fg="#991b1b")
            return

        msg = "Complaint submitted successfully."
        if other_open:
            msg += " Note: this PC already has another open issue being worked on."
            self.msg_label.config(text=msg, fg="#854d0e")
        else:
            self.msg_label.config(text=msg, fg="#166534")

        self.description_text.delete("1.0", tk.END)


# ---------- DASHBOARD SCREEN ----------
class DashboardScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=CONTENT_BG)
        self.app = app
        self.pack(fill="both", expand=True)

        tk.Label(self, text="Dashboard", font=("Segoe UI", 22, "bold"),
                 bg=CONTENT_BG, fg=TEXT_DARK).pack(pady=(25, 15))

        stats_frame = tk.Frame(self, bg=CONTENT_BG)
        stats_frame.pack(fill="x", padx=40)
        for i in range(3):
            stats_frame.columnconfigure(i, weight=1, uniform="stat")

        self.card_total = self.make_stat_card(stats_frame, 0, "0", "Total Assets")
        self.card_active = self.make_stat_card(stats_frame, 1, "0", "Active Assets")
        self.card_complaints = self.make_stat_card(stats_frame, 2, "0", "Open Complaints")

        tk.Label(self, text="Search Computer by Lab / PC Number", font=("Segoe UI", 15, "bold"),
                 bg=CONTENT_BG, fg=TEXT_DARK).pack(pady=(25, 10))

        search_frame = tk.Frame(self, bg=CONTENT_BG)
        search_frame.pack(pady=(0, 15))
        self.search_entry = tk.Entry(search_frame, width=40, font=("Segoe UI", 13), relief="solid", bd=1)
        self.search_entry.pack(side="left", ipady=8, ipadx=8)
        self.search_entry.bind("<Return>", lambda e: self.search_assets())
        tk.Button(search_frame, text="🔍 Search", bg=BTN_BLUE, fg="white", relief="flat",
                  font=("Segoe UI", 12, "bold"),
                  command=self.search_assets).pack(side="left", padx=10, ipadx=18, ipady=8)

        columns = ("pc", "name", "location", "processor", "ram", "storage", "os", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col, label in zip(columns, ["PC No.", "Name", "Lab", "Processor", "RAM", "Storage", "OS", "Status"]):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=40, pady=(10, 25))

        self.load_stats()

    def make_stat_card(self, parent, column, value, label):
        card = tk.Frame(parent, bg=CARD_BG, padx=20, pady=15, highlightbackground=BTN_BLUE, highlightthickness=2)
        card.grid(row=0, column=column, sticky="ew", padx=10)
        val_label = tk.Label(card, text=value, font=("Segoe UI", 26, "bold"), bg=CARD_BG, fg=TEXT_DARK)
        val_label.pack()
        tk.Label(card, text=label, bg=CARD_BG, fg="#666").pack()
        return val_label

    def load_stats(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM assets")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Active'")
            active = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Open'")
            open_complaints = cursor.fetchone()[0]
            conn.close()
            self.card_total.config(text=str(total))
            self.card_active.config(text=str(active))
            self.card_complaints.config(text=str(open_complaints))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load stats: {e}")

    def search_assets(self):
        query = self.search_entry.get()
        rows, error = Asset.search(query)
        self.tree.delete(*self.tree.get_children())
        if error:
            messagebox.showerror("Error", error)
            return
        self.tree.tag_configure("odd", background="#f4f6f9")
        self.tree.tag_configure("even", background="white")
        for i, a in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=(
                a.get("pc_number", ""), a.get("asset_name", ""), a.get("location", ""),
                a.get("processor", ""), a.get("ram", ""), a.get("storage", ""),
                a.get("operating_system", ""), a.get("status", "")
            ), tags=(tag,))


# ---------- ASSETS SCREEN ----------
class AssetsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=CONTENT_BG)
        self.app = app
        self.pack(fill="both", expand=True)

        tk.Label(self, text="All Assets", font=("Segoe UI", 22, "bold"),
                 bg=CONTENT_BG, fg=TEXT_DARK).pack(pady=(25, 15))

        btn_frame = tk.Frame(self, bg=CONTENT_BG)
        btn_frame.pack(pady=(0, 10))
        tk.Button(btn_frame, text="+ Add Asset", bg=BTN_BLUE, fg="white", relief="flat",
                  font=("Segoe UI", 12, "bold"),
                  command=self.open_add_asset).pack(side="left", ipadx=16, ipady=8, padx=(0, 12))
        tk.Button(btn_frame, text="⬇ Export to CSV", bg=BTN_GREEN, fg="white", relief="flat",
                  font=("Segoe UI", 12, "bold"),
                  command=self.export_csv).pack(side="left", ipadx=16, ipady=8)

        columns = ("id", "name", "type", "location", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col, label in zip(columns, ["ID", "Name", "Type", "Location", "Status"]):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=130, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=40, pady=15)

        tk.Button(self, text="Delete Selected", bg=BTN_RED, fg="white", relief="flat",
                  font=("Segoe UI", 12, "bold"),
                  command=self.delete_selected).pack(pady=(10, 20), ipadx=16, ipady=8)

        self.load_assets()

    def load_assets(self):
        rows, error = Asset.get_all()
        self.tree.delete(*self.tree.get_children())
        if error:
            messagebox.showerror("Error", error)
            return
        self.tree.tag_configure("odd", background="#f4f6f9")
        self.tree.tag_configure("even", background="white")
        for i, a in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=a["asset_id"], values=(
                a["asset_id"], a["asset_name"], a.get("asset_type", ""),
                a.get("location", ""), a.get("status", "")
            ), tags=(tag,))

    def open_add_asset(self):
        AddAssetModal(self)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an asset to delete.")
            return
        asset_id = int(selected[0])
        if not messagebox.askyesno("Confirm", "Delete this asset?"):
            return
        success, error = Asset.delete(asset_id)
        if not success:
            messagebox.showerror("Error", error)
            return
        self.load_assets()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             initialfile="lab_assets.csv")
        if not path:
            return
        try:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM assets ORDER BY location, pc_number", conn)
            conn.close()
            df.to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Assets exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export assets: {e}")


class AddAssetModal(tk.Toplevel):
    def __init__(self, assets_screen):
        super().__init__(assets_screen)
        self.assets_screen = assets_screen
        self.title("Add Asset")
        self.geometry("360x340")
        self.configure(bg=CARD_BG)
        self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text="Add Asset", font=("Segoe UI", 16, "bold"), bg=CARD_BG).pack(pady=18)

        form = tk.Frame(self, bg=CARD_BG)
        form.pack()

        tk.Label(form, text="Asset Name:", bg=CARD_BG, font=FONT_LABEL).grid(row=0, column=0, sticky="e", pady=8, padx=8)
        self.name_entry = tk.Entry(form, width=20, font=FONT_FIELD)
        self.name_entry.grid(row=0, column=1, pady=8)

        tk.Label(form, text="Asset Type:", bg=CARD_BG, font=FONT_LABEL).grid(row=1, column=0, sticky="e", pady=8, padx=8)
        self.type_entry = tk.Entry(form, width=20, font=FONT_FIELD)
        self.type_entry.grid(row=1, column=1, pady=8)

        tk.Label(form, text="Location:", bg=CARD_BG, font=FONT_LABEL).grid(row=2, column=0, sticky="e", pady=8, padx=8)
        self.location_entry = tk.Entry(form, width=20, font=FONT_FIELD)
        self.location_entry.grid(row=2, column=1, pady=8)

        tk.Label(form, text="Status:", bg=CARD_BG, font=FONT_LABEL).grid(row=3, column=0, sticky="e", pady=8, padx=8)
        self.status_var = tk.StringVar(value="Active")
        ttk.Combobox(form, textvariable=self.status_var, state="readonly", font=FONT_FIELD,
                     values=["Active", "Under Repair", "Inactive"], width=17).grid(row=3, column=1, pady=8)

        tk.Button(self, text="Save", bg=BTN_BLUE, fg="white", font=("Segoe UI", 12, "bold"),
                  relief="flat", command=self.save_asset).pack(pady=22, ipadx=16, ipady=8)

    def save_asset(self):
        name = self.name_entry.get().strip()
        asset_type = self.type_entry.get().strip()
        location = self.location_entry.get().strip()
        status = self.status_var.get()

        if not all([name, asset_type, location, status]):
            messagebox.showerror("Error", "All asset fields are required")
            return

        asset = Asset(asset_name=name, asset_type=asset_type, location=location, status=status)
        success, error = asset.save()
        if not success:
            messagebox.showerror("Error", error)
            return

        self.assets_screen.load_assets()
        self.destroy()


# ---------- COMPLAINTS SCREEN ----------
class ComplaintsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=CONTENT_BG)
        self.app = app
        self.pack(fill="both", expand=True)

        tk.Label(self, text="Student Complaints", font=("Segoe UI", 22, "bold"),
                 bg=CONTENT_BG, fg=TEXT_DARK).pack(pady=(20, 10))

        table_frame = tk.Frame(self, bg=CONTENT_BG)
        table_frame.pack(fill="both", expand=True, padx=40, pady=(0, 10))

        columns = ("id", "pc", "location", "category", "description", "reported", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=9)
        for col, label in zip(columns, ["ID", "PC", "Lab", "Issue Type", "Description", "Reported", "Status"]):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=130, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tk.Button(self, text="Mark Selected as Resolved", bg=BTN_BLUE, fg="white", relief="flat",
                  font=("Segoe UI", 12, "bold"),
                  command=self.resolve_selected).pack(pady=(0, 20), ipadx=16, ipady=8)

        self.load_complaints()

    def load_complaints(self):
        rows, error = Complaint.get_all()
        self.tree.delete(*self.tree.get_children())
        if error:
            messagebox.showerror("Error", error)
            return
        self.tree.tag_configure("odd", background="#f4f6f9")
        self.tree.tag_configure("even", background="white")
        for i, c in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=c["complaint_id"], values=(
                c["complaint_id"], c["asset_name"], c["location"], c["issue_category"],
                c.get("issue_description", ""), c["reported_at"], c["status"]
            ), tags=(tag,))

    def resolve_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a complaint to resolve.")
            return
        complaint_id = int(selected[0])
        success, error = Complaint.resolve(complaint_id)
        if not success:
            messagebox.showerror("Error", error)
            return
        self.load_complaints()


if __name__ == "__main__":
    app = App()
    app.mainloop()