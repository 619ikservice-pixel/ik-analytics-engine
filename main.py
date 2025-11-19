import os
import json
import datetime as dt
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# === GOOGLE CLIENT ===
def get_gspread_client():
    """Авторизация в Google Sheets через service account."""
    service_account_info = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    if not service_account_info:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT is not set")

    info = json.loads(service_account_info)

    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(info, scopes)
    gc = gspread.authorize(credentials)
    return gc


# === WORKIZ CLIENT ===
def get_workiz_jobs():
    """Получение списка JOBS из Workiz API."""
    api_key = os.environ.get("WORKIZ_API_KEY")
    api_secret = os.environ.get("WORKIZ_API_SECRET")

    if not api_key or not api_secret:
        raise RuntimeError("Workiz API credentials not set")

    url = "https://api.workiz.com/api/jobs"
    headers = {
        "Content-Type": "application/json",
        "WZ-API-KEY": api_key,
        "WZ-API-SECRET": api_secret,
    }

    print("Запрос к Workiz API...")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Ошибка Workiz:", response.text)
        raise RuntimeError(f"Workiz API failed ({response.status_code})")

    return response.json().get("data", [])


# === PARSING JOB FIELDS ===
def parse_job(job):
    """Достаём нужные поля из Workiz Job."""
    return [
        job.get("_id", ""),
        job.get("title", ""),
        job.get("status", ""),
        (job.get("assigned", [{}])[0].get("name", "") if job.get("assigned") else ""),
        job.get("createdAt", ""),
        job.get("scheduledAt", ""),
        job.get("completedAt", ""),
        job.get("client", {}).get("fullName", ""),
        job.get("client", {}).get("phone", ""),
        job.get("total", ""),
        job.get("balance", ""),
        job.get("source", ""),
    ]


# === WRITE TO GOOGLE SHEETS ===
def write_jobs_to_sheet():
    print("=== IK Analytics Engine: start job sync ===")

    gc = get_gspread_client()
    sheet_name = os.environ.get("GOOGLE_SHEET_NAME")

    sh = gc.open(sheet_name)
    ws = sh.worksheet("Jobs")

    # 1. Очистка листа перед записью
    ws.clear()
    print("Лист очищен.")

    # 2. Добавляем заголовки
    headers = [
        "job_id", "title", "status", "technician", "created",
        "scheduled", "completed", "customer_name", "customer_phone",
        "total", "balance", "source"
    ]
    ws.insert_row(headers, index=1)
    print("Заголовки установлены.")

    # 3. Запрос Workiz Jobs
    jobs = get_workiz_jobs()
    print(f"Получено {len(jobs)} jobs.")

    # 4. Обработка данных
    rows = [parse_job(j) for j in jobs]

    if rows:
        ws.insert_rows(rows, row=2)
        print(f"Записано {len(rows)} строк.")
    else:
        print("Нет данных для записи.")

    print("=== IK Analytics Engine: job sync complete ===")


# === MAIN ENTRY ===
if __name__ == "__main__":
    write_jobs_to_sheet()
