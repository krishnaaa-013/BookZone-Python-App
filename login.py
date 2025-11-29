from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import mysql.connector
import os

# import your main app window (make sure open_main_app.py defines open_main_app)
from open_main_app import open_main_app

# -------------------- DB helper --------------------
def get_connection():
    """
    Return a fresh MySQL connection. Keep credentials here.
    """
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Krishna@13",  # update if needed
        database="book_system"
    )

# -------------------- LOGIN FUNCTION --------------------
def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if username == "" or password == "":
        messagebox.showerror("Error", "All fields are required")
        return

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"Could not connect to DB: {e}")
        return
    finally:
        try:
            conn.close()
        except:
            pass

    if user:
        messagebox.showinfo("Success", f"Welcome, {username}!")
        
        # --- FIX: HIDE THE MASTER ROOT WINDOW ---
        # Instead of destroying 'root', we hide it. This keeps the application 
        # process running, allowing Toplevel windows (like the main app) to persist.
        root.withdraw() 
        
        # open main app window (from open_main_app)
        main_app_window = open_main_app(username)
        
        # --- CLEAN SHUTDOWN PROTOCOL (Optional but Recommended) ---
        # When the user closes the main Toplevel window, destroy the hidden master root
        # to ensure the application truly exits instead of running silently in the background.
        main_app_window.protocol("WM_DELETE_WINDOW", root.destroy)
        
        username_entry.delete(0, END)
        password_entry.delete(0, END)
    else:
        messagebox.showerror("Error", "Invalid username or password")


