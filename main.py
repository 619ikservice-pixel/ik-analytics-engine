import requests
import time
import hashlib
import hmac
import csv
import math

API_KEY = "api_89xljyng6fbsyrl5a4rz5ek0cl162qvd"
API_SECRET = "sec_5133785265790364470609218657"

GRAPHQL_URL = "https://app.workiz.com/graphql"

# -----------------------------
# Подпись Workiz
# -----------------------------
def make_signature():
    timestamp = str(int(time.time()))
    message = f"{API_KEY}{timestamp}"

    signature = hmac.new(
        API_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return timestamp, signature


# -----------------------------
# Запрос к Workiz GraphQL
# -----------------------------
def gql_request(query, variables):
    timestamp, signature = make_signature()

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "x-api-timestamp": timestamp,
        "x-api-signature": signature,
    }

    payload = {
        "operationName": "jobs-list-to-sql",
        "variables": variables,
        "query": query
    }

    response = requests.post(GRAPHQL_URL, headers=headers, json=payload)

    if response.status_code == 429:
        print("⚠️ RATE LIMIT — ждём 5 секунд…")
        time.sleep(5)
        return gql_request(query, variables)

    if response.status_code != 200:
        raise Exception(f"GraphQL Error {response.status_code}: {response.text}")

    return response.json()


# -----------------------------
# Основной запрос Workiz
# -----------------------------
QUERY = """
query jobs_list_to_sql($limit:Int!, $offset:Int!, $filters:JobsFilterInput) {
  jobs(limit:$limit, offset:$offset, filters:$filters) {
    id
    status
    jobType
    scheduledAt
    createdAt
    updatedAt
    technician {
      fullName
    }
    client {
      name
      phone
    }
    address {
      street
      city
      state
      zipcode
    }
    financial {
      total
      subtotal
      tax
    }
  }
}
"""


# -----------------------------
# Выгрузка всех работ
# -----------------------------
def fetch_all_jobs(limit=500):
    print("🔍 Получаем общее количество работ...")

    # Запрос первой страницы чтобы узнать total
    first_page = gql_request(QUERY, {
        "limit": 1,
        "offset": 0,
        "filters": {}
    })

    # Workiz не отдаёт total, поэтому считаем по факту
    # Делаем safe fallback: качаем, пока не придёт пусто

    all_jobs = []
    offset = 0

    while True:
        print(f"⏳ Загружаем offset={offset} ...")

        data = gql_request(QUERY, {
            "limit": limit,
            "offset": offset,
            "filters": {}
        })

        page = data.get("data", {}).get("jobs", [])

        if not page:
            print("✅ Дальше пусто — выгрузка завершена")
            break

        all_jobs.extend(page)
        offset += limit

        print(f"📦 Загружено: {len(all_jobs)}")

        time.sleep(0.5)

    print(f"\n🎉 ИТОГО загружено работ: {len(all_jobs)}")
    return all_jobs


# -----------------------------
# Сохранение CSV
# -----------------------------
def save_csv(jobs, filename="jobs_2025.csv"):
    print(f"💾 Сохраняем файл {filename} ...")

    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "Job ID", "Status", "Job Type",
            "Technician", "Client Name", "Client Phone",
            "Street", "City", "State", "Zip",
            "Scheduled At", "Created At", "Updated At",
            "Total", "Subtotal", "Tax"
        ])

        for j in jobs:
            writer.writerow([
                j.get("id"),
                j.get("status"),
                j.get("jobType"),
                j.get("technician", {}).get("fullName"),
                j.get("client", {}).get("name"),
                j.get("client", {}).get("phone"),
                j.get("address", {}).get("street"),
                j.get("address", {}).get("city"),
                j.get("address", {}).get("state"),
                j.get("address", {}).get("zipcode"),
                j.get("scheduledAt"),
                j.get("createdAt"),
                j.get("updatedAt"),
                j.get("financial", {}).get("total"),
                j.get("financial", {}).get("subtotal"),
                j.get("financial", {}).get("tax"),
            ])

    print("✅ CSV сохранён")


# -----------------------------
# MAIN
# -----------------------------
def main():
    print("\n🚀 Запуск Workiz Analytics Engine...")
    jobs = fetch_all_jobs(limit=300)   # можно 1000, но 300 стабильнее
    save_csv(jobs)
    print("\n🎉 ГОТОВО.\n")


if __name__ == "__main__":
    main()
