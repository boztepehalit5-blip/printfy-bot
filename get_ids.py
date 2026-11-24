import os
import requests

HEADERS = {"Authorization": f"Bearer {os.environ['PRINTIFY_API']}"}
BASE = "https://api.printify.com/v1"

print("SHOPS:", requests.get(f"{BASE}/shops.json", headers=HEADERS, timeout=30).json())

for bp in requests.get(f"{BASE}/catalog/blueprints.json", headers=HEADERS, timeout=30).json():
    t = bp.get("title", "")
    if any(k in t.lower() for k in ["sweatshirt", "hoodie", "tee", "t-shirt"]):
        print(f"{bp.get('id')} -> {t}")
