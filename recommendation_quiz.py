# --- recommendation_quiz.py (Complete Code with UI Setup) ---
import tkinter as tk
from tkinter import messagebox
from collections import Counter
import threading 

# --- FULL LIST OF 5 QUESTIONS ---
SEQUENTIAL_QUIZ_QUESTIONS = [
    {"q": "Q1: Choose your pace: High action or deep feeling?", "genre_map": {"Action/Pace": "Thriller", "Emotional/Comfort": "Romance"}},
    {"q": "Q2: Choose your world: Reality or imagination?", "genre_map": {"Real-World Puzzle": "Mystery", "Magic/Deep Lore": "Fantasy"}},
    {"q": "Q3: Choose your goal: Growth or escape?", "genre_map": {"Growth/Insight": "Inspirational", "High Adventure": "Adventure"}},
    {"q": "Q4: Choose your time period: Past or Future?", "genre_map": {"The Past": "Historical Fiction", "The Future": "Sci-Fi"}},
    {"q": "Q5: Choose your intensity: Gentle or Tense?", "genre_map": {"Gentle/Sweet": "Romance", "Tense/Dark": "Horror"}}
]

def calculate_recommendation(all_answers, show_books_callback, load_books_callback, show_message=True):
    """Calculates the final recommendation and filters the books."""
    if not all_answers:
        if show_message: messagebox.showinfo("Recommendation", "No answers provided. Displaying all books.")
        recommended_books = load_books_callback()
        show_books_callback(recommended_books)
        return
        
    genre_counts = Counter(all_answers)
    recommended_genre = genre_counts.most_common(1)[0][0]
    
    if show_message: messagebox.showinfo("Final Recommendation", f"Quiz finished! Recommended genre: **{recommended_genre}**")
    
    recommended_books = load_books_callback(genre_filter=recommended_genre)
    show_books_callback(recommended_books)
    return recommended_genre 

def open_sequential_quiz_step(parent, question_index, current_answers, next_step_callback, show_books_callback, load_books_callback):
    """Opens a Toplevel window for a single quiz step."""
    
    if question_index >= len(SEQUENTIAL_QUIZ_QUESTIONS):
        # Quiz is over, perform final calculation
        calculate_recommendation(current_answers, show_books_callback, load_books_callback, show_message=True)
        return

    q_data = SEQUENTIAL_QUIZ_QUESTIONS[question_index]
    
    quiz_win = tk.Toplevel(parent)
    quiz_win.title(f"Quiz Step {question_index + 1} of {len(SEQUENTIAL_QUIZ_QUESTIONS)}")
    quiz_win.geometry("400x200") # Add geometry
    quiz_win.configure(bg="#ffffe0") # Add background color
    quiz_win.attributes('-topmost', True) # Keep window on top

    # UI Setup: Question Label
    tk.Label(quiz_win, text=q_data["q"], font=("Arial", 12, "bold"), bg="#ffffe0").pack(pady=10)

    selected_genre = tk.StringVar(value="")
    
    # UI Setup: Radiobutton Frame
    q_frame = tk.Frame(quiz_win, bg="#ffffe0")
    q_frame.pack(pady=5)
    
    for option, genre_map in q_data["genre_map"].items():
        tk.Radiobutton(q_frame, text=option, variable=selected_genre, value=genre_map, bg="#ffffe0", anchor="w", width=20).pack(pady=2)

    def submit_answer():
        answer = selected_genre.get()
        if not answer:
            messagebox.showwarning("Incomplete", "Please select an option before proceeding.", parent=quiz_win)
            return

        current_answers.append(answer)
        quiz_win.destroy()
        
        # --- SAFELY THREADED LIVE UPDATE LOGIC ---
        def run_live_update():
            try:
                # Calculate the current running recommendation (no popup message)
                calculate_recommendation(current_answers, show_books_callback, load_books_callback, show_message=False)
            except Exception as e:
                print(f"Error during quiz recommendation calculation: {e}")
                parent.after(0, lambda: messagebox.showerror("Quiz Error", f"A database error occurred: {e}"))
            
            # Trigger the next step (MUST be on main thread to manage `root.after()`)
            parent.after(0, lambda: next_step_callback(question_index + 1))
            
        threading.Thread(target=run_live_update).start()
        
        
    def on_closing():
        quiz_win.destroy()
        
        def run_final_calc():
            try:
                calculate_recommendation(current_answers, show_books_callback, load_books_callback, show_message=True)
            except Exception as e:
                 parent.after(0, lambda: messagebox.showerror("Quiz Error", f"Final calc error: {e}"))
            
            # Stop the future timers in the main app (MUST be on main thread)
            parent.after(0, lambda: setattr(parent, 'quiz_in_progress', False))
            if parent.quiz_job_id:
                 parent.after(0, lambda: parent.after_cancel(parent.quiz_job_id))
                 
        threading.Thread(target=run_final_calc).start()
        
    quiz_win.protocol("WM_DELETE_WINDOW", on_closing)

    tk.Button(quiz_win, text="Next Step >>", command=submit_answer, bg="#7a00ff", fg="white", font=("Arial", 10, "bold")).pack(pady=10)