import json
import gspread
import requests
from datetime import datetime


# =========================
#  CONFIG
# =========================

SHEET_NAME = "IKSHEET"   # <— ОБНОВЛЁННОЕ ИМЯ ГУГЛ-ТАБЛИЦЫ
JOBS_SHEET = "Jobs"
HEALTHCHECK_SHEET = "healthcheck"

WORKIZ_API_KEY = "YOUR_WORKIZ_API_KEY"  # Если нет — оставь пустым
WORKIZ_URL = "https://api.workiz.com/api/v1/jobs"


# =========================
#  GOOGLE CLIENT
# =========================

def load_gspread_client():
    """Loads service account credentials from key.json file in repo."""
    with open("key.json", "r") as f:
        creds = json.load(f)
    return gspread.service_account_from_dict(creds)


# =========================
#  WRITE JOBS TO SHEET
# =========================

def write_jobs_to_sheet(gc):
    """Writes job list into the Jobs sheet."""
    print("=== Writing jobs to sheet ===")

    sh = gc.open(SHEET_NAME)
    ws = sh.worksheet(JOBS_SHEET)

    # Заголовки
    header = ["job_id", "title", "status", "technician", "created", "scheduled"]
    ws.clear()
    ws.append_row(header)

    # Если Workiz API нет — заполним тестовыми строками, чтобы убедиться что запись работает
    fake_jobs = [
        ["12345", "Dryer not heating", "Completed", "Dennis", "2025-10-01", "2025-10-01"],
        ["12346", "Oven not working", "Scheduled", "Oleg", "2025-10-02", "2025-10-05"]
    ]

    for row in fake_jobs:
        ws.append_row(row)

    print("Jobs sheet updated successfully.")


# =========================
#  HEALTHCHECK
# =========================

def write_healthcheck(gc):
    """Writes timestamp into healthcheck sheet to confirm sync worked."""
    print("=== Writing healthcheck ===")

    sh = gc.open(SHEET_NAME)
    ws = sh.worksheet(HEALTHCHECK_SHEET)

    ws.clear()
    ws.append_row(["last_sync", datetime.utcnow().isoformat() + "Z"])

    print("Healthcheck updated.")


# =========================
#  MAIN
# =========================

def main():
    print("=== IK Analytics Engine: start job sync ===")

    try:
        gc = load_gspread_client()
        print("Google client loaded successfully.")
    except Exception as e:
        print("ERROR loading Google client:", e)
        raise

    try:
        write_jobs_to_sheet(gc)
        write_healthcheck(gc)
    except Exception as e:
        print("ERROR during sync:", e)
        raise

    print("=== Sync completed ===")


if __name__ == "__main__":
    main()

