import requests
from urllib.parse import urlencode
import json

BASE_URL = "http://localhost:8000"
CHANNEL_ID = "C0934AQ91EH"  # #general
TEAM_ID = "T09269K6UTB"
TEAM_DOMAIN = "sytyatsquad1"
COMMANDER_ID = "U0926NF1601"
COMMANDER_NAME = "ayobamideleewetuga"
SCORE_FILE = "scores.xlsx"  # Path to your .xlsx file
UPLOADER_ID = "U123456"
UPLOADER_NAME = "test_uploader"
FILE_ID = "F094L3J29HP"

# Example multiple users
USERS = [
    "U09269KANMP|erisannieannie"
    # "U092SBV1E8G|happinessegeonu"
]


def build_slack_payload(command: str, user_mentions: list[str]):
    return urlencode({
        "token": "test-token",
        "team_id": TEAM_ID,
        "team_domain": TEAM_DOMAIN,
        "channel_id": CHANNEL_ID,
        "channel_name": "general",
        "user_id": COMMANDER_ID,
        "user_name": COMMANDER_NAME,
        "command": command,
        "text": " ".join([f"<@{u}>" for u in user_mentions]),
        "api_app_id": "A093KK8DL8H",
        "is_enterprise_install": "false",
        "response_url": "https://hooks.slack.com/commands/...",
        "trigger_id": "1234.5678.abcdef"
    })


def simulate_slack_post(endpoint: str, command: str):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = build_slack_payload(command, USERS)
    response = requests.post(
        f"{BASE_URL}/slack/{endpoint}", data=payload, headers=headers)
    print(f"{command} response:", json.dumps(response.json(), indent=4))


def test_score_upload():
    url = f"{BASE_URL}/slack/score"
    payload = {
        'user_id': UPLOADER_ID,
        'user_name': UPLOADER_NAME,
        'file_id': FILE_ID
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print("Status code:", response.status_code)
    try:
        print("Response:", json.dumps(response.json(), indent=4))
    except Exception:
        print("Raw response:", response.text)


if __name__ == "__main__":
    test_score_upload()

