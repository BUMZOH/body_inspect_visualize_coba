""" OperationData Generator
    - PLCから出力された稼働データ(3330個)を集計・計算し、
      各種稼働データを返す関数群(モジュール)
    - 引数を少なくするため、サーバの情報はこのモジュールに含める
      (引数は3330個のデータからなるlist)
      (Last update=2025/10/5)
"""
import os
from ping3 import ping
import pprint as pp

# 定数 ----------------------------------------------
FILE_SERVER_IP_ADD = '192.168.2.1'
BASE_FOLDER_OP = r'\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data' + '\\'

def get_op_data(mc_name:str, op_date:str)-> list:
    """ 機械名と稼働日を元にファイルサーバから稼働データを取得

    Args:
        mc_name (str): 機械名 例:MC067
        op_date (str): 稼働日 例:2025/09/25

    Returns:
        list: PLCから出力された稼働データ(3330個分)
    """
    # ファイルサーバ疎通チェック
    if connect_check(FILE_SERVER_IP_ADD)==False:
        print('Can not connect to File-Server')
        return []
    
    # ファイルパス生成
    op_date = op_date.replace('/', '')  # /除去
    fname = 'op_data' + op_date[2:] + '.CSV'
    fpath = BASE_FOLDER_OP + mc_name + '/' + fname
        
    # ファイル存在確認
    if os.path.isfile(fpath)==False:
        print(f'{mc_name}/{op_date}:Operation-data file is not found')
        return []
    
    # CSVファイル読み込み(1列データ)
    with open(fpath, 'r') as f:
        data = f.readlines()
    data = [x.rstrip('\n') for x in data]   # CR除去
    data = [int(x) for x in data]           # str→int変換

    # データサイズチェック
    if len(data)!=3330:
        print(f'{mc_name}/{op_date}:Operation-data-size is abnormal(!=3330)')
        return []

    return data


def connect_check(ip_add:str)-> bool:
    """PINGを使用した疎通確認を実施
    LANで使用するためtimeoutは0.2sec

    Args:
        ip_add (str): 接続先IPアドレス

    Returns:
        bool: 応答ありでTrue
    """
    res = ping(ip_add, timeout=0.2)
    if res!=None and res!=False:
        return True     # 応答あり
    else:
        return False    # 応答なし

# 以下DocStringなし(煩雑になるため)
# --- 必要データ取得関数 -----------------------------------
def get_all_status_data(op_data:list)->list:
    # 全時間(24h=1440min)ステータスデータのみ抽出
    return op_data[10:(10+1440)]  

def get_rt_status_data(op_data:list)->list:
    # 定時間(8:00-17:00=540min)のステータスデータのみ抽出
    return op_data[250:(250+540)]  

def get_all_prod_data(op_data:list)->list:
    # 全時間(24h=1440min)生産数データのみ抽出
    return op_data[1510:(1510+1440)]  

def get_rt_prod_data(op_data:list)->list:
    # 定時間(8:00-17:00=540min)の生産数データのみ抽出
    return op_data[1750:(1750+540)]  

# ---<TPM指標(表の順番)>-------------------------------------
# 負荷時間
def get_load_time(op_data:list)-> int:
    return 540  #負荷時間は原則540分(9h)

# 故障時間(定時間内)
def get_breakdown_time(op_data:list)->int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(3)  # 故障ステータス=3

# 段取り時間＝段取りロス(定時間内)
def get_changeover_time(op_data:list)->int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(2)  # 段替えステータス=2

# 刃具交換時間＝刃具交換ロス(定時間内)
def get_toolchange_time(op_data:list)->int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(1)  # 刃具交換ステータス=1

# 単純停止時間(定時間内)
def get_stop_time(op_data:list)->int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(16)  # 単純停止ステータス=1

# アラーム発生時間(定時間内)
def get_alarm_time(op_data:list)->int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(20)  # アラーム発生ステータス=20

# 材料切れ時間(定時間内)
def get_wait_time(op_data:list)->int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(4)  # 材料切れステータス=4

# ステータス不明時間(定時間内)
def get_unknown_time(op_data:list)->int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(0)  # 不明ステータス=0

# 稼働時間(定時間内)
def get_run_time(op_data:list)-> int:
    rt_status_data = get_rt_status_data(op_data)
    return rt_status_data.count(15) # 自動運転ステータス=15

# 時間稼働率(定時間内)
def get_op_rate(op_data:list)-> float:
    op_rate = round(get_run_time(op_data) / get_load_time(op_data), 2)
    return op_rate

# 基準CT[sec] →　本来は技術的に計算された理想値を使うべき
# (近日中にop_dataに含まれるように改良する)
def get_std_ct(op_data:list)->float:
    rt_prod_data = get_rt_prod_data(op_data)
    # 10個平均値で再格納
    avg_data = []
    for i in range(len(rt_prod_data)-10):
        avg_data.append(sum(rt_prod_data[i:i+10]) / 10)
    # 最大分間生産数から算出
    if max(avg_data)!=0:
        return round(60 / max(avg_data), 2)
    else:
        return 0

