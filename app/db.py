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
        remaining_double_checker TEXT,

        drop_count INTEGER,

        abnormal_report TEXT,


        ok_count INTEGER,
        ng_count INTEGER,

        inner_d_ngcount1 INTEGER,
        inner_d_ngcount2 INTEGER,

        phi071_ngcount1 INTEGER,
        phi071_ngcount2 INTEGER,

        total_length_ngcount1 INTEGER,
        total_length_ngcount2 INTEGER,

        taper_thickness_ngcount1 INTEGER,
        taper_thickness_ngcount2 INTEGER,

        bottom_ngcount1 INTEGER,
        bottom_ngcount2 INTEGER,

        thickness_ngcount1 INTEGER,
        thickness_ngcount2 INTEGER,

        side_visual_ngcount1 INTEGER,
        side_visual_ngcount2 INTEGER,

        st6_ngcount1 INTEGER,
        st6_ngcount2 INTEGER,

        st1_alarm_count INTEGER,
        st2_alarm_count INTEGER,
        st3_alarm_count INTEGER,
        st4_alarm_count INTEGER,
        st5_alarm_count INTEGER,
        st6_alarm_count INTEGER,
        st7_alarm_count INTEGER,
        st8_alarm_count INTEGER,
        others_alarm_count INTEGER

    );
    """

    with sqlite3.connect(DB_FILE) as conn:

        conn.execute(sql)

        conn.commit()


def insert_record(data: dict):

    columns = ", ".join(data.keys())

    placeholders = ", ".join(
        f":{key}"
        for key in data.keys()
    )

    sql = f"""
    INSERT INTO inspection_data (
        {columns}
    )
    VALUES (
        {placeholders}
    )
    """

    with sqlite3.connect(DB_FILE) as conn:

        conn.execute(sql, data)

        conn.commit()



if __name__ == "__main__":
    init_db()
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
        "remaining_double_checker": "神野",

        "drop_count": 0,

        "abnormal_report": "",

        # 集計
        "ok_count": 997,
        "ng_count": 3,

        # NG内訳
        "inner_d_ngcount1": 1,
        "inner_d_ngcount2": 0,

        "phi071_ngcount1": 0,
        "phi071_ngcount2": 1,

        "total_length_ngcount1": 0,
        "total_length_ngcount2": 0,

        "taper_thickness_ngcount1": 1,
        "taper_thickness_ngcount2": 0,

        "bottom_ngcount1": 0,
        "bottom_ngcount2": 0,

        "thickness_ngcount1": 0,
        "thickness_ngcount2": 0,

        "side_visual_ngcount1": 0,
        "side_visual_ngcount2": 0,

        "st6_ngcount1": 0,
        "st6_ngcount2": 0,

        # アラーム回数
        "st1_alarm_count": 0,
        "st2_alarm_count": 1,
        "st3_alarm_count": 0,
        "st4_alarm_count": 0,
        "st5_alarm_count": 2,
        "st6_alarm_count": 0,
        "st7_alarm_count": 0,
        "st8_alarm_count": 0,

        "others_alarm_count": 0,
    }

    insert_record(sample_data)
    print("データ追加しました")
