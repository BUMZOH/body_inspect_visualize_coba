from datetime import datetime, timedelta
from pathlib import Path
import csv
import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed


# 独自モジュール
import db
from common_lib_mw import kv_com, kv_alarm_history


# CONSTANTS -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STAFF_FILE = BASE_DIR / "staff.json"
CONFIG_FILE = BASE_DIR / "config.json"
PART_NO_FILE = BASE_DIR / "part_no.json"
DATA_DEFINITION_FILE = BASE_DIR / "data_definition.json"


# GLOBAL VARIABLES --------------------------------------------------
staff = {}
config = {}
part_no_table = {}
data_definitions = {}


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


def load_part_no_table():
    global part_no_table

    if not PART_NO_FILE.exists():
        print("part_no.jsonが見つかりません")
        return
    
    with PART_NO_FILE.open(mode="r", encoding="UTF-8") as file:
        part_no_table = json.load(file)


def load_data_definitions():
    global data_definitions

    if not DATA_DEFINITION_FILE.exists():
        print("data_definitionが見つかりません")
        return

    with DATA_DEFINITION_FILE.open(mode="r", encoding="UTF-8") as file:
        data_definitions = json.load(file)


def is_empty_value(value) -> bool:
    """
    値が未入力か確認する。

    未入力とする値:
    - None
    - 空文字
    - 空白だけの文字列

    数値の0は未入力としない。
    """
    if value is None:
        return True

    # value が文字列だった場合、空文字かどうかを判定する
    if isinstance(value, str):
        return value.strip() == ""

    return False


def convert_empty_to_none(value):
    """
    空欄をNoneへ変換する。
    """
    if is_empty_value(value):
        return None
    
    return value


def get_required_columns() -> dict[str, str]:
    """
    必須入力カラムと日本語表示名を取得する。

    Returns:
        dict[str, str]:
            キー: DBカラム名
            値: エラー表示用の日本語名
    """
    return {
        column: definition.get("japanese", column)
        for column, definition in data_definitions.items()
        if definition.get("required", False)
    }


def validate_required(data: dict) -> list[str]:
    """
    data_definition.jsonでrequiredがtrueの項目を確認する。
    """
    errors = []
    required_columns = get_required_columns()

    for column, label in required_columns.items():
        value = data.get(column)

        if is_empty_value(value):
            errors.append(f"{label}が未入力です")
    
    return errors


def validate_data_type(
        value,
        data_type: str,
        label: str,
) -> str | None:
    """
    data_definition.jsonのtypeに従って、
    入力値のデータ型を確認する。

    正常な場合: None
    異常な場合: エラーメッセージ
    """
    if is_empty_value(value):
        return None

    if data_type == "INTEGER":
        try:
            int(value)
        except (TypeError, ValueError):
            return f"{label}は整数で入力してください"

    elif data_type == "TEXT":
        if not isinstance(value, str):
            return f"{label}は文字列で入力してください"

    else:
        return (
            f"{label}に未対応のデータ型"
            f"「{data_type}」が設定されています"
        )

    return None


def validate_record_types(data: dict) -> list[str]:
    """
    data_definition.jsonのtypeに従って、
    登録データ全体の型を確認する。
    """
    errors = []

    for column, definition in data_definitions.items():
        value = data.get(column)
        data_type = definition.get("type")
        label = definition.get("japanese", column)

        if data_type is None:
            continue

        error = validate_data_type(
            value=value,
            data_type=data_type,
            label=label,
        )

        if error:
            errors.append(error)

    return errors


def validate_format(
        value,
        format_name: str,
        label: str,
) -> str | None:
    """
    data_definition.jsonのformatに従って、
    日付や日時の形式を確認する。

    正常な場合: None
    異常な場合: エラーメッセージ
    """ 
    if is_empty_value(value):
        return None

    if not isinstance(value, str):
        return f"{label}の形式が正しくありません"

    if format_name == "date":
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return f"{label}はYYYY-MM-DD形式で入力してください"

    elif format_name == "datetime":
        normalized_value = value.replace("T", " ")

        datetime_formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
        ]

        for datetime_format in datetime_formats:
            try:
                datetime.strptime(
                    normalized_value,
                    datetime_format,
                )
                return None

            except ValueError:
                continue

        return (f"{label}はYYYY-MM-DD HH:MM形式で入力してください")

    else:
        return(f"{label}に未対応の形式「{format_name}」が設定されています")

    return None


