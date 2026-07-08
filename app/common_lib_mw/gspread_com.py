""" Google SpreadSheet関連の処理

    セルの読み取りや書き込みは最下部テストコード参照のこと
"""
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Definition of Constant -------------------------------------------------


# --- Definition of Function --------------------------------------------------
def connect_gspread(sheet_id:str, user:str)->object:
    '''
    Google SpreadSheetへの接続処理
    jsonkeyやsheet_idについては下記のURLを参照して取得しておく
    https://brian0111.com/python-google-spreadsheet-automation/
    戻り値は捜査対象となるSpreadSheetオブジェクトである
    '''
    cwd = os.getcwd()   # 現在のワーキングディレクトリ保存
    os.chdir(os.path.dirname(__file__))     # スクリプト本体にディレクトリ移動

    JSON_KEY = user + '.json'   # Jasonファイルは事前にフォルダ内に保存しておく
    if os.path.isfile(JSON_KEY)==False:
        print('JSON_KEY file is not found')
        return None

    # Google APIのスコープを設定
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]  
    # 認証情報を読み込む
    credentials = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEY, scope)
    # Googleスプレッドシートに接続
    client = gspread.authorize(credentials)
    # スプレッドシートを開く
    spreadsheet = client.open_by_key(sheet_id)

    os.chdir(cwd)   # ワーキングディレクトリを元に戻す

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
    
    # 値の取得(単一セル A1形式)
    # val = sht.acell('H1').value

    # 値の取得(複数セル) → cellオブジェクトが入ったlistが返ってくる
    # val = sht.range('A1:B10')

    # 行全体を取得
    # val = sht.row_values(1)
    
    # print(val)

    # 値の更新
    sht.update_acell('F1','12,345')

#===== MEMO ===================================================================
#
# %などの表示形式は一度空文字('')を入力するとリセットされる
# (例えば0.75を75%と表示し、空文字入力後に0.75を入力すると75%ではなく、
#  0.75と表示される)
# → 常に%をつけて入力すれば自動的に%形式の数字として認識される
# → 日付も同様のことが言える(フォーマットを常に揃える)
# → カンマ区切りもリセットされる
#
#











