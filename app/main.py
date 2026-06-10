from __future__ import annotations
from datetime import datetime
from pathlib import Path
import webview
import json
#　独自モジュール
from db import (
    init_db,
    insert_inspection_data,
)

# CONSTANTS -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "index.html"
STAFF_FILE = BASE_DIR / "staff.json"

# GLOBAL VARIABLES ----------------------------------------
staff = {}



def load_staff_info():
    global staff

    if not STAFF_FILE.exists():
        print("staff.jsonが見つかりません")
        return

    with STAFF_FILE.open(mode='r', encoding='UTF-8') as f:
        staff = json.load(f)
    

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
        print(shift_name)

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
        barcode_text.strip()
        staff_name = staff.get(barcode_text, "不明")
        print(staff_name)   # Debug
        return{
            "barcode_text": barcode_text,
            "staff_name": staff_name
        }
    
    def get_table_data(self):
        # 現段階は仮プログラム（固定データ）
        return {
            "count_summary": {
                "ok_count": 120,
                "ng_count": 8,
            },

            "ng_count_detail": {
                "first_check": [1, 0, 2, 0, 1, 0 ,0, 4],
                "re_check": [0, 0, 1, 0, 0, 0, 0, 0],
            },

            "alarm_info": [0, 1, 0, 2, 3, 0, 0, 1, 22]
        }


def main() -> None:
    load_staff_info()    # 従業員番号-氏名 対応表読み込み
    
    init_db()

    api = AppAPI()

    webview.create_window(
        title="ボディ検査装置 稼働データ入力画面",
        url=str(INDEX_HTML),
        js_api=api,
        width=1600,
        height=900,
    )

    webview.start(
        gui="edgechromium",
        debug=True,
    )


if __name__ == "__main__":
    main()




