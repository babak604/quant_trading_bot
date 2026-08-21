import sqlite3
from datetime import datetime

class PerformanceTracker:
    def __init__(self, db_path="markov_1.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    coin TEXT,
                    price REAL,
                    ofi REAL,
                    regime TEXT,
                    win_prob REAL,
                    tail_risk REAL,
                    signal TEXT,
                    pos_size_usd REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    coin TEXT,
                    size_units REAL,
                    price REAL,
                    status TEXT
                )
            """)
            conn.commit()

    def log_signal(self, coin, price, ofi, regime, win_prob, tail_risk, signal, pos_size_usd):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trading_signals 
                (timestamp, coin, price, ofi, regime, win_prob, tail_risk, signal, pos_size_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.utcnow().isoformat(), coin, price, ofi, regime, win_prob, tail_risk, signal, pos_size_usd))
            conn.commit()

    def log_order(self, coin, size_units, price, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO order_history (timestamp, coin, size_units, price, status)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.utcnow().isoformat(), coin, size_units, price, status))
            conn.commit()
