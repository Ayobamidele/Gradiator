from sqlalchemy.orm import Session
from bot.models.score import Score, TrackEnum
from sqlalchemy import func


class LeaderboardService:
    @staticmethod
    def add_or_update_score(db: Session, user_id: str, score: int):
        score_obj = db.query(Score).filter(Score.user_id == user_id).first()
        if score_obj:
            score_obj.score = score
        else:
            score_obj = Score(user_id=user_id, score=score)
            db.add(score_obj)
        db.commit()
        db.refresh(score_obj)
        return score_obj

    @staticmethod
    def get_score(db: Session, slack_user_id: str):
        total_score = (
            db.query(func.sum(Score.points))
            .filter(Score.slack_user_id == slack_user_id)
            .scalar()
        ) or 0.0

        user_scores = (
            db.query(Score)
            .filter(Score.slack_user_id == slack_user_id)
            .order_by(Score.updated_at.desc())
            .all()
        )

        track_data = {}

        for score in user_scores:
            track = score.track.value

            if track not in track_data:
                track_data[track] = {
                    "total_score": 0.0,
                    "latest_stage": score.stage.value,
                    "latest_score": score.points
                }

            # Add points to total score
            track_data[track]["total_score"] += score.points

        return {
            "total_score": total_score,
            "tracks": track_data
        }

    @staticmethod
    def get_leaderboard(db: Session, track: TrackEnum, limit: int = 10):
        return (
            db.query(Score)
            .filter(Score.track == track)
            .order_by(Score.points.desc())
            .limit(limit)
            .all()
        )
