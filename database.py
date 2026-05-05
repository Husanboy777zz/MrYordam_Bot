import sqlite3
import logging

logger = logging.getLogger(__name__)
DB_PATH = "bot_data.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id      INTEGER PRIMARY KEY,
        name         TEXT NOT NULL,
        shop_name    TEXT NOT NULL,
        phone        TEXT NOT NULL,
        msg_template TEXT DEFAULT 'navbatingiz keldi',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Mavjud bazaga ustun qo'shish (agar bo'lmasa)
    try:
        c.execute("ALTER TABLE users ADD COLUMN msg_template TEXT DEFAULT 'navbatingiz keldi'")
    except:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id         INTEGER NOT NULL,
        client_name      TEXT NOT NULL,
        client_phone     TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        notified         INTEGER DEFAULT 0,
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users(user_id)
    )''')

    conn.commit()
    conn.close()
    logger.info("Database initialized.")


def save_user(user_id, name, shop_name, phone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO users (user_id, name, shop_name, phone) VALUES (?,?,?,?)",
        (user_id, name, shop_name, phone)
    )
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, name, shop_name, phone, msg_template FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row  # (user_id, name, shop_name, phone, msg_template)


def update_shop_name(user_id, new_shop_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET shop_name=? WHERE user_id=?", (new_shop_name, user_id))
    conn.commit()
    conn.close()


def update_user_phone(user_id, new_phone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET phone=? WHERE user_id=?", (new_phone, user_id))
    conn.commit()
    conn.close()


def update_user_template(user_id, new_template):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET msg_template=? WHERE user_id=?", (new_template, user_id))
    conn.commit()
    conn.close()


def save_client(owner_id, client_name, client_phone, appointment_time_str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO clients (owner_id, client_name, client_phone, appointment_time) VALUES (?,?,?,?)",
        (owner_id, client_name, client_phone, appointment_time_str)
    )
    client_id = c.lastrowid
    conn.commit()
    conn.close()
    return client_id


def get_clients_for_owner(owner_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, client_name, client_phone, appointment_time, notified "
        "FROM clients WHERE owner_id=? ORDER BY appointment_time ASC",
        (owner_id,)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_pending_clients():
    """Returns clients whose appointment_time has arrived and not yet notified."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """SELECT cl.id, cl.client_name, cl.client_phone, cl.appointment_time,
                  u.name AS owner_name, u.shop_name, cl.owner_id, u.msg_template
           FROM clients cl
           JOIN users u ON cl.owner_id = u.user_id
           WHERE cl.notified = 0
             AND cl.appointment_time <= datetime('now', '+5 hours')""",
    )
    rows = c.fetchall()
    conn.close()
    return rows


def mark_notified(client_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE clients SET notified=1 WHERE id=?", (client_id,))
    conn.commit()
    conn.close()


def get_clients_history(owner_id, months=None):
    """Mijozlar tarixini ma'lum oylar soni bo'yicha qaytaradi. Months None bo'lsa hammasi."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if months:
        query = (
            "SELECT id, client_name, client_phone, appointment_time, notified, created_at "
            "FROM clients WHERE owner_id=? AND created_at >= datetime('now', ? || ' months') "
            "ORDER BY created_at DESC"
        )
        params = (owner_id, f"-{months}")
    else:
        query = (
            "SELECT id, client_name, client_phone, appointment_time, notified, created_at "
            "FROM clients WHERE owner_id=? ORDER BY created_at DESC"
        )
        params = (owner_id,)
        
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def delete_client(client_id, owner_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM clients WHERE id=? AND owner_id=?", (client_id, owner_id))
    conn.commit()
    conn.close()