def validate_record_formats(data: dict) -> list[str]:
    """
    data_definition.jsonのformatに従って、
    登録データ全体の形式を確認する。
    """
    errors = []

    for column, definition in data_definitions.items():
        format_name = definition.get("format")

        if format_name is None:
            continue

        value = data.get(column)
        label = definition.get("japanese", column)

        error = validate_format(
            value=value,
            format_name=format_name,
            label=label,
        )

        if error:
            errors.append(error)

    return errors


def validate_reference(
        value,
        reference_name: str,
        label: str,
) -> str | None:
    """
    data_definition.jsonのreferenceに従って、
    マスタに存在する値か確認する。
    """
    if is_empty_value(value):
        return None

    if reference_name == "staff":
        if value not in staff.values():
            return f"{label}がマスタに存在しません"

    elif reference_name == "part_no":
        if value not in part_no_table.values():
            return f"{label}がマスタに存在しません"

    else:
        return (
            f"{label}に未対応の参照先"
            f"「{reference_name}」が設定されています"
        )

    return None


def validate_record_references(data: dict) -> list[str]:
    """
    data_definition.jsonのreferenceに従って、
    登録データ全体の参照チェックを行う。
    """
    errors = []

    for column, definition in data_definitions.items():
        reference_name = definition.get("reference")

        if reference_name is None:
            continue

        value = data.get(column)
        label = definition.get("japanese", column)

        error = validate_reference(
            value=value,
            reference_name=reference_name,
            label=label,
        )

        if error:
            errors.append(error)

    return errors


def get_datetime_columns() -> set[str]:
    """
    datetime形式として変換するカラム名を取得する。
    """
    return {
        column
        for column, definition in data_definitions.items()
        if definition.get("format") == "datetime"
    }


def convert_datetime(value):
    """
    HTMLの入力フォームは日付と時間の間に"T"が入る
    入力フォームは分単位なので秒を補完する    
    """
    if not value:
        return None
    
    value = value.replace("T", " ")

    if len(value) == 16:
        value += ":00"

    return value


def get_integer_columns() -> set[str]:
    """
    INTEGER型として定義されているカラム名を取得する。
    """
    return {
        column
        for column, definition in data_definitions.items()
        if definition.get("type") == "INTEGER"
    }


def normalize_record(data: dict) -> tuple[dict, list[str]]:
    errors = validate_required(data)
    errors.extend(validate_record_types(data))
    errors.extend(validate_record_formats(data))
    errors.extend(validate_record_references(data))

    record = {}

    integer_columns = get_integer_columns()
    datetime_columns = get_datetime_columns()


    for key, value in data.items():
        value = convert_empty_to_none(value)

        if key in integer_columns:
            try:
                # Noneなら0、None以外ならint変換
                record[key] = int(value) if value is not None else 0
            except (TypeError, ValueError):
                record[key] = 0

        elif key in datetime_columns:
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
    # print(dt.strftime("%Y-%m-%d %H:%M"))

    return dt.strftime("%Y-%m-%d %H:%M")


def get_part_no(machine_no: str) -> str:
    """PLCのEM10012から品番識別値を取得し、対応する品番を返す。"""

    plc_ip_address = config["machines"][machine_no]["plc_ip_address"]

    part_no_value = int(kv_com.read_device_u(plc_ip_address, "EM10012"))

    return part_no_table.get(str(part_no_value), "unknown")


def check_record_waiting_machine(
        machine_no: str,
        machine_config: dict
) -> tuple[str, bool, bool]:
    """
    1台の設備について、記録待ち状態を確認する。

    Returns:
        tuple[str, bool, bool]:
            machine_no:
                設備番号

            is_record_waiting:
                EM10011がONならTrue

            has_communication_error:
                PLC通信に失敗した場合はTrue
    """
    plc_ip_address = machine_config["plc_ip_address"]

    try:
        record_waiting = int(
            kv_com.read_device_u(plc_ip_address, "EM10011")
        )

        return machine_no, record_waiting == 1, False
    
    except Exception as error:
        print(
            f"設備番号{machine_no}のPLC通信に失敗しました。"
            f" IPアドレス: {plc_ip_address}"
        )
        print(error)

        return machine_no, False, True


