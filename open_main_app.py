import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import mysql.connector
import os
import datetime
import webbrowser
from urllib.parse import quote 
from collections import Counter 

# --- FEATURE IMPORTS ---
try:
    from reading_goals_tracker import open_goal_tracker 
except ImportError:
    def open_goal_tracker(username, parent):
        messagebox.showinfo("Error", "Missing reading_goals_tracker.py file.")

try:
    from recommendation_quiz import open_sequential_quiz_step, SEQUENTIAL_QUIZ_QUESTIONS, calculate_recommendation
except ImportError:
    def open_sequential_quiz_step(*args, **kwargs):
        messagebox.showinfo("Error", "Missing recommendation_quiz.py file.")
    SEQUENTIAL_QUIZ_QUESTIONS = []
    def calculate_recommendation(*args, **kwargs):
        pass

# try to import camera mood function — optional
try:
    from camera_mood import detect_mood_camera
    CAMERA_AVAILABLE = True
except Exception:
    CAMERA_AVAILABLE = False

# book details opener (separate file)
try:
    from book_details import open_book_details
except Exception:
    def open_book_details(book, username, parent=None):
        messagebox.showinfo("Book Details", f"Would open details for: {book.get('title')}")

# --- VOICE ASSISTANT IMPORTS ---
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("WARNING: Speech libraries (speech_recognition/pyttsx3/PyAudio) not installed. Voice search disabled.")
# ------------------------------

# -------------------- DB CONFIG --------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Krishna@13', 
    'database': 'book_system'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# -------------------- Voice Search Logic --------------------
def get_voice_search_term():
    """Listens for the user's voice input and returns the recognized text."""
    if not VOICE_AVAILABLE:
        return ""

    r = sr.Recognizer()
    engine = pyttsx3.init()
    engine.say("Speak the book title or genre you want to search.")
    engine.runAndWait()
    
    with sr.Microphone() as source:
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening for search term...")
            
            audio = r.listen(source, timeout=5) 
            print("Recognizing...")
            
            search_term = r.recognize_google(audio)
            
            print(f"Recognized: {search_term}")
            engine.say(f"Searching for {search_term}.")
            engine.runAndWait()
            
            return search_term
            
        except sr.WaitTimeoutError:
            engine.say("No speech detected. Please try again.")
            engine.runAndWait()
            return ""
        except sr.UnknownValueError:
            engine.say("Sorry, I could not understand that.")
            engine.runAndWait()
            return ""
        except sr.RequestError as e:
            engine.say("Speech service is unavailable.")
            engine.runAndWait()
            return ""
        except Exception as e:
            print(f"General Voice Error: {e}")
            return ""
# -----------------------------------------------------------


