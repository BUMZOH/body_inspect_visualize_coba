import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = BASE_DIR / "config.json"

with CONFIG_PATH.open(encoding='utf-8') as f:
    config = json.load(f)

# 対象機械取得
machines = list(config["machines"])
print(machines)

# 各機械のPLC IPアドレス取得
for machine in machines:
    plc_ip_address = config["machines"][machine]["plc_ip_address"]
    print(f"{machine} : plc_ip_address= {plc_ip_address}")

# 各機械の検査項目と使用デバイス
for machine in machines:
    print(f"machine={machine} : Inspection Items -----")
    
    inspection_items = config["machines"][machine]["inspection_items"]
    
    for key, value in inspection_items.items():
        japanese_name = config["japanese_names"][key]
        print(f"{key}({japanese_name}) - {value}")

    print("----------")


