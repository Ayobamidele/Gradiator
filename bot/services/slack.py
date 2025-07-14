from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from bot.core.config import settings
from sqlalchemy.orm import Session
import requests
import io
import pandas as pd
from bot.models.score import Score, StageEnum, TrackEnum


import time
from typing import Dict
from slack_sdk import WebClient
from bot.core.config import settings


class SlackService:
    _user_cache: Dict[str, str] = {}
    _last_cache_time: float = 0
    _cache_ttl: int = 3600  # Cache for 1 hour

    @staticmethod
    def _client():
        return WebClient(token=settings.SLACK_BOT_TOKEN)

    @staticmethod
    def _refresh_user_cache():
        now = time.time()
        if not SlackService._user_cache or (now - SlackService._last_cache_time) > SlackService._cache_ttl:
            try:
                response = SlackService._client().users_list()
            except SlackApiError as e:
                if e.response.status_code == 429:
                    retry_after = int(
                        e.response.headers.get("Retry-After", 10))
                    print(
                        f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    response = SlackService._client().users_list()
                else:
                    raise Exception(
                        f"User with username '{username}' not found.")

            SlackService._user_cache.clear()
            for user in response["members"]:
                if not user.get("deleted", False) and not user.get("is_bot", False):
                    SlackService._user_cache[user["name"]] = user["id"]
            SlackService._last_cache_time = now

    @staticmethod
    def get_user_id_by_username(username: str) -> str:
        SlackService._refresh_user_cache()
        user_id = SlackService._user_cache.get(username)
        if user_id:
            return user_id
        raise Exception(f"User with username '{username}' not found.")

    @staticmethod
    def list_channels(channel_name=None):
        response = SlackService._client().conversations_list(
            types="private_channel"
        )
        channels = response["channels"]
        if channel_name:
            channels = [c for c in channels if c["name"] == channel_name]
        return [{"name": c["name"], "id": c["id"]} for c in channels]

    @staticmethod
    def send_dm(user_id: str, text: str):
        client = SlackService._client()
        # Open a DM channel
        response = client.conversations_open(users=user_id)
        channel_id = response["channel"]["id"]
        # Send the message
        client.chat_postMessage(channel=channel_id, text=text)

    @staticmethod
    def process_slack_file(file_id, user_id, user_name, db):
        bot_token = settings.SLACK_BOT_TOKEN
        info_url = "https://slack.com/api/files.info"
        headers = {"Authorization": f"Bearer {bot_token}"}
        params = {"file": file_id}
        info_resp = requests.get(info_url, headers=headers, params=params)
        info_data = info_resp.json()
        if not info_data.get("ok"):
            return {"message": f"Failed to get file info: {info_data}", "status_code": 400}
        file_data = info_data["file"]
        url_private = file_data["url_private"]
        filename = file_data["name"]
        file_resp = requests.get(url_private, headers=headers)
        if file_resp.status_code != 200:
            return {"message": f"Failed to download file: {file_resp.text}", "status_code": 400}
        file_bytes = file_resp.content
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes))
            else:
                df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            return {"message": f"Error reading file: {e}", "status_code": 400}
        required_columns = {"slack_username", "points", "stage", "track"}
        if not required_columns.issubset(df.columns):
            return {"message": f"Missing columns. Required: {required_columns}", "status_code": 400}
        logs = []
        errors = []
        for idx, row in df.iterrows():
            slack_username = row["slack_username"]
            points = str(row["points"])
            stage = str(row["stage"]).lower()
            track = str(row["track"]).lower().replace(" ", "_")
            try:
                stage_enum = StageEnum(stage)
                track_enum = TrackEnum(track)
            except Exception as e:
                errors.append(f"Row {idx+2}: Invalid stage or track - {e}")
                continue
            try:
                slack_user_id = SlackService.get_user_id_by_username(
                    slack_username)
            except Exception as e:
                slack_user_id = "unknown"
                errors.append(
                    f"Row {idx+2}: Could not get Slack user ID for username '{slack_username}' - {e}")
            try:
                log = Score(
                    slack_username=slack_username,
                    slack_user_id=slack_user_id,
                    points=points,
                    stage=stage_enum,
                    track=track_enum,
                    uploader_id=user_id or "unknown",
                    uploader_username=user_name or "unknown"
                )
                logs.append(log)
            except Exception as e:
                errors.append(
                    f"Row {idx+2}: Error creating Score object - {e}")
                continue
        if logs:
            db.add_all(logs)
            db.commit()
        response = {
            "message": f"Logged {len(logs)} score entries."
        }
        if errors:
            response["errors"] = errors
        return response
