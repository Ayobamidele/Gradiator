from fastapi import FastAPI, Request, Depends, Form
from slack_sdk.signature import SignatureVerifier
from bot.core.config import settings
from bot.services.slack import SlackService
from bot.core.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from urllib.parse import parse_qs
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


@app.post("/slack/score")
async def add_or_update_score(
    request: Request,
    user_id: str = Form(...),
    user_name: str = Form(...),
    text: str = Form(""),
    db: Session = Depends(get_db)
):
    file_id = None

    if "file_id=" in text:
        parts = text.strip().split("file_id=")
        if len(parts) > 1:
            file_id = parts[1].strip()

    if not file_id:
        file_id = SlackService.get_latest_file_id_for_user(user_id)

    if not file_id:
        return JSONResponse(
            content={"message": "No file_id provided or found for user."},
            status_code=400
        )

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
    return JSONResponse(
        content={"text": leaderboard_text}
    )


@app.post("/slack/myscore")
async def myscore(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    form = parse_qs(raw_body.decode())
    user_id = form.get("user_id", [None])[0]
    if not user_id:
        return JSONResponse(
            content={"text": "Could not determine user."},
            status_code=400
        )
    score_entry = LeaderboardService.get_score(db, user_id)
    if not score_entry:
        text = "You have no score yet."
    else:
        text = f"Your score is: {score_entry.score}"
    SlackService.send_dm(user_id, text)
    return JSONResponse(
        content={"text": "Your score has been sent to you via DM."}
    )


@app.get("/")
async def home():
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "app_description": settings.APP_DESCRIPTION,
        "message": "Hi from Ayobamidele Ewetuga."
    }


if __name__ == "__main__":
    print(SlackService.list_channels())
