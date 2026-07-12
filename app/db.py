import sqlite3
from pathlib import Path
from datetime import datetime

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

        level_gap_ngcount1 INTEGER,
        level_gap_ngcount2 INTEGER,
        
        bottom_ngcount1 INTEGER,
        bottom_ngcount2 INTEGER,

        thickness_ngcount1 INTEGER,
        thickness_ngcount2 INTEGER,

        side_visual1_ngcount1 INTEGER,
        side_visual1_ngcount2 INTEGER,

        side_visual2_ngcount1 INTEGER,
        side_visual2_ngcount2 INTEGER,

        phi2435_depth_ngcount1 INTEGER,
        phi2435_depth_ngcount2 INTEGER,

        phi14_depth_ngcount1 INTEGER,
        phi14_depth_ngcount2 INTEGER,

        
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


def get_monthly_serial_no(
        inspection_machine_no: int | str,
        record_date: str
) -> int:
    """
    指定した検査機・記録年月に対する次の月別通しNoを返す。

    同じ検査機・同じ年月のデータが存在しない場合は1を返す。
    """
    machine_no = int(inspection_machine_no)

    try:
        record_dt = datetime.strptime(record_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            "記録日はYYYY-MM-DD形式で指定してください"
        ) from e

    target_year_month = record_dt.strftime("%Y-%m")

    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute(
            """
            SELECT MAX(monthly_serial_no)
            FROM inspection_data
            WHERE inspection_machine_no = ?
              AND substr(record_date, 1, 7) = ?
            """,
            (machine_no, target_year_month),
        ).fetchone()

    current_max_no = row[0]

    if current_max_no is None:
        return 1
    
    return int(current_max_no) + 1




if __name__ == "__main__":

    print( get_monthly_serial_no(555, '2026-07-01'))
    exit()

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
        "ng_count": 33,

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

        "level_gap_ngcount1": 10,
        "level_gap_ngcount2": 15,

        "side_visual1_ngcount1": 0,
        "side_visual1_ngcount2": 0,

        "side_visual2_ngcount1": 0,
        "side_visual2_ngcount2": 0,

        "phi2435_depth_ngcount1": 0,
        "phi2435_depth_ngcount2": 0,

        "phi14_depth_ngcount1": 5,
        "phi14_depth_ngcount2": 6,

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
