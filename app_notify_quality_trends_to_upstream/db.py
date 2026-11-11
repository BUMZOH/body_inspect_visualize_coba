"""Create the SQLite database and measurement_result table."""

import sqlite3
from pathlib import Path


# ================================================
# Settings
# ================================================
DB_FILE = Path(__file__).resolve().parent.parent / "data" / "body_insp_measurement_data.db"


# ================================================
# Database
# ================================================
def create_table():
    """Create the database and table if they do not exist."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurement_result (
                insp_machine_no INTEGER NOT NULL,
                inspection_item TEXT NOT NULL,
                measured_at TEXT NOT NULL,
                part_no TEXT,
                proc_machine_no INTEGER,
                process_date TEXT,
                measured_value REAL,
                judgment TEXT,
                upper_limit REAL,
                lower_limit REAL,
                PRIMARY KEY (insp_machine_no, inspection_item, measured_at)
            )
            """
        )

    print(f"DB ready: {DB_FILE}")
    print("Table ready: measurement_result")


# ================================================
# Main
# ================================================
def main():
    create_table()


if __name__ == "__main__":
    main()
