""" 動作確認用プログラム """
from common_lib_mw import kv_com

plc_ip_address = "192.168.8.1"

alarm = kv_com.dl_alarm_comment(plc_ip_address)
print(alarm)


res = kv_com.write_device_d(plc_ip_address, "DM100", 445)
print(res)

res = kv_com.read_devices_d(plc_ip_address, "DM100", 10)
print(res)
print(kv_com.kv_seconds_to_datetime_str(res[0]))
exit()

# カウンタデバイス設定 ------------------------------------
device_map = {
    "EM10090": 500,         # OK数
    "EM10092": 444,         # NG数

    # 1回目検査結果
    "EM10104": 104,
    "EM10106": 106,
    "EM10108": 108,
    "EM10110": 110,
    "EM10112": 112,
    "EM10114": 114,
    "EM10116": 116,
    "EM10118": 118,
    "EM10120": 120,
    "EM10122": 122,
    "EM10124": 124,


    # 2回目検査結果
    "EM10204": 204,
    "EM10206": 206,
    "EM10208": 208,
    "EM10210": 210,
    "EM10212": 212,
    "EM10214": 214,
    "EM10216": 216,
    "EM10218": 218,
    "EM10220": 220,
    "EM10222": 222,
    "EM10224": 224,
}

if True:
    for key, value in device_map.items():
        print(key,value)
        kv_com.write_device_d(plc_ip_address, key, value)
        print(kv_com.read_device_d(plc_ip_address, key))


# 検査開始時間格納 ------------------------------------
device_map_time = {
    "EM10000":2026,     # 年
    "EM10001":7,        # 月
    "EM10002":8,        # 日
    "EM10003":19,       # 時
    "EM10004":30,       # 分
    "EM10005":44,       # 秒
}

for key, value in device_map_time.items():
    kv_com.write_device_u(plc_ip_address, key, value)
    print(kv_com.read_device_u(plc_ip_address , key))