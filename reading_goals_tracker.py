import tkinter as tk
from tkinter import messagebox, ttk 
from datetime import datetime, timedelta
import mysql.connector
import smtplib
from email.message import EmailMessage

# --- EMAIL CONFIGURATION (REQUIRED: REPLACE PLACEHOLDERS) ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587 
SENDER_EMAIL = 'yooformee@gmail.com' # <-- CHECK THIS
SENDER_PASSWORD = 'Krishnaaa@13'     # <-- CHECK THIS (Requires App Password for Gmail)
# -----------------------------------------------------------

# --- DB CONFIG (Ensure this matches your credentials) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Krishna@13',
    'database': 'book_system'
}
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Helper function to get user ID and email (requires 'email' column in 'users' table)
def get_user_data(username):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, email FROM users WHERE username=%s", (username,))
        result = cur.fetchone()
        return {"user_id": result[0], "email": result[1]} if result else None
    except Exception:
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

# --- Email Notification Function ---
def send_completion_email(recipient_email, username, goal_type, target):
    if not recipient_email or SENDER_EMAIL == 'YOUR_SENDER_EMAIL@gmail.com':
        print("Email sending skipped: Recipient email missing or sender credentials not set.")
        return

    msg = EmailMessage()
    msg['Subject'] = f'🏆 Goal Completed: BookZone - Your {goal_type.capitalize()} Reading Goal!'
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    body = f"""
Hello {username},

Congratulations! You have successfully completed your {goal_type} reading goal!

Goal Achieved: {target} books read this {goal_type}.

Time to set a new challenge or pick your next read!

Happy Reading,
The BookZone Team
"""
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Goal completion email successfully sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# ----------------------------------------

# --- Goal Setter Logic ---
def save_goal_db(user_id, goal_type, target_value):
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT goal_id FROM reading_goals WHERE user_id=%s AND goal_type=%s", (user_id, goal_type))
        if cur.fetchone():
             cur.execute("UPDATE reading_goals SET goal_number=%s WHERE user_id=%s AND goal_type=%s", 
                         (target_value, user_id, goal_type))
        else:
             cur.execute("INSERT INTO reading_goals (user_id, goal_type, goal_number) VALUES (%s,%s,%s)", 
                         (user_id, goal_type, target_value))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("DB Error", f"Failed to save goal: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

# --- Progress Tracker Logic ---
def get_goal_progress(user_id, goal_type):
    conn = get_connection()
    progress = {"target": 0, "completed": 0, "start_date": None, "end_date": None}
    
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT goal_number FROM reading_goals WHERE user_id=%s AND goal_type=%s", (user_id, goal_type))
        goal_row = cur.fetchone()
        if not goal_row:
            return progress
            
        progress["target"] = goal_row[0]
        
        today = datetime.now()
        if goal_type == 'weekly':
            # Calculate start of the current week (Monday)
            progress["start_date"] = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=today.weekday())
        elif goal_type == 'monthly':
            # Calculate start of the current month
            progress["start_date"] = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        cur.execute("""
            SELECT COUNT(DISTINCT book_id)
            FROM reading_progress
            WHERE user_id=%s AND status='read' AND updated_at >= %s
        """, (user_id, progress["start_date"].strftime('%Y-%m-%d %H:%M:%S')))
        
        progress["completed"] = cur.fetchone()[0]
        return progress

    except Exception as e:
        print("Progress tracking error:", e)
        return progress
    finally:
        if conn and conn.is_connected():
            conn.close()

