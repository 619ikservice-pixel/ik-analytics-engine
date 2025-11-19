import os
import json
import datetime as dt

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_gspread_client():
    """Авторизация в Google Sheets через service account из переменной окружения."""
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


def get_or_create_healthcheck_worksheet(sh):
    """Берём лист healthcheck, если его нет — создаём и ставим заголовки."""
    title = "healthcheck"
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=100, cols=3)
        ws.append_row(["timestamp_utc", "message"])
    return ws


def main():
    print("=== IK Analytics Engine: start healthcheck ===")

    # Название таблицы — то, что ты создал в Google Sheets
    sheet_name = os.environ.get("GOOGLE_SHEET_NAME", "IK Analytics Engine")

    gc = get_gspread_client()
    print(f"Opened Google client, trying to open spreadsheet: {sheet_name!r}")

    try:
        sh = gc.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        # На всякий случай — если вдруг таблицу удалят, создадим новую
        print("Spreadsheet not found, creating a new one...")
        sh = gc.create(sheet_name)

    ws = get_or_create_healthcheck_worksheet(sh)

    now_utc = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    row = [now_utc, "GitHub Actions sync OK"]
    ws.append_row(row)

    print("Row appended to 'healthcheck':", row)
    print("=== IK Analytics Engine: healthcheck finished successfully ===")


if __name__ == "__main__":
    main()
