import requests
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ===============================
#   CONFIG
# ===============================
API_KEY = "api_89xljyng6fbsyrl5a4rz5ek0cl162qvd"       # ← Вставить сюда
API_SECRET = "sec_5133785265790364470609218657"        # ← Вставить сюда
WORKIZ_ACCOUNT_ID = "145257"                           # твой accountId из /root/jobs/
SHEET_NAME = "IKSHEET"

GRAPHQL_URL = "https://api.workiz.com/graphql"

# ===============================
#   GOOGLE SHEETS AUTH
# ===============================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME)

YEARS = ["2025", "2026", "2027", "2028"]

# ===============================
#   GRAPHQL QUERY
# ===============================
QUERY = """
query Jobs($pagination: PaginationInput!) {
  jobs(pagination: $pagination) {
    items {
      id
      title
      status
      createdAt
      scheduledAt
      completedAt
      customer {
        fullName
        phone
      }
      assignedTechnician {
        fullName
      }
      total
      balance
      source
      jobType {
        name
      }
    }
    pageInfo {
      hasNextPage
      nextCursor
    }
  }
}
"""

# ===============================
#   SIGNATURE GENERATION
# ===============================
def generate_signature():
    timestamp = str(int(datetime.utcnow().timestamp()))
    raw = f"{API_KEY}{timestamp}{API_SECRET}"
    signature = requests.utils.hashlib.sha256(raw.encode()).hexdigest()
    return timestamp, signature


# ===============================
#   FETCH JOBS WITH PAGINATION
# ===============================
def fetch_all_jobs():
    print("🔍 Получаем все работы из Workiz...")

    all_jobs = []
    cursor = None
    page = 1

    while True:
        timestamp, signature = generate_signature()

        variables = {
            "pagination": {
                "limit": 100,
                "cursor": cursor
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "x-timestamp": timestamp,
            "x-signature": signature
        }

        response = requests.post(
            GRAPHQL_URL,
            json={"query": QUERY, "variables": variables},
            headers=headers
        )

        try:
            data = response.json()
        except Exception:
            print("\n❌ RAW RESPONSE:")
            print(response.text)
            raise Exception("Workiz GraphQL вернул ошибку. Проверь ключи или сигнатуру.")

        if "errors" in data:
            print("\n❌ GraphQL Errors:", data["errors"])
            raise Exception("Ошибка GraphQL")

        batch = data["data"]["jobs"]["items"]
        all_jobs.extend(batch)

        print(f"✔ Страница {page}: получено {len(batch)} работ")

        page += 1

        if not data["data"]["jobs"]["pageInfo"]["hasNextPage"]:
            break

        cursor = data["data"]["jobs"]["pageInfo"]["nextCursor"]

    print(f"\n✅ Всего работ получено: {len(all_jobs)}")
    return all_jobs


# ===============================
#   CLEAR SHEETS
# ===============================
def clear_year_sheets():
    for year in YEARS:
        ws = sheet.worksheet(year)
        ws.clear()
        ws.append_row([
            "job_id", "title", "status", "technician", "created",
            "scheduled", "completed", "customer_name", "customer_phone",
            "total", "balance", "source", "updated_at", "appliance_type"
        ])


# ===============================
#   WRITE TO SHEETS
# ===============================
def write_jobs(jobs):
    print("\n✏ Обновляем Google Sheets...")

    # сортировка по created
    jobs.sort(key=lambda x: x["createdAt"] or "", reverse=False)

    rows_by_year = {
        year: [] for year in YEARS
    }

    for job in jobs:
        created_year = job["createdAt"][:4] if job["createdAt"] else "2025"
        if created_year not in YEARS:
            continue

        rows_by_year[created_year].append([
            job["id"],
            job["title"],
            job["status"],
            (job["assignedTechnician"]["fullName"] if job["assignedTechnician"] else ""),
            job["createdAt"],
            job["scheduledAt"],
            job["completedAt"],
            (job["customer"]["fullName"] if job["customer"] else ""),
            (job["customer"]["phone"] if job["customer"] else ""),
            job["total"],
            job["balance"],
            job["source"],
            datetime.utcnow().isoformat(),
            (job["jobType"]["name"] if job["jobType"] else "")
        ])

    for year in YEARS:
        ws = sheet.worksheet(year)
        if rows_by_year[year]:
            ws.append_rows(rows_by_year[year])
            print(f"✔ {year}: добавлено {len(rows_by_year[year])} строк")

    print("🎉 Sheets обновлён полностью!")


# ===============================
#   MAIN
# ===============================
def main():
    print("🚀 Запуск Workiz Analytics Engine...")
    clear_year_sheets()
    jobs = fetch_all_jobs()
    write_jobs(jobs)


if __name__ == "__main__":
    main()
