from datetime import datetime
from pathlib import Path
import json
#　独自モジュール
from db import insert_record


# CONSTANTS -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STAFF_FILE = BASE_DIR / "staff.json"

# FOR VALIDATION ----
INTEGER_COLUMNS = {
    "inspection_machine_no",
    "nc_machine_no",
    "monthly_serial_no",
    "drop_count",

    "ok_count",
    "ng_count",

    "inner_d_ngcount1",
    "inner_d_ngcount2",
    "phi071_ngcount1",
    "phi071_ngcount2",
    "total_length_ngcount1",
    "total_length_ngcount2",
    "taper_thickness_ngcount1",
    "taper_thickness_ngcount2",
    "bottom_ngcount1",
    "bottom_ngcount2",
    "thickness_ngcount1",
    "thickness_ngcount2",
    "side_visual_ngcount1",
    "side_visual_ngcount2",
    "st6_ngcount1",
    "st6_ngcount2",

    "st1_alarm_count",
    "st2_alarm_count",
    "st3_alarm_count",
    "st4_alarm_count",
    "st5_alarm_count",
    "st6_alarm_count",
    "st7_alarm_count",
    "st8_alarm_count",
    "others_alarm_count",
}

DATETIME_COLUMNS = {
    "inspection_start_time",
    "inspection_end_time",
}

REQUIRED_COLUMNS = {
    "inspection_machine_no": "検査機番",
    "record_date": "記録日",
    "shift_name": "シフト",
    "part_no": "品番",
    "worker_name": "担当者",
    "inspection_start_time": "検査開始時間",
    "inspection_end_time": "検査終了時間",
}

# GLOBAL VARIABLES --------------------------------------------------
staff = {}

# FUNCTIONS ---------------------------------------------------------
def load_staff_info():
    global staff

    if not STAFF_FILE.exists():
        print("staff.jsonが見つかりません")
        return

    with STAFF_FILE.open(mode='r', encoding='UTF-8') as f:
        staff = json.load(f)


def convert_empty_to_none(value):
    if value =="":
        return None
    
    return value


def validate_required(data: dict) -> list[str]:
    errors = []

    for column, label in REQUIRED_COLUMNS.items():
        print(f"{column} : {data.get(column)}")
        if not data.get(column):
            errors.append(f"{label}が未入力です")
    
    return errors


def convert_datetime(value):
    """
    HTMLの入力フォームは日付と時間の間に"T"が入る
    入力フォームは分単位なので秒を補完する    
    """
    if not value:
        return None
    
    value = value.replace("T"," ")

    if len(value) == 16:
        value += ":00"

    return value


def normalize_record(data: dict) -> tuple[dict, list[str]]:
    errors = validate_required(data)
    record = {}

    for key, value in data.items():
        value = convert_empty_to_none(value)

        if key in INTEGER_COLUMNS:
            try:
                # Noneなら0、None以外ならint変換
                record[key] = int(value) if value is not None else 0
            except ValueError:
                errors.append(f"{key}は数値で入力してください")
                record[key] = 0

        elif key in DATETIME_COLUMNS:
            record[key] = convert_datetime(value)

        else:
            record[key] = value

    return record, errors




class AppAPI:
    def __init__(self) -> None:
        # 機械番号はPLC通信で「記録待ち」になっている設備をサーチする
        self.inspection_machine_no = "552"  # DummyData

        # 検査開始時間はPLCのデバイスから取得する
        self.inspection_start_time = datetime.now() # テスト用としてアプリ起動時間

    def get_default_values(self) -> dict[str, str]:
        """画面のデフォルト値を返す。"""
        now = datetime.now()

        # 昼勤/夜勤 自動判断
        if 8 <= now.hour and now.hour < 20:
            shift_name = "昼勤"
        else:
            shift_name = "夜勤"

        # idに対するデフォルト値を渡す(辞書型)
        return {
            "inspection_machine_no": self.inspection_machine_no,
            "record_date": now.strftime("%Y-%m-%d"),
            "shift_name": shift_name,
            "inspection_start_time": self.inspection_start_time.strftime("%Y-%m-%d %H:%M"),
            "inspection_end_time": now.strftime("%Y-%m-%d %H:%M"),
            "change_point_record": "社内"
        }
    
    def convert_barcode(self, barcode_text: str) -> dict[str, str]:
        """バーコードで読み取った従業員番号を氏名に変換"""
        barcode_text = barcode_text.strip()
        staff_name = staff.get(barcode_text, "不明")
        return{
            "barcode_text": barcode_text,
            "staff_name": staff_name
        }
    
    
    def get_table_data(self):
        # 現段階は仮プログラム（固定データ）→ PLCから読み取る
        return {

            "ok_count": 120,
            "ng_count": 8,

            "inner_d_ngcount1": 1,
            "phi071_ngcount1": 0,
            "total_length_ngcount1": 2,
            "taper_thickness_ngcount1": 0,
            "bottom_ngcount1": 1,
            "thickness_ngcount1": 0,
            "side_visual_ngcount1": 0,
            "st6_ngcount1": 4,

            "inner_d_ngcount2": 0,
            "phi071_ngcount2": 0,
            "total_length_ngcount2": 1,
            "taper_thickness_ngcount2": 0,
            "bottom_ngcount2": 0,
            "thickness_ngcount2": 0,
            "side_visual_ngcount2": 0,
            "st6_ngcount2": 0,

            "st1_alarm_count": 0,
            "st2_alarm_count": 1,
            "st3_alarm_count": 0,
            "st4_alarm_count": 2,
            "st5_alarm_count": 3,
            "st6_alarm_count": 0,
            "st7_alarm_count": 0,
            "st8_alarm_count": 1,
            "others_alarm_count": 22,
        }


    def register_data(self,data: dict):
        try:
            record, errors = normalize_record(data)

            if errors:
                return {
                    "ok": False,
                    "message":"\n".join(errors),
                }
            
            insert_record(record)

            return {
                "ok": True,
                "message": "データ登録しました",
            }

        except Exception as e:
            return {
                "ok": False,
                "message": str(e),
            }