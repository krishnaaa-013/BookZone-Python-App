import csv
import mysql.connector
from googlesearch import search

# ---------------- DB Connection ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Krishna@13",
    database="book_system"
)
cursor = db.cursor(dictionary=True)

# -------------- Fetch All Book Titles ----------
cursor.execute("SELECT book_id, title FROM bookks")
books = cursor.fetchall()

result_rows = []

print("\nFetching Amazon links...\n")

for book in books:
    bid = book["book_id"]
    title = book["title"]

    query = f"{title} book amazon"
    amazon_link = "NOT FOUND"

    try:
        # get top google results
        for link in search(query, num_results=5):
            if "amazon" in link:
                amazon_link = link
                break
    except:
        pass

    result_rows.append([bid, title, amazon_link])
    print(f"{title}  -->  {amazon_link}")

# -------- Save to CSV --------
with open("book_links.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["book_id", "title", "amazon_link"])
    writer.writerows(result_rows)

print("\nDONE! Check file 'book_links.csv'")