# -------------------- Ensure helper tables/columns --------------------
def ensure_tables_and_columns():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Ensure reading_progress has updated_at column
        try:
            cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='reading_progress' AND COLUMN_NAME='updated_at'")
            if cur.fetchone()[0] == 0:
                cur.execute("ALTER TABLE reading_progress ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass
            
        conn.commit()
    except Exception:
        pass
    finally:
        if conn and conn.is_connected():
            conn.close()

# -------------------- Load books --------------------
def load_books(search_term="", genre_filter=None):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        if search_term:
            term = f"%{search_term}%"
            cur.execute("SELECT * FROM bookks WHERE title LIKE %s OR genre LIKE %s OR summary LIKE %s", (term, term, term))
        elif genre_filter:
            cur.execute("SELECT * FROM bookks WHERE genre=%s", (genre_filter,))
        else:
            cur.execute("SELECT * FROM bookks ORDER BY RAND() LIMIT 40")
        return cur.fetchall()
    except Exception as e:
        print("load_books error:", e)
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

# -------------------- Recommendation Helpers --------------------
def get_popular_books():
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT b.title, COUNT(rp.book_id) AS read_count
            FROM bookks b
            JOIN reading_progress rp ON b.book_id = rp.book_id
            WHERE rp.status = 'read'
            GROUP BY b.book_id
            ORDER BY read_count DESC
            LIMIT 5
        """)
        return cur.fetchall()
    except Exception:
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_user_history_genres(username):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username=%s", (username,))
        r = cur.fetchone()
        if not r: return []
        user_id = r[0]
        
        cur.execute("""
            SELECT b.genre, COUNT(rp.book_id) AS action_count
            FROM reading_progress rp
            JOIN bookks b ON rp.book_id = b.book_id
            WHERE rp.user_id = %s
            GROUP BY b.genre
            ORDER BY action_count DESC
            LIMIT 2
        """, (user_id,))
        return [r[0] for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def populate_recommendation_panel(parent_frame, current_username):
    for widget in parent_frame.winfo_children():
        widget.destroy()

    tk.Label(parent_frame, text="🔥 Popular Now", font=("Arial", 11, "bold"), bg="#f3e8ff", fg="#5e17eb").pack(anchor="w", pady=(0, 5))
    popular_books = get_popular_books()
    
    if popular_books:
        for book in popular_books:
            tk.Label(parent_frame, text=f"- {book['title']} ({book['read_count']} reads)", font=("Arial", 9), bg="#f3e8ff", wraplength=230, justify="left").pack(anchor="w", fill="x")
    else:
        tk.Label(parent_frame, text="No popular data yet.", font=("Arial", 9), bg="#f3e8ff").pack(anchor="w", fill="x")

    tk.Frame(parent_frame, height=1, bg="#7a00ff").pack(fill="x", pady=10)

    tk.Label(parent_frame, text=f"👤 Personalized for You", font=("Arial", 11, "bold"), bg="#f3e8ff", fg="#5e17eb").pack(anchor="w", pady=(0, 5))
    
    top_genres = get_user_history_genres(current_username)
    
    if top_genres:
        tk.Label(parent_frame, text=f"Your top genres:", font=("Arial", 9, "italic"), bg="#f3e8ff").pack(anchor="w")
        for genre in top_genres:
            tk.Label(parent_frame, text=f"• {genre}", font=("Arial", 10, "bold"), bg="#f3e8ff", fg="#7a00ff").pack(anchor="w")
        
        tk.Label(parent_frame, text="\nTry these related genres:", font=("Arial", 9, "italic"), bg="#f3e8ff").pack(anchor="w")
        
        for genre in top_genres:
            books = load_books(genre_filter=genre)
            for book in books[:2]:
                    tk.Label(parent_frame, text=f"- {book['title']}", font=("Arial", 9), bg="#f3e8ff", wraplength=230, justify="left").pack(anchor="w", fill="x")
            
    else:
        tk.Label(parent_frame, text="Mark some books as 'Read' or 'Want to Read' to see personalized suggestions!", font=("Arial", 9), bg="#f3e8ff", wraplength=230, justify="left").pack(anchor="w", fill="x")


# -------------------- Camera/Mood Helpers --------------------
def save_mood_for_user(username, mood):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username=%s", (username,))
        r = cur.fetchone()
        if not r:
            return
        user_id = r[0]
        cur.execute("INSERT INTO mood_history (user_id, mood) VALUES (%s,%s)", (user_id, mood))
        conn.commit()
    except Exception:
        pass
    finally:
        if conn and conn.is_connected():
            conn.close()

def map_camera_mood_to_genre(mood):
    if not mood:
        return None
    mood = mood.lower()
    if mood in ("happy", "surprise"):
        return "Romance"
    if mood == "sad":
        return "Inspirational"
    if mood == "neutral":
        return "Mystery"
    if mood in ("angry", "disgust"):
        return "Thriller"
    if mood == "fear":
        return "Horror"
    return "Fantasy"

# -------------------- Amazon Link Helper --------------------
def open_amazon_link(book_title):
    formatted_title = quote(book_title) 
    url = f"https://www.amazon.in/s?k={formatted_title}"
    webbrowser.open(url)
# ------------------------------------------------------------------

# -------------------- Open main app --------------------
def open_main_app(username):
    ensure_tables_and_columns()

    root = tk.Toplevel()
    root.title("BookZone - Home")
    root.geometry("1200x720")
    root.config(bg="white")
    
    # --- SEQUENTIAL QUIZ STATE ---
    root.quiz_in_progress = False 
    root.quiz_answers = [] 
    root.quiz_job_id = None 
    QUIZ_INTERVAL_MS = 10000 # 30 seconds between steps
    
    def manage_sequential_quiz(step_index=0):
        # Cancel any previous timer job 
        if root.quiz_job_id:
            root.after_cancel(root.quiz_job_id)

        if step_index >= len(SEQUENTIAL_QUIZ_QUESTIONS):
            # Sequence finished
            root.quiz_in_progress = False
            return
            
        root.quiz_in_progress = True
        
        # Open the specific question pop-up
        open_sequential_quiz_step(
            parent=root, 
            question_index=step_index, 
            current_answers=root.quiz_answers, 
            # Pass the delay function for the next step
            next_step_callback=manage_sequential_quiz_with_delay, 
            show_books_callback=root.show_books, 
            load_books_callback=load_books
        )

    def manage_sequential_quiz_with_delay(next_step_index):
        """Starts the 30-second countdown for the next step."""
        if not root.winfo_exists():
            return 
        
        if next_step_index >= len(SEQUENTIAL_QUIZ_QUESTIONS):
            root.quiz_in_progress = False
            return
            
        # Schedule the next step popup after 30 seconds
        root.quiz_job_id = root.after(QUIZ_INTERVAL_MS, lambda: manage_sequential_quiz(next_step_index))
    
    # --- END SEQUENTIAL QUIZ TIMER LOGIC ---
    
    # header
    header = tk.Frame(root, bg="#7a00ff")
    header.pack(fill="x")
    tk.Label(header, text="📚 BookZone", font=("Arial", 20, "bold"), bg="#7a00ff", fg="white").pack(side="left", padx=12, pady=10)
    tk.Label(header, text=f"Welcome, {username}", font=("Arial", 11), bg="#7a00ff", fg="white").pack(side="left", padx=8)

    # top controls
    top_frame = tk.Frame(root, bg="white")
    top_frame.pack(fill="x", padx=12, pady=8)

    # search and voice search
    search_entry = tk.Entry(top_frame, font=("Arial", 13), width=30)
    search_entry.pack(side="left", padx=(0,8))
    
    # Manual text search handler (now accepts the term)
    def do_search(term=None):
        if term is None:
            term = search_entry.get().strip()
        show_books(load_books(search_term=term))

    # --- VOICE SEARCH HANDLER ---
    def voice_search_action():
        term = get_voice_search_term()
        if term:
            search_entry.delete(0, tk.END) # Clear manual entry
            search_entry.insert(0, term) # Display the recognized term
            do_search(term)
    
    # The normal Search button now calls do_search without arguments
    tk.Button(top_frame, text="🔍 Search", bg="#5e17eb", fg="white", command=lambda: do_search()).pack(side="left", padx=6)
    
    # NEW: Voice Search Button
    voice_btn = tk.Button(top_frame, text="🎙️ Speak Search", bg="#4CAF50", fg="white", command=voice_search_action)
    voice_btn.pack(side="left", padx=6)

    # Disable the voice button if libraries are missing
    if not VOICE_AVAILABLE:
        voice_btn.config(state=tk.DISABLED, text="🎙️ Speak Search (Disabled)")
    # ----------------------------

    # profile (if you have profile_page.py)
    try:
        from profile_page import open_profile
        tk.Button(top_frame, text="👤 Profile", bg="#d9d2ff", command=lambda: open_profile(username)).pack(side="left", padx=6)
    except Exception:
        pass

    # camera mood button
    def camera_detect_action():
        if not CAMERA_AVAILABLE:
            messagebox.showinfo("Camera Disabled", "Camera mood detection is not available on this machine (missing module).")
            return
        try:
            mood, err = detect_mood_camera()
            if err:
                messagebox.showerror("Camera Error", err)
                return
            genre = map_camera_mood_to_genre(mood)
            if genre:
                save_mood_for_user(username, mood)
                messagebox.showinfo("Mood Detected", f"Detected: {mood}\nShowing: {genre} books")
                show_books(load_books(genre_filter=genre))
            else:
                messagebox.showinfo("Mood Detected", f"Detected: {mood} — no mapping found.")
        except Exception as e:
            messagebox.showerror("Camera Error", str(e))

    cam_btn = tk.Button(top_frame, text="🎥 Detect Mood", bg="#ffbbe6", command=camera_detect_action)
    cam_btn.pack(side="left", padx=6)
    
    # --- FEATURE: GOAL TRACKER BUTTON ---
    tk.Button(top_frame, text="🎯 Set Goals", bg="#ff9900", fg="white", 
              command=lambda: open_goal_tracker(username, root)).pack(side="left", padx=6)
    # ------------------------------------
    
    # --- FEATURE: BOOK QUIZ BUTTON (Manual trigger) ---
    def manual_open_quiz():
        if root.quiz_in_progress:
            messagebox.showinfo("Quiz In Progress", "The automatic quiz is already running. Please complete it.")
            return

        # Reset and start the sequential quiz immediately (step 0)
        root.quiz_answers = []
        manage_sequential_quiz(0) 

    tk.Button(top_frame, text="❓ Book Quiz", bg="#c6e2ff", 
              command=manual_open_quiz).pack(side="left", padx=6)
    # ---------------------------------
    
    if not CAMERA_AVAILABLE:
        cam_btn.config(state="normal") 

    # dropdown for all genres (right side)
    genres = ["All", "Romance", "Mystery", "Fantasy", "Sci-Fi", "Horror", "Adventure", "Thriller", "Inspirational", "Historical Fiction"]
    genre_var = tk.StringVar(value="All")
    genre_dropdown = ttk.Combobox(top_frame, values=genres, textvariable=genre_var, state="readonly", width=22)
    genre_dropdown.pack(side="right", padx=(6,0))
    def apply_dropdown():
        g = genre_var.get()
        if g == "All":
            show_books(load_books())
        else:
            show_books(load_books(genre_filter=g))
    tk.Button(top_frame, text="Apply", bg="#e8d6ff", command=apply_dropdown).pack(side="right", padx=6)

    # quick row
    quick_frame = tk.Frame(root, bg="white")
    quick_frame.pack(fill="x", padx=12)
    for g in ["Romance", "Thriller", "Inspirational", "Horror"]:
        tk.Button(quick_frame, text=g, width=14, bg="#d9d2ff", command=lambda gg=g: show_books(load_books(genre_filter=gg))).pack(side="left", padx=6, pady=6)

    # main body structure (Restructured for Recommendation Panel)
    body = tk.Frame(root, bg="white")
    body.pack(fill="both", expand=True, padx=12, pady=(6,12))

    # --- NEW RECOMMENDATION PANEL (RIGHT SIDE) ---
    rec_panel = tk.Frame(body, width=250, bg="#f3e8ff", padx=10, pady=10, bd=1, relief="solid")
    rec_panel.pack(side="right", fill="y", padx=(12, 0))
    rec_panel.pack_propagate(False) 

    # --- MAIN CONTENT FRAME (LEFT SIDE - Holds Books) ---
    main_content_frame = tk.Frame(body, bg="white")
    main_content_frame.pack(side="left", fill="both", expand=True) 

    # Now, the canvas and scrollbar go inside the main_content_frame
    canvas = tk.Canvas(main_content_frame, bg="white", highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_content_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    book_images = [] 

    # tooltip window for summary
    tooltip = tk.Toplevel(root)
    tooltip.withdraw()
    tooltip.overrideredirect(True)
    tooltip.attributes("-topmost", True)
    tip_label = tk.Label(tooltip, text="", bg="#ffffe0", justify="left", wraplength=300, font=("Arial",10), bd=1, relief="solid")
    tip_label.pack(ipadx=6, ipady=4)

    def show_tooltip(event, text):
        tip_label.config(text=text)
        x = event.x_root + 12
        y = event.y_root + 10
        tooltip.geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def hide_tooltip(event):
        tooltip.withdraw()

    # show_books implementation
    def show_books(books):
        for w in scrollable_frame.winfo_children():
            w.destroy()
        book_images.clear()

        if not books:
            tk.Label(scrollable_frame, text="No books found.", bg="white", font=("Arial", 14)).pack(pady=20)
            return

        cols = 4
        for idx, book in enumerate(books):
            r = idx // cols
            c = idx % cols
            card = tk.Frame(scrollable_frame, bg="white", bd=1, relief="raised", padx=8, pady=8)
            card.grid(row=r, column=c, padx=12, pady=12, sticky="n")
            card.bind("<Enter>", lambda e, w=card: w.config(bg="#f3e8ff"))
            card.bind("<Leave>", lambda e, w=card: w.config(bg="white"))

            # load image
            img_path = book.get("cover_image") or ""
            if img_path and not os.path.isabs(img_path):
                img_path = os.path.join(os.getcwd(), img_path)
            try:
                img = Image.open(img_path).resize((140,180))
                photo = ImageTk.PhotoImage(img)
                book_images.append(photo)
                img_lbl = tk.Label(card, image=photo, bg="white")
                img_lbl.pack()
            except Exception:
                img_lbl = tk.Label(card, text="[No Image]", bg="#e6e6e6", width=18, height=10)
                img_lbl.pack()

            # title + genre
            title_label = tk.Label(card, text=book.get("title","Unknown"), font=("Arial", 11, "bold"), bg="white", wraplength=160, justify="center")
            title_label.pack(pady=(6,2))
            genre_label = tk.Label(card, text=book.get("genre",""), font=("Arial", 9), fg="gray", bg="white")
            genre_label.pack()
            
            # --- FEATURE: DYNAMIC BUY BUTTON ON CARD ---
            book_title = book.get("title", "Unknown") 
            buy_btn = tk.Button(card, text="🛒 Buy Now", 
                                 bg="#ff9900", fg="white", 
                                 font=("Arial", 10),
                                 command=lambda title=book_title: open_amazon_link(title))
            buy_btn.pack(pady=(8, 4))
            # ---------------------------------------------

            # bind hover to show summary tooltip
            summary_text = book.get("summary","No summary available")
            img_lbl.bind("<Enter>", lambda e, t=summary_text: show_tooltip(e, t))
            img_lbl.bind("<Leave>", hide_tooltip)
            title_label.bind("<Enter>", lambda e, t=summary_text: show_tooltip(e, t))
            title_label.bind("<Leave>", hide_tooltip)

            # click opens detailed page
            card.bind("<Button-1>", lambda e, b=book: open_book_details(b, username, root))
            img_lbl.bind("<Button-1>", lambda e, b=book: open_book_details(b, username, root))
            title_label.bind("<Button-1>", lambda e, b=book: open_book_details(b, username, root))

    # initial load
    populate_recommendation_panel(rec_panel, username) 
    show_books(load_books())

    # expose this for quiz/other module filtering
    root.show_books = show_books

    # ensure canvas resizes nicely
    def on_resize(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    root.bind("<Configure>", on_resize)
    
    # *** START THE AUTOMATIC QUIZ SEQUENCE AFTER A SHORT INITIAL DELAY ***
    root.after(5000, lambda: manage_sequential_quiz_with_delay(0)) 

    return root

# allow running standalone for quick test
if __name__ == "__main__":
    tk_root = tk.Tk()
    tk_root.withdraw()
    # Replace 'TestUser' with a valid username from your 'users' table for testing database access
    open_main_app("TestUser") 
    tk_root.mainloop()