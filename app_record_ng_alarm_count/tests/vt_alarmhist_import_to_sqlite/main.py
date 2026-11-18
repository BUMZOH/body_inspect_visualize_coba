import json
from datetime import datetime
# 独自モジュール
from modules import vt_output_csv as vtcsv
from modules import vt_csv_to_sql as vtsql

# --- FUNCTIONS -------------------------------------------
def log(msg: str):
    """ログ出力用"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
    with open("log.txt", "a", encoding="utf-8") as f:  
	    f.write(f"{now} {msg}\n")


# --- MAIN PROCESS ----------------------------------------
# 設定ファイル読み込み
with open("setting.json", "r", encoding="utf-8") as f:
    mc_info = json.load(f)

# enableがtrueのデータのみ抽出
mc_info = { key:data for key,data in mc_info.items() if data['enable']==True}

for mc, data in mc_info.items():
    
    mc_no = int(mc[-3:])    # mcデータ例=MC055
    plc_ip = data['plc_ip']
    vt_ip = data['vt_ip']
    print(f"\n====== PROCESS START({mc}/PLC IP={plc_ip}/VT IP={vt_ip}) =====")

    # アラーム履歴をVT内SDカードへ出力(PLCのB0015をON->OFF)
    try:
        vtcsv.vt_output_csv(plc_ip)
    except Exception as e:
         print(f"例外発生(PLC通信):{e}")
         continue
         
    # アラーム履歴CSV取得->SQLiteデータ登録->CSV削除
    try:
        vtsql.vt_csv_to_sql(mc_no, vt_ip)
    except Exception as e:
        print(f"例外発生(VT通信):{e}")
        continue

print(f"===== PROCESS COMPLETED =====")
