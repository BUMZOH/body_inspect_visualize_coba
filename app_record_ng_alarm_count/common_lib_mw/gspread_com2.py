from pathlib import Path
import gspread
import os


def connect_gspread(sheet_id:str, user:str):

    base_dir = Path(__file__).resolve().parent
    json_path = base_dir / f"{user}.json"

    client = gspread.service_account(
        filename=str(json_path)
    )

    spreadsheet = client.open_by_key(sheet_id)

    return spreadsheet


# テストコード(動作確認用) -----------------------------------------------------------------
if __name__=='__main__':
    # ワーキングディレクトリ変更(VSCode使用時必要)
    os.chdir(os.path.dirname(__file__))
    
    # スプレッドシートID(URLから取得する) → 下は「光和 工場稼働モニタ」の場合
    spread_sheet_id = '1_vy216XmrivXZLFosfxT3TLmpHHnyX2lgbhk3f7P-DY'
    # SpreadSheetオブジェクト取得
    spreadsheet = connect_gspread(spread_sheet_id, 'bumzoh')

    
    # ----- gspreadモジュールの使い方は以下のURL参照 -----
    # https://qiita.com/plumfield56/items/dab6230512f3381fdcad
    # https://tanuhack.com/library-gspread/
    
    # 操作対象シートの取得
    sht = spreadsheet.worksheet('Monthly')
    print(sht)



