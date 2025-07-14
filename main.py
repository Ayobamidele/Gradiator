from fastapi import FastAPI, Request, Depends, Form, BackgroundTasks
from slack_sdk.signature import SignatureVerifier
from bot.core.config import settings
from bot.services.slack import SlackService
from bot.core.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
import logging
from bot.services.leaderboard import LeaderboardService


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
async def leaderboard(
    request: Request,
    user_id: str = Form(...),
    user_name: str = Form(...),
    text: str = Form(""),
    db: Session = Depends(get_db)
):
    track = None
    cleaned_text = text.strip().lower()

    if cleaned_text:
        try:
            track = TrackEnum(cleaned_text)
        except ValueError:
            return JSONResponse(
                content={
                    "text": f"Invalid track '{cleaned_text}'. Valid options: backend, frontend, design, devops, data_analysis, project_management"
                },
                status_code=200
            )

    leaderboard = LeaderboardService.get_leaderboard(db, track=track, limit=10)

    if not leaderboard:
        return JSONResponse(content={"text": "No scores found for this track."}, status_code=200)

    title = f"*🏆 Leaderboard* {'for *' + track.value + '*' if track else ''}:\n"
    leaderboard_text = "\n".join([
        f"{idx+1}. `{entry.slack_username}` — {entry.points} pts (Stage {entry.stage.value})"
        for idx, entry in enumerate(leaderboard)
    ])

    return JSONResponse(
        content={
            "response_type": "in_channel",
            "text": title + leaderboard_text
        }
    )


@app.post("/slack/myscore")
async def myscore(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    score_data = LeaderboardService.get_score(db, user_id)

    if not score_data or score_data["total_score"] == 0:
        message = "You have no score yet."
    else:
        total_score = score_data["total_score"]
        tracks = score_data["tracks"]

        message_lines = [
            f"*🎯 Total Score Across All Tracks:* {total_score:.2f} pts", ""]

        for track, info in tracks.items():
            message_lines.append(
                f"*• {track.capitalize()}*\n"
                f"  └ Total: `{info['total_score']:.2f}` pts\n"
                f"  └ Latest Stage: `{info['latest_stage']}` ({info['latest_score']:.2f} pts)"
            )

        message = "\n".join(message_lines)

    # Schedule Slack DM
    background_tasks.add_task(SlackService.send_dm, user_id, message)

    return JSONResponse(
        content={"text": "📬 Your detailed score breakdown has been sent via DM."},
        status_code=200
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
