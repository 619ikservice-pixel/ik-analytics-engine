import time
import json
import hashlib
import hmac
import requests
from urllib.parse import urlencode

# ==============================
# 🔧 Workiz API Credentials
# ==============================
API_KEY = "api_89xljyng6fbsyrl5a4rz5ek0cl162qvd"
API_SECRET = "sec_5133785265790364470609218657"
ACCOUNT_ID = "145257"   # ← это твой accountId, он виден в DevTools

BASE_URL = "https://api.workiz.com/api/v2/jobs"


# ==============================
# 🔐 Signature generator
# ==============================
def generate_signature():
    timestamp = str(int(time.time()))
    raw = timestamp + API_KEY + API_SECRET
    signature = hashlib.sha256(raw.encode()).hexdigest()
    return timestamp, signature


# ==============================
# 📥 Fetch all jobs (with logging)
# ==============================
def fetch_all_jobs(limit=1000):
    print("📡 Fetching jobs from Workiz...")

    timestamp, signature = generate_signature()

    params = {
        "limit": limit,
        "api_key": API_KEY,
        "timestamp": timestamp,
        "signature": signature
    }

    url = f"{BASE_URL}?{urlencode(params)}"
    print(f"➡️ Request URL: {url}")

    response = requests.get(url)

    print(f"➡️ HTTP Status: {response.status_code}")

    # Если Workiz вернул не JSON — покажем сырой ответ
    try:
        data = response.json()
    except Exception:
        print("\n❌ ERROR: Workiz returned NON-JSON response!")
        print("Raw response below (first 2000 chars):\n")
        print(response.text[:2000])
        raise

    return data


# ==============================
# 🚀 MAIN
# ==============================
def main():
    print("🚀 Запуск Workiz Analytics Engine…")
    print("🔍 Получаем все работы из Workiz…")

    jobs = fetch_all_jobs()

    print(f"✅ Загружено работ: {len(jobs.get('data', []))}")

    # Если хочешь — позже добавим сохранение в файл/Google Sheets


if __name__ == "__main__":
    main()
