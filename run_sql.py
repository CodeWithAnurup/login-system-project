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
    conn.autocommit = True
    cursor = conn.cursor(dictionary=True)

    print("=== Interactive SQL Runner ===")
    print("Type your SQL query below and press Enter (Type 'exit' to quit).")
    print("Example: SELECT * FROM users;")
    print("==============================")

    while True:
        try:
            query = input("\nSQL> ").strip()
            if not query:
                continue
            if query.lower() in ['exit', 'quit']:
                break

            cursor.execute(query)

            # Check if it was a SELECT query that returns rows
            if cursor.description:
                results = cursor.fetchall()
                if not results:
                    print("No rows returned.")
                else:
                    # Print headers
                    headers = results[0].keys()
                    print(" | ".join(headers))
                    print("-" * 50)
                    # Print rows
                    for row in results:
                        print(" | ".join(str(val) for val in row.values()))
            else:
                print(f"Query OK. Affected rows: {cursor.rowcount}")

        except Exception as query_error:
            print(f"SQL Error: {query_error}")

    cursor.close()
    conn.close()
    print("SQL session closed.")

except Exception as e:
    print(f"Connection Error: {e}")