# -------------------- REGISTER WINDOW --------------------
def register():
    def center(win):
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        ws = win.winfo_screenwidth()
        hs = win.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        win.geometry(f'+{x}+{y}')

    reg = Toplevel(root)
    reg.title("Register")
    reg.geometry("480x640")
    reg.configure(bg="#f8eaff")

    # Header
    Label(reg, text="Create Your Account", font=("Arial", 22, "bold"),
          bg="#f8eaff", fg="#7a00ff").pack(pady=18)

    # Container frame for nicer spacing
    frm = Frame(reg, bg="#f8eaff")
    frm.pack(pady=6, padx=20, fill="x")

    # Full name
    Label(frm, text="Full Name:", bg="#f8eaff").pack(anchor="w", pady=(6,0))
    full_name_entry = Entry(frm, font=("Arial", 12))
    full_name_entry.pack(fill="x", pady=4)

    # Email
    Label(frm, text="Email:", bg="#f8eaff").pack(anchor="w", pady=(6,0))
    email_entry = Entry(frm, font=("Arial", 12))
    email_entry.pack(fill="x", pady=4)

    # Phone
    Label(frm, text="Phone:", bg="#f8eaff").pack(anchor="w", pady=(6,0))
    phone_entry = Entry(frm, font=("Arial", 12))
    phone_entry.pack(fill="x", pady=4)

    # Gender (radio buttons)
    Label(frm, text="Gender:", bg="#f8eaff").pack(anchor="w", pady=(8,0))
    gender_var = StringVar(value="Male")
    gfrm = Frame(frm, bg="#f8eaff")
    gfrm.pack(fill="x", pady=4)
    Radiobutton(gfrm, text="Male", variable=gender_var, value="Male", bg="#f8eaff").pack(side="left", padx=6)
    Radiobutton(gfrm, text="Female", variable=gender_var, value="Female", bg="#f8eaff").pack(side="left", padx=6)
    Radiobutton(gfrm, text="Others", variable=gender_var, value="Others", bg="#f8eaff").pack(side="left", padx=6)

    # Country dropdown
    Label(frm, text="Country:", bg="#f8eaff").pack(anchor="w", pady=(8,0))
    country_var = StringVar(value="India")
    countries = [
        "India","United States","United Kingdom","Canada","Australia","Germany",
        "France","Netherlands","Japan","South Korea","China","Brazil","Other"
    ]
    country_box = ttk.Combobox(frm, values=countries, textvariable=country_var, state="readonly")
    country_box.pack(fill="x", pady=4)

    # Username
    Label(frm, text="Username:", bg="#f8eaff").pack(anchor="w", pady=(8,0))
    reg_username_entry = Entry(frm, font=("Arial", 12))
    reg_username_entry.pack(fill="x", pady=4)

    # Password
    Label(frm, text="Password:", bg="#f8eaff").pack(anchor="w", pady=(8,0))
    reg_password_entry = Entry(frm, show="*", font=("Arial", 12))
    reg_password_entry.pack(fill="x", pady=4)

    # Confirm Password
    Label(frm, text="Confirm Password:", bg="#f8eaff").pack(anchor="w", pady=(8,0))
    reg_confirm_entry = Entry(frm, show="*", font=("Arial", 12))
    reg_confirm_entry.pack(fill="x", pady=4)

    # Helper: validate email simple
    def is_valid_email(e):
        return ("@" in e and "." in e and len(e) >= 6)

    # Register action
    def register_user():
        fn = full_name_entry.get().strip()
        em = email_entry.get().strip()
        ph = phone_entry.get().strip()
        gd = gender_var.get().strip()
        cn = country_var.get().strip()
        un = reg_username_entry.get().strip()
        pw = reg_password_entry.get().strip()
        conf = reg_confirm_entry.get().strip()

        # Basic validation
        if not (fn and em and ph and gd and cn and un and pw and conf):
            messagebox.showerror("Error", "All fields are required")
            return

        if not is_valid_email(em):
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        if len(ph) < 7 or not ph.isdigit():
            messagebox.showerror("Error", "Please enter a valid phone number (digits only)")
            return

        if pw != conf:
            messagebox.showerror("Error", "Passwords do not match")
            return

        # Insert to DB
        try:
            conn = get_connection()
            cur = conn.cursor()
            # check username uniqueness
            cur.execute("SELECT user_id FROM users WHERE username=%s", (un,))
            if cur.fetchone():
                messagebox.showerror("Error", "Username already exists. Choose another.")
                return

            # Insert - ensure your users table has these columns: full_name, email, contact, gender, country, username, password
            cur.execute("""
                INSERT INTO users (full_name, email, contact, gender, country, username, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (fn, em, ph, gd, cn, un, pw))
            conn.commit()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Could not register user: {e}")
            return
        finally:
            try:
                conn.close()
            except:
                pass

        messagebox.showinfo("Success", "Registration completed successfully! You can now login.")
        reg.destroy()

    # Register button (guaranteed to work)
    register_btn = Button(reg, text="Register", font=("Arial", 14, "bold"),
                          bg="#7a00ff", fg="white", width=20, command=register_user)
    register_btn.pack(pady=18)

    center(reg)
    reg.transient(root)
    reg.grab_set()
    reg.wait_window()

# -------------------- MAIN LOGIN WINDOW UI --------------------
root = Tk()
root.title("Login Page")
root.geometry("520x420")
root.configure(bg="#2e2931")

# Logo (if image exists)
logo_path = "img.jpg"
if os.path.exists(logo_path):
    try:
        # Assuming the image files are accessible for this environment
        # Fallback to text if PIL/ImageTk fails or file is missing
        logo_img = Image.open(logo_path).resize((420, 90))
        logo_photo = ImageTk.PhotoImage(logo_img)
        Label(root, image=logo_photo, bg="#2e2931").pack(pady=10)
    except:
        Label(root, text="BOOKZONE", font=("Arial", 22, "bold"), bg="#2e2931", fg="white").pack(pady=10)
else:
    Label(root, text="BOOKZONE", font=("Arial", 22, "bold"), bg="#2e2931", fg="white").pack(pady=10)

Label(root, text="Welcome to BookZone", font=("Arial", 16, "bold"),
      fg="#afc9e8", bg="#2e2931").pack(pady=4)

# Username
Label(root, text="Username:", font=("Arial", 12), bg="#2e2931", fg="white").pack(pady=(10, 0))
username_entry = Entry(root, font=("Arial", 12))
username_entry.pack(pady=4)

# Password
Label(root, text="Password:", font=("Arial", 12), bg="#2e2931", fg="white").pack(pady=(6, 0))
password_entry = Entry(root, show="*", font=("Arial", 12))
password_entry.pack(pady=4)

# Buttons
btn_frame = Frame(root, bg="#2e2931")
btn_frame.pack(pady=18)

login_btn = Button(btn_frame, text="Login", font=("Arial", 12, "bold"),
                   bg="#5e17eb", fg="white", width=14, command=login)
login_btn.grid(row=0, column=0, padx=8)

register_btn = Button(btn_frame, text="Register", font=("Arial", 12, "bold"),
                      bg="#ff6f91", fg="white", width=14, command=register)
register_btn.grid(row=0, column=1, padx=8)

# Helpful: press Enter to login
root.bind('<Return>', lambda e: login())

root.mainloop()