"""異常連絡書をExcelテンプレートから作成する（Step1-1 動作確認版）。

Windows PCにMicrosoft Excelとxlwingsが必要。
現段階ではDBのID=259を参考にした固定データを転記する。
転記後はExcelを開いたままにし、作業者が追記・印刷できるようにする。
"""
import ctypes
from datetime import datetime
import json
from pathlib import Path
import shutil


import xlwings as xw


# CONSTANTS ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_FILE = BASE_DIR / "異常連絡書テンプレート.xlsx"
OUTPUT_DIR = BASE_DIR / "excel_output"
DATA_DEFINITION_FILE = BASE_DIR / "data_definition.json"

# DBのinspection_data、ID=259から採用した固定テストデータ
TEST_DATA = {
    "inspection_machine_no": 413,
    "record_date": "2026-09-15",
    "part_no": "299526-3520",
    "nc_process_date": "2026-09-03",
    "nc_machine_no": 43,
    "worker_name": "新美 達也",
    "remaining_checker": "林守男",
    "ng_count": 885,
    "ok_count": 4586,
    "inner_d_ngcount2": 700,
    "phi071_ngcount2": 0,
    "total_length_ngcount2": 600,
    "taper_thickness_ngcount2": 862,
    "level_gap_ngcount2": 800,
    "bottom_ngcount2": 0,
    "thickness_ngcount2": 0,
    "bottom_thickness_ngcount2": 0,
    "side_visual1_ngcount2": 300,
    "side_visual2_ngcount2": 400,
    "phi2435_depth_ngcount2": 500,
    "phi14_depth_ngcount2": 23,
}

# Excel転記先セル（テンプレート変更時はここを修正する）
BASIC_CELLS = {
    "inspection_machine_no": "W3",
    "record_date": "M2",
    "part_no": "C3",
    "nc_process_date": "L3",
    "nc_machine_no": "R3",
    "worker_name": "V2",
    "remaining_checker": "V14",
    "ng_count": "C4",
    "ok_count": "H4",
}

# (検査項目名セル, 再検査不良数セル)
NG_CELLS = [
    ("A8", "F8"),
    ("A9", "F9"),
    ("A10", "F10"),
    ("M8", "R8"),
    ("M9", "R9"),
    ("M10", "R10"),
]


# FUNCTIONS ---------------------------------------------------------
def get_inspection_items() -> dict:
    """data_definition.jsonから再検査NG項目と正式名称を取得する。"""
    with DATA_DEFINITION_FILE.open(encoding="utf-8") as file:
        definitions = json.load(file)

    return {
        column: definition["japanese"].removesuffix("NG-2").removesuffix("NG2")
        for column, definition in definitions.items()
        if column.endswith("_ngcount2")
    }


def issue_abnormality_report(data: dict) -> Path:
    """テンプレートをコピーし、指定セルへ基本情報・検査項目名・再検査不良数を転記してExcelを表示する。"""
    if not TEMPLATE_FILE.is_file():
        raise FileNotFoundError(f"テンプレートが見つかりません: {TEMPLATE_FILE}")

    inspection_items = get_inspection_items()

    abnormal_items = [
        (name, int(data.get(column) or 0))
        for column, name in inspection_items.items()
        if int(data.get(column) or 0) >= 100
    ]

    # 不良数の多い順に並べ、転記先の数だけ採用する。
    # 同数の場合はdata_definition.jsonの定義順を維持する。
    abnormal_items.sort(key=lambda item: item[1], reverse=True)
    abnormal_items = abnormal_items[:len(NG_CELLS)]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"異常連絡書_{timestamp}.xlsx"
    shutil.copy2(TEMPLATE_FILE, output_file)

    app = None
    book = None
    try:
        app = xw.App(visible=True, add_book=False)
        book = app.books.open(str(output_file))
        sheet = book.sheets["Sheet1"]

        for column, cell in BASIC_CELLS.items():
            sheet.range(cell).value = data.get(column)

        # 未使用の転記欄は空欄にする（テンプレートの残存値対策）。
        for name_cell, count_cell in NG_CELLS:
            sheet.range(name_cell).value = None
            sheet.range(count_cell).value = None

        for (name, count), (name_cell, count_cell) in zip(abnormal_items, NG_CELLS):
            sheet.range(name_cell).value = name
            sheet.range(count_cell).value = count

        book.save()
        app.visible = True
        book.activate()

        # Excelウィンドウを最大化して最前面に表示する
        hwnd = app.hwnd
        ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
        ctypes.windll.user32.SetForegroundWindow(hwnd)

        # 正常終了時はbook.close() / app.quit()を呼ばない。
        # Excelは作業者が閉じるまで開いたままにする。
    except Exception:
        if book is not None:
            book.close()
        if app is not None:
            app.quit()
        raise

    return output_file


def main() -> None:
    output_file = issue_abnormality_report(TEST_DATA)
    print(f"Excel転記完了（Excelは開いたままです）: {output_file}")


if __name__ == "__main__":
    main()
