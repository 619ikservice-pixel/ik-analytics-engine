import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# -------------------------------
# CONFIG
# -------------------------------

WORKIZ_API_KEY = "${{ secrets.WORKIZ_API_KEY }}"        # API key из GitHub secrets
WORKIZ_API_URL = "https://api.workiz.com/api/v1/jobs"

GOOGLE_KEY_FILE = "key.json"                            # Google service file
SPREADSHEET_NAME = "IKSHEET"                            # Название Google Sheet

# Вкладки по годам
YEAR_SHEETS = ["2025", "2026", "2027", "2028"]

# Поля, которые пишем в таблицу
FIELDS = [
    "job_id", "title", "status", "technician", "created",
    "scheduled", "completed", "customer_name", "customer_phone",
    "total", "balance", "source", "updated_at", "appliance_type"
]

# -------------------------------
# GOOGLE AUTH
# -------------------------------

def load_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_KEY_FILE, scope)
    return gspread.authorize(creds)

# -------------------------------
# WORKIZ API — выгрузка всех работ
# -------------------------------

def fetch_all_jobs():
    print("Fetching Workiz jobs...")

    all_jobs = []
    page = 1

    while True:
        params = {
            "api_key": WORKIZ_API_KEY,
            "page": page,
            "per_page": 200   # максимум Workiz
        }

        response = requests.get(WORKIZ_API_URL, params=params)
        data = response.json()

        jobs = data.get("jobs", [])
        if not jobs:
            break

        all_jobs.extend(jobs)
        print(f"Loaded page {page} ({len(jobs)} jobs)")

        page += 1

    print(f"Total jobs fetched: {len(all_jobs)}")
    return all_jobs

# -------------------------------
# ПРЕОБРАЗОВАНИЕ ДАТ
# -------------------------------

def safe_date(value):
    """Convert date or return empty string."""
    if not value:
        return ""
    try:
        return value.split("T")[0]
    except:
        return ""

# -------------------------------
# ПОДГОТОВКА ДАННЫХ ДЛЯ ГОДА
# -------------------------------

def convert_job(job):
    """Convert raw Workiz job to row for Google Sheets."""
    return [
        job.get("_id", ""),
        job.get("title", ""),
        job.get("status", ""),
        job.get("assignedTech", {}).get("fullName", ""),
        safe_date(job.get("createdAt")),
        safe_date(job.get("scheduledFor")),
        safe_date(job.get("completedAt")),
        job.get("client", {}).get("fullName", ""),
        job.get("client", {}).get("phone", ""),
        job.get("total", ""),
        job.get("balance", ""),
        job.get("source", ""),
        safe_date(job.get("updatedAt")),
        job.get("appliance", job.get("category", ""))  # appliance_type fallback
    ]

# -------------------------------
# ЗАПИСЬ В GOOGLE SHEETS
# -------------------------------

def write_jobs_to_sheets(gc, jobs):
    print("Writing jobs to sheets...")

    sh = gc.open(SPREADSHEET_NAME)

    # Подготовка данных по годам
    year_rows = {year: [] for year in YEAR_SHEETS}

    for job in jobs:
        created = job.get("createdAt")
        if not created:
            continue

        year = created[:4]

        if year in year_rows:
            row = convert_job(job)
            year_rows[year].append(row)

    # Запись по годам
    for year in YEAR_SHEETS:
        ws = sh.worksheet(year)

        # очищаем перед записью (кроме заголовков)
        ws.resize(1)

        rows = year_rows[year]
        if rows:
            ws.append_rows(rows, value_input_option="RAW")

        print(f"{year}: {len(rows)} jobs written")

# -------------------------------
# MAIN
# -------------------------------

def main():
    print("=== IK Analytics Engine: START ===")

    # Google Sheets auth
    gc = load_gspread_client()

    # Fetch jobs from Workiz
    jobs = fetch_all_jobs()

    # Write jobs into year sheets
    write_jobs_to_sheets(gc, jobs)

    print("=== IK Analytics Engine: DONE ===")

if __name__ == "__main__":
    main()
