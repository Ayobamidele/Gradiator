from fastapi import FastAPI, Request, status, Depends, UploadFile, File, Form
from slack_sdk.signature import SignatureVerifier
from bot.core.config import settings
from bot.services.slack import SlackService
from bot.core.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from urllib.parse import parse_qs
import re
import logging
from bot.services.leaderboard import LeaderboardService
import pandas as pd
from bot.models.score import Score, StageEnum, TrackEnum
import requests
import io

logger = logging.getLogger("slack")
logging.basicConfig(level=logging.INFO)
app = FastAPI()
verifier = SignatureVerifier(signing_secret=settings.SLACK_SIGNING_SECRET)


def parse_slack_form(request: Request):
    async def inner():
        body = await request.body()
        form = parse_qs(body.decode())
        text = form.get("text", [""])[0]
        channel_id = form.get("channel_id", [""])[0]
        user_ids = re.findall(r"<@([A-Z0-9]+)(?:\|[^>]+)?>", text)

        if user_ids:
            return user_ids, channel_id, True

        raw_words = text.replace(',', ' ').split()
        usernames = [
            word.strip().lstrip('@').replace(" ", "").lower()
            for word in raw_words if word.strip()
        ]
        return usernames, channel_id, False
    return inner



@app.post("/slack/score")
async def add_or_update_score(
    request: Request,
    db: Session = Depends(get_db)
):
    data = await request.json()
    user_id = data.get("user_id")
    user_name = data.get("user_name")
    file_id = data.get("file_id")
    if not (user_id and user_name and file_id):
        return JSONResponse(content={"message": "user_id, user_name, and file_id are required."}, status_code=400)

    response = SlackService.process_slack_file(file_id, user_id, user_name, db)
    status = response.pop("status_code", 201)
    return JSONResponse(content=response, status_code=status)


@app.post("/slack/leaderboard")
async def leaderboard(request: Request, db: Session = Depends(get_db)):
    leaderboard = LeaderboardService.get_leaderboard(db, limit=10)
    if not leaderboard:
        return JSONResponse(content={"text": "No scores yet."})
    leaderboard_text = "*Leaderboard:*" + "\n".join([
        f"{idx+1}. <@{entry.user_id}>: {entry.score}" for idx, entry in enumerate(leaderboard)
    ])
    return JSONResponse(content={"text": leaderboard_text})


@app.post("/slack/myscore")
async def myscore(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    form = parse_qs(raw_body.decode())
    user_id = form.get("user_id", [None])[0]
    if not user_id:
        return JSONResponse(content={"text": "Could not determine user."}, status_code=400)
    score_entry = LeaderboardService.get_score(db, user_id)
    if not score_entry:
        text = "You have no score yet."
    else:
        text = f"Your score is: {score_entry.score}"
    SlackService.send_dm(user_id, text)
    return JSONResponse(content={"text": "Your score has been sent to you via DM."})


@app.post("/slack/events")
async def slack_events(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    # Slack URL verification challenge
    if payload.get("type") == "url_verification":
        return JSONResponse(content={"challenge": payload["challenge"]})
    # Handle file_shared event
    event = payload.get("event", {})
    if event.get("type") == "file_shared":
        file_id = event.get("file_id")
        if file_id:
            process_slack_file(file_id, db)
    return JSONResponse(content={"ok": True})


@app.get("/")
async def home():
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "app_description": settings.APP_DESCRIPTION,
        "message": "Hi from Ayobamidele Ewetuga."
    }


def process_slack_file(file_id, db):
    bot_token = settings.SLACK_BOT_TOKEN  # Make sure this is set in your config
    # Step 1: Get file info
    info_url = "https://slack.com/api/files.info"
    headers = {"Authorization": f"Bearer {bot_token}"}
    params = {"file": file_id}
    info_resp = requests.get(info_url, headers=headers, params=params)
    info_data = info_resp.json()
    if not info_data.get("ok"):
        logger.error(f"Failed to get file info: {info_data}")
        return
    file_data = info_data["file"]
    url_private = file_data["url_private"]
    filename = file_data["name"]
    # Step 2: Download the file
    file_resp = requests.get(url_private, headers=headers)
    if file_resp.status_code != 200:
        logger.error(f"Failed to download file: {file_resp.text}")
        return
    file_bytes = file_resp.content
    # Step 3: Process the file (CSV or Excel)
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return
    required_columns = {"slack_username", "points", "stage", "track"}
    if not required_columns.issubset(df.columns):
        logger.error(f"Missing columns. Required: {required_columns}")
        return
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
            slack_user_id = SlackService.get_user_id_by_username(slack_username)
        except Exception as e:
            slack_user_id = "unknown"
            errors.append(f"Row {idx+2}: Could not get Slack user ID for username '{slack_username}' - {e}")
        try:
            log = Score(
                slack_username=slack_username,
                slack_user_id=slack_user_id,
                points=points,
                stage=stage_enum,
                track=track_enum,
                uploader_id="slack_file_upload",
                uploader_username="slack_file_upload"
            )
            logs.append(log)
        except Exception as e:
            errors.append(f"Row {idx+2}: Error creating Score object - {e}")
            continue
    if logs:
        db.add_all(logs)
        db.commit()
    logger.info(f"Logged {len(logs)} score entries from Slack file upload.")
    if errors:
        logger.error(f"Errors during Slack file upload: {errors}")


if __name__ == "__main__":
    print(SlackService.list_channels())
