import os
import mysql.connector
from dotenv import load_dotenv

# Load database settings
load_dotenv()

try:
    # Connect to your Aiven MySQL database
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQL_PORT", 3306))
    )

    cursor = conn.cursor(dictionary=True)

    # 1. Show all tables in the database
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("--- TABLES IN YOUR CLOUD DATABASE ---")
    if not tables:
        print("No tables found.")
    for t in tables:
        # MySQL return tables as a dict with key 'Tables_in_defaultdb'
        print(f"Table name: {list(t.values())[0]}")
    print("------------------------------------\n")

    # 2. Show all users in the 'users' table
    cursor.execute("SELECT id, name, phone, email, emoji FROM users")
    users = cursor.fetchall()
    print("--- REGISTERED USERS IN 'users' TABLE ---")
    if not users:
        print("No users registered yet.")
    for u in users:
        print(f"ID: {u['id']} | Name: {u['name']} | Phone: {u['phone']} | Email: {u['email']} | Emoji: {u['emoji']}")
    print("-----------------------------------------")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error connecting to database: {e}")
