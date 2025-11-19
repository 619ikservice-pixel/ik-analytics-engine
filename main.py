import requests
import json
import gspread

# ==============================
# CONFIG
# ==============================

WORKIZ_API_KEY = "api_89xljyng6fbsyrl5a4rz5ek0cl162qvd"
GOOGLE_SHEET_NAME = "IKSHEET"

# ==============================
# GOOGLE CLIENT
# ==============================

def load_gspread_client():
    try:
        gc = gspread.service_account(filename="key.json")
        return gc
    except Exception as e:
        print("ERROR LOADING GOOGLE CLIENT:", e)
        raise

# ==============================
# FETCH JOBS FROM WORKIZ
# ==============================

def fetch_all_jobs():

    url = "https://api.workiz.com/api/v2/jobs?limit=1000"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WORKIZ_API_KEY}"
    }

    print("\n=== Fetching Workiz jobs (diagnostic mode) ===")
    response = requests.get(url, headers=headers)

    # Diagnostic output
    print("\n--- RAW RESPONSE ---")
    print("STATUS:", response.status_code)
    print("BODY:")
    print(response.text)
    print("--- END RAW RESPONSE ---\n")

    # Try convert to JSON
    try:
        data = response.json()
        return data
    except Exception as e:
        print("\nERROR: Could not parse JSON from Workiz response")
        print("Most likely wrong permissions or incorrect API endpoint.")
        raise

# ==============================
# MAIN
# ==============================

def main():
    print("=== IK Analytics Engine: Start sync ===")

    # 1. Load Google Sheets
    gc = load_gspread_client()

    # 2. Open Google Sheet
    try:
        sh = gc.open(GOOGLE_SHEET_NAME)
    except Exception as e:
        print("ERROR OPENING GOOGLE SHEET:", e)
        raise

    # 3. Fetch jobs (diagnostic only)
    jobs_raw = fetch_all_jobs()

    print("\n=== Parsed JSON structure ===")
    print(json.dumps(jobs_raw, indent=2)[:2000])  # preview
    print("\nSync COMPLETE (diagnostic mode).")

if __name__ == "__main__":
    main()
