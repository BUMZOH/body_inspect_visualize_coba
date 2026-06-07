import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE = DATA_DIR / "body_inspection_machine.db"


def init_db():

    sql = """
    CREATE TABLE IF NOT EXISTS inspection_data (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        inspection_machine_no INTEGER,
        record_date TEXT,
        shift_name TEXT,

        part_no TEXT,
        nc_process_date TEXT,
        nc_machine_no INTEGER,
        monthly_serial_no INTEGER,

        inspection_start_time TEXT,
        inspection_end_time TEXT,

        change_point_record TEXT,
        camera_threshold TEXT,

        worker_name TEXT,

        appearance_check TEXT,
        appearance_checker TEXT,

        setup_check TEXT,

        remaining_checker TEXT,
        camera_5st_checker TEXT,

        drop_count INTEGER,

        abnormal_report TEXT

    );
    """

    with sqlite3.connect(DB_FILE) as conn:

        conn.execute(sql)

        conn.commit()


def insert_inspection_data(data):

    sql = """
    INSERT INTO inspection_data (

        inspection_machine_no,
        record_date,
        shift_name,

        part_no,
        nc_process_date,
        nc_machine_no,
        monthly_serial_no,

        inspection_start_time,
        inspection_end_time,

        change_point_record,
        camera_threshold,

        worker_name,

        appearance_check,
        appearance_checker,

        setup_check,

        remaining_checker,
        camera_5st_checker,

        drop_count,

        abnormal_report

    )
    VALUES (

        :inspection_machine_no,
        :record_date,
        :shift_name,

        :part_no,
        :nc_process_date,
        :nc_machine_no,
        :monthly_serial_no,

        :inspection_start_time,
        :inspection_end_time,

        :change_point_record,
        :camera_threshold,

        :worker_name,

        :appearance_check,
        :appearance_checker,

        :setup_check,

        :remaining_checker,
        :camera_5st_checker,

        :drop_count,

        :abnormal_report

    )
    """

    with sqlite3.connect(DB_FILE) as conn:

        conn.execute(
            sql,
            data
        )

        conn.commit()


if __name__ == "__main__":
    sample_data = {
        "inspection_machine_no": 1,
        "record_date": "2026-06-07", 
        "shift_name": "昼勤", 
        "part_no": "ABC-123", 
        "nc_process_date": "2026-06-07", 
        "nc_machine_no": 5, 
        "monthly_serial_no": 1001, 
        "inspection_start_time": "2026-06-07 08:00:00", 
        "inspection_end_time": "2026-06-07 08:15:00", 
        "change_point_record": "なし", 
        "camera_threshold": "80", 
        "worker_name": "田中", 
        "appearance_check": "良", 
        "appearance_checker": "鈴木", 
        "setup_check": "OK", 
        "remaining_checker": "佐藤", 
        "camera_5st_checker": "高橋", 
        "drop_count": 0, 
        "abnormal_report": ""
    }

    insert_inspection_data(sample_data)
    print("データ追加しました")
