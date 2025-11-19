import requests
import time
import hashlib
import hmac

API_KEY = "api_89xljyng6fbsyrl5a4rz5ek0cl162qvd"
API_SECRET = "sec_5133785265790364470609218657"

GRAPHQL_URL = "https://app.workiz.com/graphql"

def make_signature():
    timestamp = str(int(time.time()))
    message = f"{API_KEY}{timestamp}"
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    return timestamp, signature

timestamp, signature = make_signature()

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
    "x-api-timestamp": timestamp,
    "x-api-signature": signature
}

payload = {
    "query": "query { account { id name } }",
    "variables": {}
}

r = requests.post(GRAPHQL_URL, json=payload, headers=headers)

print("STATUS:", r.status_code)
print("RAW BODY:")
print(r.text)
