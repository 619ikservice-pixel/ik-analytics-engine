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
