import sqlite3
from datetime import datetime
import pytz

DB_PATH = "bot_data.db"
UZ_TZ = pytz.timezone("Asia/Tashkent")

def check():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print(f"Hozirgi vaqt (Toshkent): {datetime.now(UZ_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.execute("SELECT datetime('now', '+5 hours')")
    db_now = c.fetchone()[0]
    print(f"Bazadagi 'hozirgi' vaqt (UTC+5): {db_now}")
    
    c.execute("SELECT id, client_name, client_phone, appointment_time, notified FROM clients WHERE notified = 0")
    rows = c.fetchall()
    
    if not rows:
        print("\nHabar yuborilishi kerak bo'lgan (notified=0) mijozlar topilmadi.")
    else:
        print(f"\nTopilgan mijozlar ({len(rows)} ta):")
        for r in rows:
            print(f"ID: {r[0]}, Ism: {r[1]}, Vaqt: {r[3]}, Notified: {r[4]}")
            if r[3] <= db_now:
                print(f"  -> BU MIJOZGA XABAR KETISHI KERAK!")
            else:
                print(f"  -> Vaqti hali kelmagan (Kutish kerak).")
    
    conn.close()

if __name__ == "__main__":
    check()
