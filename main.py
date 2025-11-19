import time
import json
import hashlib
import requests
from urllib.parse import urlencode

# ==============================
# 🔧 Workiz API Credentials
# ==============================
API_KEY = "api_89xljyng6fbsyrl5a4rz5ek0cl162qvd"
API_SECRET = "sec_5133785265790364470609218657"
ACCOUNT_ID = "145257"

BASE_URL = "https://api.workiz.com/api/v2/jobs"


# ==============================
# 🔐 Generate Signature
# ==============================
def generate_signature():
    timestamp = str(int(time.time()))
    raw = timestamp + API_KEY + API_SECRET
    signature = hashlib.sha256(raw.encode()).hexdigest()
    return timestamp, signature


# ==============================
# 📥 Fetch jobs (with forced raw logging)
# ==============================
def fetch_all_jobs(limit=1000):
    print("📡 Fetching jobs...")

    timestamp, signature = generate_signature()

    params = {
        "limit": limit,
        "api_key": API_KEY,
        "timestamp": timestamp,
        "signature": signature
    }

    url = f"{BASE_URL}?{urlencode(params)}"
    print(f"\n➡️ REQUEST URL:\n{url}\n")

    response = requests.get(url)

    print(f"➡️ HTTP STATUS: {response.status_code}")

    # ==============================
    # 🔥 ВАЖНО: Печать сырого ответа ВСЕГДА
    # ==============================
    raw = response.text
    print("\n🔍 RAW RESPONSE (first 4000 chars):\n")
    print(raw[:4000])
    print("\n🔍 END OF RAW RESPONSE\n")

    # Теперь пробуем JSON
    try:
        data = response.json()
        return data
    except Exception as e:
        print("\n❌ JSON PARSE ERROR:", e)
        raise


# ==============================
# 🚀 MAIN
# ==============================
def main():
    print("\n🚀 Starting Workiz Sync Engine")
    print("🔍 Trying to load jobs...\n")

    jobs = fetch_all_jobs()

    print(f"\n✅ Success. Jobs loaded: {len(jobs.get('data', []))}\n")


if __name__ == "__main__":
    main()
