from datetime import datetime
from pathlib import Path
import json
#　独自モジュール
from db import insert_record, DB_FILE
from common_lib_mw import kv_com, kv_alarm_history


# CONSTANTS -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STAFF_FILE = BASE_DIR / "staff.json"
CONFIG_FILE = BASE_DIR / "config.json"


# FOR VALIDATION ----
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
config = {}

# FUNCTIONS ---------------------------------------------------------
def load_staff_info():
    global staff

    if not STAFF_FILE.exists():
        print("staff.jsonが見つかりません")
        return

    with STAFF_FILE.open(mode='r', encoding='UTF-8') as f:
        staff = json.load(f)


def load_config():
    global config

    if not CONFIG_FILE.exists():
        print("config.jsonが見つかりません")
        return

    with CONFIG_FILE.open(mode='r', encoding='UTF-8') as f:
        config = json.load(f)


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


def get_integer_columns() -> set[str]:
    # (辞書データの結合に注意)
    return (
        {
            "inspection_machine_no",
            "nc_machine_no",
            "monthly_serial_no",
            "drop_count",
        }
        | set(config["plc_count_devices"].keys())
        | {
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
    )


def normalize_record(data: dict) -> tuple[dict, list[str]]:
    errors = validate_required(data)
    record = {}
    integer_columns = get_integer_columns()


    for key, value in data.items():
        value = convert_empty_to_none(value)

        if key in integer_columns:
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


def get_inspection_start_time(machine_no: str):
    """ PLCから検査開始時間を取得 """
    plc_ip_address = config["machines"][machine_no]["plc_ip_address"]
    
    year = int(kv_com.read_device_u(plc_ip_address, "EM10000"))
    month = int(kv_com.read_device_u(plc_ip_address, "EM10001"))
    day = int(kv_com.read_device_u(plc_ip_address, "EM10002"))
    hour = int(kv_com.read_device_u(plc_ip_address, "EM10003"))
    minute = int(kv_com.read_device_u(plc_ip_address, "EM10004"))

    dt = datetime(year, month, day, hour, minute)
    print(dt.strftime("%Y-%m-%d %H-%M"))

    return dt.strftime("%Y-%m-%d %H:%M")


def search_record_waiting_machine() -> list[str]:
    """「記録待ち(EM10011=ON)」になっている機械を探す
        該当なし:   空のリスト
        複数台該当: 要素2個以上のリスト
        ※正常時は要素数1個のリスト
    """
    # (以下作成予定)
    
    return ["555"]


def debug_dump(data):
    """JSONデータ結果確認用"""
    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=4,
        )
    )


#---- API CLASS -----------------------------------------------------
class AppAPI:
    def __init__(self) -> None:
        load_staff_info()   # 従業員番号-氏名 対応表読み込み
        load_config()       # 設備関連情報読み込み


    def get_default_values(self) -> dict[str, str]:
        """画面のデフォルト値を返す。"""

        # 「記録待ち(EM10011=ON)」になっている機械を探す ※※※(以下ダミー関数)
        # (戻り値が空/複数個の場合を考えること)
        inspection_machine_no = search_record_waiting_machine()[0]

        now = datetime.now()
        # 昼勤/夜勤 自動判断
        if 8 <= now.hour and now.hour < 20:
            shift_name = "昼勤"
        else:
            shift_name = "夜勤"

        # idに対するデフォルト値を渡す(辞書型)
        return {
            "inspection_machine_no": inspection_machine_no,
            "record_date": now.strftime("%Y-%m-%d"),
            "shift_name": shift_name,
            "inspection_start_time": get_inspection_start_time(inspection_machine_no),
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
    
    
    def get_table_data(
        self,
        inspection_machine_no: str,
        inspection_start_time: str,
        inspection_end_time: str
    ) -> dict:
        """PLCの検査数・不良数・アラーム件数を取得する。"""
        machine_no = int(inspection_machine_no)

        if not inspection_start_time or not inspection_end_time:
            raise ValueError("検査開始時間または検査終了時間が未入力です")
        
        # datetime-localの値をSQLite保存形式へ合わせる。
        start_datetime = inspection_start_time.replace("T", " ")
        end_datetime = inspection_end_time.replace("T", " ")

        # 秒(:00)の補完
        if len(start_datetime) == 16:
            start_datetime += ":00"
        if len(end_datetime) == 16:
            end_datetime += ":00"

        machine_config = config["machines"].get(str(machine_no))
        if machine_config is None:
            raise ValueError(
                f"設備番号{machine_no}の設定がconfig.jsonにありません"
            )

        ip_address = machine_config["plc_ip_address"]
        table_data = {}

        # PLCカウント用デバイスの値受信
        for key, device in config["plc_count_devices"].items():
            res = kv_com.read_device_d(ip_address, device)
            table_data[key] = int(res)

        # PLC履歴をDBへ保存した後、指定期間の履歴を取得して集計する。
        kv_alarm_history.collect_alarm_history(
            ip_add=ip_address,
            machine_no=machine_no,
            db_path=DB_FILE
        )

        alarm_history = kv_alarm_history.get_alarm_history(
            machine_no=machine_no,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            db_path=DB_FILE
        )

        alarm_keywords = [
            "1ST",
            "2ST",
            "3ST",
            "4ST",
            "5ST",
            "6ST",
            "7ST",
            "8ST",
        ]
        keyword_counts = kv_alarm_history.count_alarm_keywords(
            alarm_history=alarm_history,
            keywords=alarm_keywords
        )

        alarm_count_data = {
            f"st{station_no}_alarm_count": keyword_counts[f"{station_no}ST"]
            for station_no in range(1,9)
        }
        alarm_count_data["others_alarm_count"] = (
            len(alarm_history) - sum(keyword_counts.values())
        )

        table_data |= alarm_count_data  # データ結合
        debug_dump(table_data)  # debug

        return table_data


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