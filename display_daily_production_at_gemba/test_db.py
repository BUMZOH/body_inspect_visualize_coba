
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "data"
DB_FILE = BASE_DIR.parent / "data" / "body_insp_production_data.db"


def create_table():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS production_result (
                machine_no INTEGER NOT NULL,
                date_hour TEXT NOT NULL,
                operating_time_sec INTEGER NOT NULL
                    CHECK (operating_time_sec BETWEEN 0 AND 3600),
                production_num_1hour INTEGER NOT NULL
                    CHECK (production_num_1hour >= 0),
                PRIMARY KEY (machine_no, date_hour)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS production_goal (
                date TEXT PRIMARY KEY NOT NULL,
                production_goal INTEGER NOT NULL
                    CHECK (production_goal >= 0)
            )
            """
        )


def create_sample_data():
    machine_numbers = [412, 413, 416, 421, 428]
    start = datetime(2026, 10, 1)
    hours = 60 * 24

    records = []
    for machine_no in machine_numbers:
        for hour in range(hours):
            date_hour = (start + timedelta(hours=hour)).strftime(
                "%Y-%m-%d %H:%M"
            )
            records.append(
                (
                    machine_no,
                    date_hour,
                    random.randint(0, 3600),
                    random.randint(0, 2000),
                )
            )

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM production_result")
        conn.executemany(
            """
            INSERT INTO production_result (
                machine_no, date_hour, operating_time_sec, production_num_1hour
            ) VALUES (?, ?, ?, ?)
            """,
            records,
        )

    print(f"Sample data created: {len(records)} records")


def create_sample_goal():
    start = datetime(2026, 10, 1)
    records = []

    for day in range(60):
        date = (start + timedelta(days=day)).strftime("%Y-%m-%d")
        goal = random.randrange(50000, 150001, 5000)
        records.append((date, goal))

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM production_goal")
        conn.executemany(
            """
            INSERT INTO production_goal (date, production_goal)
            VALUES (?, ?)
            """,
            records,
        )

    print(f"Sample goals created: {len(records)} records")


if __name__ == "__main__":
    create_table()
    create_sample_data()
    create_sample_goal()
    print(f"Database ready: {DB_FILE}")