def search_record_waiting_machine() -> dict[str, list[str]]:
    """
    全設備を並列で確認し、記録待ち設備と通信失敗設備を返す

    Returns:
        dict[str, list[str]]:
            record_waiting_machines:
                EM10011がONになっている設備番号

            communication_error_machines:
                PLC通信に失敗した設備番号
    """
    record_waiting_machines = []
    communication_error_machines = []

    machines = config["machines"]

    with ThreadPoolExecutor(
        max_workers=min(len(machines), 10)
    ) as executor:
        
        futures = [
            executor.submit(
                check_record_waiting_machine,
                machine_no,
                machine_config,
            )
            for machine_no, machine_config in machines.items()
        ]

        for future in as_completed(futures):
            machine_no, is_record_waiting, has_communication_error = (
                future.result()
            )

            if has_communication_error:
                communication_error_machines.append(machine_no)
                continue

            if is_record_waiting:
                record_waiting_machines.append(machine_no)

    return {
        "record_waiting_machines": sorted(record_waiting_machines),
        "communication_error_machines": sorted(communication_error_machines),
    }


def get_column_label(column: str) -> str:
    definition = data_definitions.get(column, {})
    return definition.get("japanese", column)


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
        load_staff_info()       # 従業員番号-氏名 対応表読み込み
        load_config()           # 設備関連情報読み込み
        load_part_no_table()    # 品番対応表読み込み
        load_data_definitions() # データ定義読み込み


    def get_default_values(
        self,
        inspection_machine_no: str
    ) -> dict[str, str | int]:
        """指定された設備の画面デフォルト値を返す。"""

        if inspection_machine_no not in config["machines"]:
            raise ValueError(
                f"設備番号{inspection_machine_no}の設定が"
                "config.jsonにありません"
            )

        now = datetime.now()
        record_date = now.strftime("%Y-%m-%d")

        # 昼勤/夜勤 自動判断
        if 8 <= now.hour < 20:
            shift_name = "昼勤"
        else:
            shift_name = "夜勤"

        monthly_serial_no = db.get_monthly_serial_no(inspection_machine_no, record_date)

        # idに対するデフォルト値を渡す(辞書型)
        return {
            "inspection_machine_no": inspection_machine_no,
            "record_date": record_date,
            "shift_name": shift_name,
            "part_no": get_part_no(inspection_machine_no),
            "monthly_serial_no": monthly_serial_no,
            "inspection_start_time": get_inspection_start_time(inspection_machine_no),
            "inspection_end_time": now.strftime("%Y-%m-%d %H:%M"),
            "change_point_record": "社内"
        }
    

    def convert_barcode(self, barcode_text: str) -> dict[str, str]:
        """バーコードで読み取った従業員番号を氏名に変換"""
        barcode_text = barcode_text.strip()
        staff_name = staff.get(barcode_text, "不明")
        return {
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
            db_path=db.DB_FILE
        )

        alarm_history = kv_alarm_history.get_alarm_history(
            machine_no=machine_no,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            db_path=db.DB_FILE
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
            for station_no in range(1, 9)
        }
        alarm_count_data["others_alarm_count"] = (
            len(alarm_history) - sum(keyword_counts.values())
        )

        table_data |= alarm_count_data  # データ結合
        debug_dump(table_data)  # debug

        return table_data


    def register_data(self, data: dict):
        try:
            record, errors = normalize_record(data)

            if errors:
                return {
                    "ok": False,
                    "message": "\n".join(errors),
                }
            
            db.insert_record(record)

            return {
                "ok": True,
                "message": "データ登録しました",
            }

        except Exception as e:
            return {
                "ok": False,
                "message": str(e),
            }
    

    def get_record_waiting_machines(self) -> dict[str, list[str]]:
        return search_record_waiting_machine()


    def backup_database(self) -> dict[str, str | bool]:
        """SQLiteデータベースを指定ドライブへ世代管理付きでバックアップする。"""
        try:
            backup_drive = str(config.get("backup_drive", "")).strip()

            if not backup_drive:
                raise ValueError('config.jsonに"backup_drive"が設定されていません')

            # config.jsonでは "E" または "E:" のどちらでも指定可能
            drive_letter = backup_drive.rstrip(":")
            backup_directory = Path(f"{drive_letter}:/")

            if not backup_directory.exists():
                raise FileNotFoundError(f"バックアップ先ドライブが見つかりません: {backup_directory}")

            source_file = db.DB_FILE

            if not source_file.exists():
                raise FileNotFoundError(f"バックアップ元ファイルが見つかりません: {source_file}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            backup_file = backup_directory / (
                f"{source_file.stem}_{timestamp}{source_file.suffix}"
            )

            shutil.copy2(source_file, backup_file)

            # 同じデータベースのバックアップは最新10個だけ残す
            backup_files = sorted(
                backup_directory.glob(
                    f"{source_file.stem}_????????_??????{source_file.suffix}"
                )
            )

            for old_file in backup_files[:-10]:
                old_file.unlink()

            return {
                "ok": True,
                "message": (
                    "バックアップが完了しました。\n"
                    f"保存先: {backup_file}"
                ),
                "backup_file": str(backup_file),
            }

        except Exception as error:
            return {
                "ok": False,
                "message": str(error),
            }


    def export_data(
        self,
        days: int | str,
    ) -> dict[str, str | bool | int]:
        """
        今日を含む指定日数分のinspection_dataをCSVへ出力する。

        Args:
            days: 今日を含めて取得する日数 (1の場合は今日のデータだけ)

        Returns:
            dict:
                ok: 正常終了ならTrue。
                message: JS側で表示するメッセージ。
                export_file: 出力したCSVファイルのパス。
                record_count: CSVへ出力したデータ件数。
        """
        try:
            days = int(days)

            if days < 1:
                raise ValueError("取得日数は1以上で入力してください")

            end_date = datetime.now().date()

            start_date = end_date - timedelta(days=days - 1)

            columns, rows = db.get_records_for_export(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            desktop_directory = Path.home() / "Desktop"

            if not desktop_directory.exists():
                raise FileNotFoundError(
                    "デスクトップが見つかりません。\n"
                    f"確認した場所: {desktop_directory}"
                )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            export_file = desktop_directory / f"export_{timestamp}.csv"

            header = [
                get_column_label(column)
                for column in columns
            ]

            with export_file.open(
                mode="w",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                writer = csv.writer(file)

                writer.writerow(header)
                writer.writerows(rows)

            return {
                "ok": True,
                "message": (
                    "CSV出力が完了しました。\n"
                    f"対象期間: {start_date} ～ {end_date}\n"
                    f"出力件数: {len(rows)}件\n"
                    f"保存先: {export_file}"
                ),
                "export_file": str(export_file),
                "record_count": len(rows),
            }

        except Exception as error:
            return {
                "ok": False,
                "message": str(error),
            }

    

    
    def export_alarm_comments(self):
        machines = config["machines"]

        for machine_no, machine_config in machines.items():
            ip = machine_config["plc_ip_address"]
            
            try:
                registered_count = kv_alarm_history.update_alarm_comments(ip, int(machine_no), db.DB_FILE)
                print(f"設備={machine_no}:アラームコメント登録/更新件数 = {registered_count}")
            except Exception as error:
                print(
                    f"設備番号{machine_no}のアラーム取得に失敗しました。"
                    f" IPアドレス: {ip}"
                )
                print(error)

        return
    

    def reset_plc_devices(self, inspection_machine_no: str) -> dict:
        """
        指定設備のEM10000～EM10999を0リセットする。
        """
        try:
            machine_config = config["machines"].get(inspection_machine_no)

            if machine_config is None:
                raise ValueError(
                    f"設備番号{inspection_machine_no}の設定がconfig.jsonにありません"
                )
            
            plc_ip_address = machine_config["plc_ip_address"]

            kv_com.write_devices_u(
                ip_add=plc_ip_address,
                device="EM10000",
                values=[0] * 1000,
            )

            return {
                "ok": True,
                "message": (
                    "PLCデバイスをリセットしました。\n"
                    "対象: EM10000 - EM10999"
                ),
            }

        except Exception as error:
            return {
                "ok": False,
                "message": str(error),
            }

    