# 実際CT[sec]
def get_act_ct(op_data:list)-> float:
    # 実際CT[sec] = 定時内稼働時間[min]÷定時内生産数 x 60
    if get_prod_num(op_data)!=0:
        act_ct = round(get_run_time(op_data) / get_prod_num(op_data) * 60, 2)
        return act_ct
    else:
        return 0

# 基準生産数
def get_std_prod_num(op_data:list)->int:
    run_time = get_run_time(op_data)
    if get_std_ct(op_data)!=0:  # 0除算対策
        std_prod_num = int(run_time * 60 / get_std_ct(op_data)) 
        return std_prod_num
    else:
        return 0

# 定時間生産数＝実際生産数
def get_prod_num(op_data:list)-> int:
    rt_prod_data = get_rt_prod_data(op_data)
    return sum(rt_prod_data)

# 性能稼働率
def get_performance_rate(op_data:list)->float:
    std_ct = get_std_ct(op_data)
    prod_num = get_prod_num(op_data)
    run_time = get_run_time(op_data)
    if run_time!=0: # 0除算対策
        pfm_rate = round((std_ct * prod_num / 60 / run_time), 2)
        return pfm_rate
    else:
        return 0

# 設備総合効率（良品率100%として仮に計算しておく)
def get_oee(op_data:list)-> list:
    oee = round(get_op_rate(op_data) * get_performance_rate(op_data), 2)
    return oee

# 稼働時間(全時間)
def get_all_run_time(op_data:list)-> int:
    all_status_data = get_all_status_data(op_data)
    return all_status_data.count(15) # 自動運転ステータス=15

# 総生産数(全時間)
def get_all_prod_num(op_data:list)-> int:
    return op_data[4]

# 総アラーム発生回数
def get_all_alm_num(op_data:list)-> int:
    return op_data[5]



# 一覧出力(TPMや詳細データ結果の表としてそのまま使えるように)
def get_opdata_list(op_data:list)->list:
    """ 3330個の稼働データ(PLCから出力されたCSVファイル)を
        基に稼働データリスト(サマリー)を出力する

    Args:
        op_data (list): 稼働データ(3330個の全データ)

    Returns:
        list: 稼働データリスト(1列目=タイトル/2列目=データ)
    """
    opdata_list = []

    opdata_list.append(['負荷時間[分]', get_load_time(op_data)])
    opdata_list.append(['故障ロス[分]', get_breakdown_time(op_data)])
    opdata_list.append(['段取ロス[分]', get_changeover_time(op_data)])
    opdata_list.append(['刃具交換ロス[分]', get_toolchange_time(op_data)])
    opdata_list.append(['単純停止[分]', get_stop_time(op_data)])
    opdata_list.append(['アラーム発生[分]', get_alarm_time(op_data)])
    opdata_list.append(['材料切れ[分]', get_wait_time(op_data)])
    opdata_list.append(['不明[分]', get_unknown_time(op_data)])
    opdata_list.append(['稼働時間[分]', get_run_time(op_data)])
    opdata_list.append(['時間稼働率[%]', get_op_rate(op_data)]) # idx=9

    opdata_list.append(['基準CT [秒]', get_std_ct(op_data)])    # idx=10
    opdata_list.append(['実際CT [秒]', get_act_ct(op_data)])
    opdata_list.append(['基準生産数 [個]', get_std_prod_num(op_data)])
    opdata_list.append(['実際生産数 [個]', get_prod_num(op_data)])
    opdata_list.append(['性能稼働率 [%]', get_performance_rate(op_data)])   # idx=14

    opdata_list.append(['不良品数 [個]', 0])    # 不良品数はop_dataに含まれない idx=15
    opdata_list.append(['良品率 [%]', 1.0])     # 不良品数0として100%を格納しておく
    opdata_list.append(['設備総合効率 [%]', get_oee(op_data)])

    opdata_list.append(['総生産時間 [分]', get_all_run_time(op_data)])
    opdata_list.append(['総生産数 [個]', get_all_prod_num(op_data)])
    opdata_list.append(['総アラーム発生回数', get_all_alm_num(op_data)])
    
    return opdata_list


# テストコード(動作確認用) -----------------------------------------------------------------
if __name__=='__main__':
    # ワーキングディレクトリ変更(VSCode使用時必要)
    os.chdir(os.path.dirname(__file__))

    # サンプルデータ条件(機械名&稼働日)
    op_data = get_op_data('MC067', '2025/10/23')
    
    if len(op_data)!=0:
        pp.pprint(get_opdata_list(op_data))


# --- ToDo ---
# 生産数が良品排出数になっている可能性あり、加工数にしてもらう