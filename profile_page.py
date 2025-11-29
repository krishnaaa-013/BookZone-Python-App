import tkinter as tk
from tkinter import messagebox
import mysql.connector

# DB connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Krishna@13",
        database="book_system"
    )

# ---------------------------------------------------------
# USER PROFILE PAGE
# ---------------------------------------------------------
def open_profile(username):
    prof = tk.Toplevel()
    prof.title("My Profile")
    prof.geometry("600x600")
    prof.configure(bg="white")

    # Header
    tk.Label(
        prof, text="👤 My Profile",
        font=("Arial", 22, "bold"),
        fg="#7a00ff",
        bg="white"
    ).pack(pady=20)

    # ---------------------------------------------------------
    # Fetch user info
    # ---------------------------------------------------------
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    conn.close()

    # USER DETAILS -----------------------------------------
    info_frame = tk.Frame(prof, bg="white")
    info_frame.pack(pady=10)

    def add_info(label, value):
        tk.Label(info_frame, text=f"{label}: ", font=("Arial", 14, "bold"), bg="white").pack(anchor="w")
        tk.Label(info_frame, text=value, font=("Arial", 13), bg="white").pack(anchor="w", pady=2)

    add_info("Full Name", user.get("full_name", ""))
    add_info("Email", user.get("email", ""))
    add_info("Phone", user.get("contact", ""))
    add_info("Gender", user.get("gender", ""))
    add_info("Country", user.get("country", ""))
    add_info("Username", user.get("username", ""))

    # ---------------------------------------------------------
    # READING PROGRESS COUNTS
    # ---------------------------------------------------------
    conn = get_connection()
    cur = conn.cursor()

    # Books Read
    cur.execute("SELECT COUNT(*) FROM reading_progress WHERE user_id=%s AND status='read'",
                (user['user_id'],))
    read_count = cur.fetchone()[0]

    # Reading Now
    cur.execute("SELECT COUNT(*) FROM reading_progress WHERE user_id=%s AND status='reading'",
                (user['user_id'],))
    reading_now = cur.fetchone()[0]

    # Want to Read
    cur.execute("SELECT COUNT(*) FROM reading_progress WHERE user_id=%s AND status='want to read'",
                (user['user_id'],))
    want_to_read = cur.fetchone()[0]

    conn.close()

    # Counts Section -----------------------------------------
    count_frame = tk.Frame(prof, bg="white")
    count_frame.pack(pady=20)

    tk.Label(count_frame, text="📚 Reading Stats", font=("Arial", 18, "bold"), fg="#7a00ff", bg="white").pack(pady=10)

    tk.Label(count_frame, text=f"✔ Books Read: {read_count}", font=("Arial", 14), bg="white").pack(pady=4)
    tk.Label(count_frame, text=f"📖 Reading Now: {reading_now}", font=("Arial", 14), bg="white").pack(pady=4)
    tk.Label(count_frame, text=f"📝 Want to Read: {want_to_read}", font=("Arial", 14), bg="white").pack(pady=4)

    # ---------------------------------------------------------
    # PASSWORD CHANGE SECTION
    # ---------------------------------------------------------
    tk.Label(
        prof, text="\n🔐 Change Password",
        font=("Arial", 18, "bold"), fg="#7a00ff", bg="white"
    ).pack(pady=10)

    tk.Label(prof, text="New Password:", bg="white", font=("Arial", 12)).pack()
    new_pass_entry = tk.Entry(prof, show="*", font=("Arial", 12))
    new_pass_entry.pack(pady=5)

    def update_password():
        new_pass = new_pass_entry.get().strip()
        if not new_pass:
            messagebox.showerror("Error", "Password cannot be empty")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=%s WHERE username=%s", (new_pass, username))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Password updated successfully!")

    tk.Button(
        prof, text="Update Password",
        bg="#7a00ff", fg="white",
        font=("Arial", 12, "bold"),
        command=update_password
    ).pack(pady=15)

    prof.mainloop()
