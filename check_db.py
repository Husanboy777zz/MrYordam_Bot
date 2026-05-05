import sqlite3
from pathlib import Path

DB_PATH = "bot_data.db"

def check_db():
    if not Path(DB_PATH).exists():
        print(f"Ma'lumotlar bazasi ({DB_PATH}) hali yaratilmagan.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("=== RO'YXATDAN O'TGAN FOYDALANUVCHILAR (SHOP OWNERS) ===")
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    if not users:
        print("Foydalanuvchilar topilmadi.")
    for user in users:
        print(user)

    print("\n=== MIJOZLAR (CLIENTS) ===")
    c.execute("SELECT * FROM clients")
    clients = c.fetchall()
    if not clients:
        print("Mijozlar topilmadi.")
    for client in clients:
        print(client)

    conn.close()

if __name__ == "__main__":
    check_db()
