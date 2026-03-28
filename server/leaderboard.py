"""SQLite-backed leaderboard for winners and challenge progress."""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data_server.db")


class Leaderboard:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                name TEXT PRIMARY KEY,
                net_profit INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                games_played INTEGER NOT NULL,
                best_streak INTEGER NOT NULL
            )
            """
        )

        # Migrate legacy schema used by earlier builds.
        c.execute("PRAGMA table_info(scores)")
        cols = {row[1] for row in c.fetchall()}

        if "net_profit" not in cols:
            c.execute("ALTER TABLE scores ADD COLUMN net_profit INTEGER NOT NULL DEFAULT 0")
            # If legacy max_score exists, use it as initial net_profit.
            if "max_score" in cols:
                c.execute("UPDATE scores SET net_profit = COALESCE(max_score, 0)")

        if "wins" not in cols:
            c.execute("ALTER TABLE scores ADD COLUMN wins INTEGER NOT NULL DEFAULT 0")

        if "games_played" not in cols:
            c.execute("ALTER TABLE scores ADD COLUMN games_played INTEGER NOT NULL DEFAULT 0")

        if "best_streak" not in cols:
            c.execute("ALTER TABLE scores ADD COLUMN best_streak INTEGER NOT NULL DEFAULT 0")

        conn.commit()
        conn.close()

    def record_result(self, name: str, delta: int, won: bool):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT net_profit, wins, games_played, best_streak FROM scores WHERE name=?", (name,))
        row = c.fetchone()

        if row:
            net_profit, wins, games_played, best_streak = row
            wins = wins + (1 if won else 0)
            c.execute(
                "UPDATE scores SET net_profit=?, wins=?, games_played=?, best_streak=? WHERE name=?",
                (net_profit + delta, wins, games_played + 1, best_streak, name),
            )
        else:
            c.execute(
                "INSERT INTO scores (name, net_profit, wins, games_played, best_streak) VALUES (?, ?, ?, ?, ?)",
                (name, delta, 1 if won else 0, 1, 1 if won else 0),
            )

        conn.commit()
        conn.close()

    def get_top_10(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(
                "SELECT name, net_profit, wins, games_played FROM scores ORDER BY net_profit DESC, wins DESC LIMIT 10"
            )
            rows = c.fetchall()
        except sqlite3.OperationalError:
            # If schema drift still appears at runtime, re-run migration and retry once.
            conn.close()
            self._init_db()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "SELECT name, net_profit, wins, games_played FROM scores ORDER BY net_profit DESC, wins DESC LIMIT 10"
            )
            rows = c.fetchall()
        conn.close()
        return [
            {
                "name": r[0],
                "score": r[1],
                "wins": r[2],
                "games": r[3],
            }
            for r in rows
        ]
