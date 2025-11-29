import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector
import os
import webbrowser
from urllib.parse import quote 

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Krishna@13',
    'database': 'book_system'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def mark_reading_status_db(username, book_id, status):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username=%s", (username,))
        r = cur.fetchone()
        if not r:
            return False, "User not found"
        user_id = r[0]
        # ensure updated_at column exists (safe)
        try:
            cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='reading_progress' AND COLUMN_NAME='updated_at'")
            if cur.fetchone()[0] == 0:
                try:
                    cur.execute("ALTER TABLE reading_progress ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                except Exception:
                    pass
        except Exception:
            pass
        cur.execute("SELECT id FROM reading_progress WHERE user_id=%s AND book_id=%s", (user_id, book_id))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE reading_progress SET status=%s, updated_at=NOW() WHERE user_id=%s AND book_id=%s", (status, user_id, book_id))
        else:
            try:
                cur.execute("INSERT INTO reading_progress (user_id, book_id, status, updated_at) VALUES (%s,%s,%s,NOW())", (user_id, book_id, status))
            except Exception:
                cur.execute("INSERT INTO reading_progress (user_id, book_id, status) VALUES (%s,%s,%s)", (user_id, book_id, status))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()

def add_like_db(username, book_id):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # simple implementation: increment like_count in bookks if such column exists,
        # otherwise create a user_likes table
        try:
            cur.execute("ALTER TABLE bookks ADD COLUMN likes INT DEFAULT 0")
        except Exception:
            pass
        cur.execute("UPDATE bookks SET likes = IFNULL(likes,0) + 1 WHERE book_id=%s", (book_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()

def set_rating_db(username, book_id, rating):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # naive: add rating column (AVG not persisted) — for demo we store ratings in ratings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ratings(
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                book_id INT,
                rating INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("SELECT user_id FROM users WHERE username=%s", (username,))
        r = cur.fetchone()
        if not r:
            return False, "User not found"
        user_id = r[0]
        # replace user's previous rating
        cur.execute("DELETE FROM ratings WHERE user_id=%s AND book_id=%s", (user_id, book_id))
        cur.execute("INSERT INTO ratings(user_id, book_id, rating) VALUES (%s,%s,%s)", (user_id, book_id, rating))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()

def open_book_details(book, username, parent=None):
    # book is expected to be a dictionary-like object from DB
    bd = tk.Toplevel(parent)
    bd.title(book.get('title','Book Details'))
    bd.geometry("700x520")
    bd.configure(bg="white")

    # top: cover and info
    top = tk.Frame(bd, bg="white")
    top.pack(fill="x", padx=12, pady=12)

    # cover
    img_path = book.get("cover_image") or ""
    if img_path and not os.path.isabs(img_path):
        img_path = os.path.join(os.getcwd(), img_path)
    try:
        img = Image.open(img_path).resize((220, 280))
        photo = ImageTk.PhotoImage(img)
        cover_lbl = tk.Label(top, image=photo, bg="white")
        cover_lbl.image = photo
        cover_lbl.pack(side="left", padx=12)
    except Exception:
        tk.Label(top, text="[No Image]", bg="#e6e6e6", width=30, height=16).pack(side="left", padx=12)

    # info block
    info = tk.Frame(top, bg="white")
    info.pack(side="left", fill="both", expand=True, padx=8)

    tk.Label(info, text=book.get("title","Unknown"), font=("Arial", 16, "bold"), bg="white", wraplength=420, justify="left").pack(anchor="w")
    tk.Label(info, text=f"Genre: {book.get('genre','')}", font=("Arial", 12), bg="white").pack(anchor="w", pady=(6,0))
    rating_text = f"Rating: {book.get('rating', 'N/A')}"
    tk.Label(info, text=rating_text, font=("Arial", 12), bg="white").pack(anchor="w", pady=(6,0))

    # Buttons (Like, Want to Read, Mark Read)
    btn_frame = tk.Frame(info, bg="white")
    btn_frame.pack(anchor="w", pady=12)

    def like_action():
        ok, err = add_like_db(username, book.get("book_id"))
        if ok:
            messagebox.showinfo("Liked", "You liked this book ❤️")
        else:
            messagebox.showerror("Error", f"Could not like: {err}")

    def want_action():
        ok, err = mark_reading_status_db(username, book.get("book_id"), "want to read")
        if ok:
            messagebox.showinfo("Saved", "Marked as 'Want to Read'")
        else:
            messagebox.showerror("Error", f"Could not save: {err}")

    def read_action():
        ok, err = mark_reading_status_db(username, book.get("book_id"), "read")
        if ok:
            messagebox.showinfo("Saved", "Marked as 'Read' ✔")
        else:
            messagebox.showerror("Error", f"Could not save: {err}")

    tk.Button(btn_frame, text="❤️ Like", bg="#ffd6e0", command=like_action).pack(side="left", padx=6)
    tk.Button(btn_frame, text="📘 Want to Read", bg="#d1ecf1", command=want_action).pack(side="left", padx=6)
    tk.Button(btn_frame, text="✔ Mark as Read", bg="#d4edda", command=read_action).pack(side="left", padx=6)

    # Rating section
    rating_frame = tk.Frame(info, bg="white")
    rating_frame.pack(anchor="w", pady=(8,0))
    tk.Label(rating_frame, text="Rate this book:", bg="white").pack(side="left", padx=(0,6))

    rating_var = tk.IntVar(value=0)
    def submit_rating():
        val = rating_var.get()
        if val < 1 or val > 5:
            messagebox.showerror("Error", "Select rating 1-5")
            return
        ok, err = set_rating_db(username, book.get("book_id"), val)
        if ok:
            messagebox.showinfo("Thanks!", "Your rating has been saved")
        else:
            messagebox.showerror("Error", f"Could not save rating: {err}")

    for i in range(1,6):
        tk.Radiobutton(rating_frame, text=str(i), variable=rating_var, value=i, bg="white").pack(side="left")

    tk.Button(rating_frame, text="Submit", command=submit_rating).pack(side="left", padx=8)

    # -----------------------------------------------------
    # Summary area (below)
    # -----------------------------------------------------
    summary_frame = tk.Frame(bd, bg="white")
    summary_frame.pack(fill="both", expand=True, padx=12, pady=(6,12))

    tk.Label(summary_frame, text="Summary:", font=("Arial", 14, "bold"), bg="white").pack(anchor="w")
    summary_text = tk.Text(summary_frame, wrap="word", height=10, bg="#fffdf5")
    summary_text.insert("1.0", book.get("summary","No summary available"))
    summary_text.config(state="disabled")
    summary_text.pack(fill="both", expand=True, pady=(6,6))

    # Amazon / external link if provided
    link_frame = tk.Frame(bd, bg="white")
    link_frame.pack(fill="x", padx=12, pady=(0,12))
    
    # --- FEATURE: DYNAMIC BUY BUTTON LOGIC ---
    book_title = book.get("title", "Unknown Book") 

    def open_amazon():
        # Encode the title (e.g., 'The Glass House' -> 'The%20Glass%20House')
        formatted_title = quote(book_title) 
        
        # Construct the dynamic search URL for Amazon India
        search_url = f"https://www.amazon.in/s?k={formatted_title}"
        
        # Open the default web browser to the search results
        webbrowser.open(search_url)

    # The 'Buy on Amazon' button now uses the new open_amazon function
    tk.Button(link_frame, text="Buy on Amazon", bg="#ffd6b6", command=open_amazon).pack(side="left", padx=6)
    # ----------------------------------------

    # The PDF button remains the same
    tk.Button(link_frame, text="Open PDF / Read Now", bg="#d1ecf1", command=lambda: messagebox.showinfo("Read", "Open your reader or provide reader integration.")).pack(side="left", padx=6)

    # --- NEW: BACK TO DASHBOARD BUTTON ---
    tk.Button(link_frame, text="<< Back to Dashboard", bg="#cccccc", command=bd.destroy).pack(side="right", padx=6)
    # -------------------------------------

    return bd

# quick test if run directly
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    fake = {
        "book_id": 1,
        "title": "The Glass House (A Very Long Title to Test Wrapping)",
        "genre": "Mystery",
        "summary": "A mansion's mirrors hide clues to a buried crime. This is a placeholder summary to demonstrate how the text area wraps and displays content about the book's plot and setting. It provides enough detail to satisfy a user's curiosity about the story.",
        "cover_image": "",  # put a path if you want
        "rating": 4.5,
        "amazon_link": "" 
    }
    open_book_details(fake, "TestUser")
    root.mainloop()