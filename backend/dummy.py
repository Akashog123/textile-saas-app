import sqlite3

conn = sqlite3.connect("instance/se_textile.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM reviews")
print(cursor.fetchone())
