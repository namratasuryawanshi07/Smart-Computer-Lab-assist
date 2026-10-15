from db import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT DATABASE()")
result = cursor.fetchone()
print("Connected to database:", result[0])
conn.close()