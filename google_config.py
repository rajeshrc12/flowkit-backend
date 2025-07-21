import requests
from dotenv import load_dotenv
import requests
import os
load_dotenv()

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SHEET_API_URL = "https://sheets.googleapis.com/v4/spreadsheets"


def refresh_access_token(client_id, client_secret, refresh_token):
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    response = requests.post(GOOGLE_TOKEN_URL, data=payload)
    if response.status_code == 200:
        print("🔁 Access token refreshed.")
        return response.json().get("access_token")
    else:
        print(
            f"❌ Error refreshing token: {response.status_code} - {response.text}")
        return None


def make_sheet_request(spreadsheet_id, worksheet_name, token):
    range_name = f"{worksheet_name}!A1:Z1000"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = f"{SHEET_API_URL}/{spreadsheet_id}/values/{range_name}"
    return requests.get(url, headers=headers)


def parse_sheet_response(response):
    if response.status_code != 200:
        print(
            f"❌ Sheet fetch failed: {response.status_code} - {response.text}")
        return []

    data = response.json()
    values = data.get("values", [])

    if not values:
        print("⚠️ Sheet is empty.")
        return []

    result = []
    for row in values:
        row_obj = {}
        for idx, val in enumerate(row):
            col_key = f"col{chr(65 + idx)}"  # colA, colB, ...
            row_obj[col_key] = val
        result.append(row_obj)

    return result


def fetch_worksheet_data(spreadsheet_id, worksheet_name, access_token, refresh_token, client_id, client_secret):
    response = make_sheet_request(spreadsheet_id, worksheet_name, access_token)

    if response.status_code == 401:
        print("⚠️ Access token expired. Attempting refresh...")
        new_token = refresh_access_token(
            client_id, client_secret, refresh_token)
        if not new_token:
            return []
        response = make_sheet_request(
            spreadsheet_id, worksheet_name, new_token)

    return parse_sheet_response(response)


# --- Example usage ---
def get_worksheet_data(node, credential):
    spreadsheet_id = node["data"]["spreadsheet"]
    worksheet_name = node["data"]["worksheet"]
    access_token = credential["data"]["access_token"]
    refresh_token = credential["data"]["refresh_token"]
    client_id = os.getenv("AUTH_GOOGLE_ID")
    client_secret = os.getenv("AUTH_GOOGLE_SECRET")

    rows = fetch_worksheet_data(
        spreadsheet_id,
        worksheet_name,
        access_token,
        refresh_token,
        client_id,
        client_secret
    )

    return rows
