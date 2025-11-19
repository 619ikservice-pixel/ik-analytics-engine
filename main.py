import requests
import json
import hashlib
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timedelta

# ===============================
#   CONFIG
# ===============================
API_KEY = "api_89xljyng6fbsyrl5a4rz5ek0cl162qvd"
API_SECRET = "sec_5133785265790364470609218657"
WORKIZ_ACCOUNT_ID = "145257"
SHEET_NAME = "IKSHEET"

GRAPHQL_URL = "https://api.workiz.com/graphql"

YEARS = ["2025", "2026", "2027", "2028"]

# ===============================
#   GOOGLE SHEETS AUTH
# ===============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME)

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
#   HELPERS
# ===============================
def generate_signature():
    """
    Workiz HMAC-подпись:
    сырой строкой берём API_KEY + timestamp + API_SECRET
    """
    timestamp = str(int(datetime.utcnow().timestamp()))
    raw = f"{API_KEY}{timestamp}{API_SECRET}"
    signature = hashlib.sha256(raw.encode()).hexdigest()
    return timestamp, signature


def parse_job_date(dt_str: str) -> date | None:
    """Парсим дату job по createdAt (берём только YYYY-MM-DD)."""
    if not dt_str:
        return None
    try:
        # '2025-03-19T13:23:05.000Z' -> '2025-03-19'
        s = dt_str[:10]
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


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
            headers=headers,
            timeout=30,
        )

        data = response.json()

        if "errors" in data:
            print("\n❌ GraphQL Errors:", data["errors"])
            raise Exception("Ошибка GraphQL при запросе jobs")

        jobs_batch = data["data"]["jobs"]["items"]
        all_jobs.extend(jobs_batch)

        print(f"✔ Страница {page}: получено {len(jobs_batch)} работ")

        page_info = data["data"]["jobs"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        cursor = page_info["nextCursor"]
        page += 1

    print(f"\n✅ Всего работ получено: {len(all_jobs)}")
    return all_jobs


# ===============================
#   CLEAR YEAR SHEETS
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
#   WRITE RAW JOBS BY YEAR
# ===============================
def write_jobs(jobs):
    print("\n✏ Обновляем вкладки 2025–2028...")

    # сортируем по createdAt
    jobs_sorted = sorted(jobs, key=lambda x: x.get("createdAt") or "")

    rows_by_year: dict[str, list[list]] = {year: [] for year in YEARS}
    now_iso = datetime.utcnow().isoformat()

    for job in jobs_sorted:
        created_at = job.get("createdAt")
        year = created_at[:4] if created_at else "2025"
        if year not in YEARS:
            continue

        customer = job.get("customer") or {}
        tech = job.get("assignedTechnician") or {}
        job_type = job.get("jobType") or {}

        row = [
            job.get("id"),
            job.get("title"),
            job.get("status"),
            tech.get("fullName") or "",
            created_at,
            job.get("scheduledAt"),
            job.get("completedAt"),
            customer.get("fullName") or "",
            customer.get("phone") or "",
            job.get("total") or 0,
            job.get("balance") or 0,
            job.get("source") or "",
            now_iso,
            job_type.get("name") or "",
        ]
        rows_by_year[year].append(row)

    for year in YEARS:
        ws = sheet.worksheet(year)
        if rows_by_year[year]:
            ws.append_rows(rows_by_year[year])
            print(f"✔ {year}: добавлено {len(rows_by_year[year])} строк")

    print("🎉 Данные по годам обновлены.")


# ===============================
#   DASHBOARD (аналитика)
# ===============================
def build_dashboard(jobs):
    """
    Пишем агрегированную аналитику во вкладку 'Dashboard':
    - Общие метрики
    - Статистика по техникам (последние 30 дней)
    - Статистика по источникам (последние 30 дней)
    """
    print("\n📊 Строим Dashboard...")

    ws = sheet.worksheet("Dashboard")
    ws.clear()

    today = date.today()
    days_30_ago = today - timedelta(days=30)

    total_jobs = len(jobs)
    total_revenue = 0.0

    # агрегаты за 30 дней
    tech_stats: dict[str, dict] = {}
    source_stats: dict[str, dict] = {}

    created_dates = []

    for job in jobs:
        created_at = job.get("createdAt")
        created_date = parse_job_date(created_at)
        if created_date:
            created_dates.append(created_date)

        total = float(job.get("total") or 0)
        total_revenue += total

        # фильтр "последние 30 дней"
        if not created_date or created_date < days_30_ago:
            continue

        tech_name = (job.get("assignedTechnician") or {}).get("fullName") or "Unassigned"
        source = job.get("source") or "Unknown"

        # техи
        if tech_name not in tech_stats:
            tech_stats[tech_name] = {"jobs": 0, "revenue": 0.0}
        tech_stats[tech_name]["jobs"] += 1
        tech_stats[tech_name]["revenue"] += total

        # источники
        if source not in source_stats:
            source_stats[source] = {"jobs": 0, "revenue": 0.0}
        source_stats[source]["jobs"] += 1
        source_stats[source]["revenue"] += total

    # ====== Общие метрики ======
    rows = []
    rows.append(["Metric", "Value"])
    rows.append(["Last sync (UTC)", datetime.utcnow().isoformat()])
    rows.append(["Total jobs (all time)", total_jobs])
    rows.append(["Total revenue (all time)", round(total_revenue, 2)])

    if created_dates:
        rows.append(["Earliest job created", min(created_dates).isoformat()])
        rows.append(["Latest job created", max(created_dates).isoformat()])

    rows.append([])
    rows.append(["Period", "Last 30 days"])
    rows.append([])

    # ====== Техники ======
    rows.append(["Technician stats (last 30 days)"])
    rows.append(["Technician", "Jobs", "Revenue", "Avg ticket"])

    for tech_name, stats in sorted(
        tech_stats.items(),
        key=lambda kv: kv[1]["revenue"],
        reverse=True,
    ):
        jobs_count = stats["jobs"]
        revenue = stats["revenue"]
        avg_ticket = revenue / jobs_count if jobs_count else 0
        rows.append([
            tech_name,
            jobs_count,
            round(revenue, 2),
            round(avg_ticket, 2),
        ])

    rows.append([])
    # ====== Источники ======
    rows.append(["Source stats (last 30 days)"])
    rows.append(["Source", "Jobs", "Revenue", "Avg ticket"])

    for source, stats in sorted(
        source_stats.items(),
        key=lambda kv: kv[1]["revenue"],
        reverse=True,
    ):
        jobs_count = stats["jobs"]
        revenue = stats["revenue"]
        avg_ticket = revenue / jobs_count if jobs_count else 0
        rows.append([
            source,
            jobs_count,
            round(revenue, 2),
            round(avg_ticket, 2),
        ])

    ws.append_rows(rows)
    print("✅ Dashboard обновлён.")


# ===============================
#   HEALTHCHECK
# ===============================
def write_healthcheck(jobs):
    """
    Вкладка 'healthcheck':
    - последний sync
    - общее кол-во работ
    - диапазон дат по createdAt
    """
    print("\n🩺 Обновляем healthcheck...")

    ws = sheet.worksheet("healthcheck")
    ws.clear()

    created_dates = [
        d for d in (parse_job_date(job.get("createdAt")) for job in jobs) if d
    ]

    rows = []
    rows.append(["metric", "value"])
    rows.append(["last_sync_utc", datetime.utcnow().isoformat()])
    rows.append(["total_jobs", len(jobs)])

    if created_dates:
        rows.append(["first_job_created", min(created_dates).isoformat()])
        rows.append(["last_job_created", max(created_dates).isoformat()])

    ws.append_rows(rows)
    print("✅ healthcheck обновлён.")


# ===============================
#   MAIN
# ===============================
def main():
    print("🚀 Запуск Workiz Analytics Engine...")
    clear_year_sheets()
    jobs = fetch_all_jobs()
    write_jobs(jobs)
    build_dashboard(jobs)
    write_healthcheck(jobs)
    print("\n🎯 Готово: данные и аналитика обновлены.")


if __name__ == "__main__":
    main()
