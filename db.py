
import sqlite3
from pathlib import Path

# Always store database in the project folder
DB_PATH = Path(__file__).resolve().parent / "expenses.db"

def connect_db():
    return sqlite3.connect(DB_PATH)


def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def add_transaction(transaction_type, amount, description, category, date):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (type, amount, description, category, date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        transaction_type,
        amount,
        description,
        category,
        str(date)
    ))

    conn.commit()
    conn.close()


def get_transactions():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, amount, description, category, date
        FROM transactions
        ORDER BY date DESC, id DESC
    """)

    data = cursor.fetchall()
    conn.close()

    return data


# ==========================================
# UPDATE TRANSACTION
# ==========================================

def update_transaction(transaction_id, transaction_type,
                       amount, description, category, date):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE transactions
        SET type = ?,
            amount = ?,
            description = ?,
            category = ?,
            date = ?
        WHERE id = ?
    """, (
        transaction_type,
        amount,
        description,
        category,
        date,
        transaction_id
    ))

    conn.commit()
    conn.close()


# ==========================================
# DELETE TRANSACTION
# ==========================================

def delete_transaction(transaction_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    conn.commit()
    conn.close()