# --- Tkinter UI ---
def open_goal_tracker(username, parent):
    user_data = get_user_data(username)
    if not user_data:
        messagebox.showerror("Error", "User not found or missing email address.")
        return

    user_id = user_data["user_id"]
    user_email = user_data["email"]

    gt = tk.Toplevel(parent)
    gt.title(f"{username}'s Reading Goals")
    gt.geometry("400x350")
    gt.configure(bg="#f8f8ff")
    gt.attributes('-topmost', True) 

    tk.Label(gt, text="📖 Reading Goal Tracker", font=("Arial", 16, "bold"), bg="#f8f8ff").pack(pady=10)

    # Goal Setting Frame
    goal_frame = tk.Frame(gt, bg="#e6e6fa", padx=10, pady=10)
    goal_frame.pack(pady=10)

    goal_var = tk.StringVar(value="monthly")
    tk.Label(goal_frame, text="Goal Type:", bg="#e6e6fa").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    tk.Radiobutton(goal_frame, text="Weekly", variable=goal_var, value="weekly", bg="#e6e6fa").grid(row=0, column=1, padx=5, sticky="w")
    tk.Radiobutton(goal_frame, text="Monthly", variable=goal_var, value="monthly", bg="#e6e6fa").grid(row=0, column=2, padx=5, sticky="w")

    target_var = tk.IntVar(value=3)
    tk.Label(goal_frame, text="Target Books:", bg="#e6e6fa").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    tk.Entry(goal_frame, textvariable=target_var, width=5).grid(row=1, column=1, padx=5, sticky="w")
    tk.Label(goal_frame, text="books", bg="#e6e6fa").grid(row=1, column=2, padx=5, sticky="w")

    def set_goal():
        try:
            target = target_var.get()
            type_ = goal_var.get()
            if target <= 0: raise ValueError
            if save_goal_db(user_id, type_, target):
                messagebox.showinfo("Success", f"Goal set: {target} books {type_}ly.")
                update_progress_display() 
        except ValueError:
            messagebox.showerror("Error", "Target must be a positive number.")

    tk.Button(goal_frame, text="Set Goal", command=set_goal, bg="#4b0082", fg="white").grid(row=2, column=0, columnspan=3, pady=10)

    # Progress Display Frame
    progress_frame = tk.Frame(gt, bg="#f8f8ff")
    progress_frame.pack(pady=10)
    
    status_label = tk.Label(progress_frame, text="Current Progress:", font=("Arial", 12), bg="#f8f8ff")
    status_label.pack()

    progress_bar_style = ttk.Style()
    progress_bar_style.theme_use('clam')
    progress_bar_style.configure("Goal.TProgressbar", thickness=20, troughcolor="#cccccc", background="#9370db")

    progress_bar = ttk.Progressbar(progress_frame, style="Goal.TProgressbar", length=350)
    progress_bar.pack(pady=5)
    
    details_label = tk.Label(progress_frame, text="", bg="#f8f8ff")
    details_label.pack()

    def update_progress_display():
        weekly_progress = get_goal_progress(user_id, 'weekly')
        monthly_progress = get_goal_progress(user_id, 'monthly')
        
        goal_achieved_key = f"{username}_goal_achieved"
        already_notified = getattr(parent, goal_achieved_key, False)

        # Prioritize Monthly goal if set
        if monthly_progress["target"] > 0:
            display_progress = monthly_progress
            type_ = 'Monthly'
            type_key = 'monthly'
        elif weekly_progress["target"] > 0:
            display_progress = weekly_progress
            type_ = 'Weekly'
            type_key = 'weekly'
        else:
            progress_bar.config(value=0, maximum=100)
            details_label.config(text="No active goal set.")
            return

        target = display_progress["target"]
        completed = display_progress["completed"]

        # Calculate maximum and set progress
        progress_bar.config(maximum=target, value=completed)
        details_label.config(text=f"Target ({type_}): {completed} / {target} books read.")
        
        # Check for goal completion and notification
        if completed >= target and not already_notified:
            # Check if this goal type was just met
            current_goal_key = f"{username}_{type_key}_met"
            
            # Use parent attributes to track notification state
            if not getattr(parent, current_goal_key, False):
                send_completion_email(user_email, username, type_, target)
                messagebox.showinfo("Email Sent", f"Goal achieved! A confirmation email has been sent to {user_email}.")
                # Set flag so it doesn't notify again until restart or new goal
                setattr(parent, current_goal_key, True) 

    # Load initial goal data when opening
    update_progress_display()
    
    # Add a refresh button
    tk.Button(progress_frame, text="Refresh Progress", command=update_progress_display).pack(pady=10)