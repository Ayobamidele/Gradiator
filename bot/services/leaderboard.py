from sqlalchemy.orm import Session
from bot.models.score import Score
from sqlalchemy.exc import NoResultFound

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
    def get_score(db: Session, user_id: str):
        return db.query(Score).filter(Score.user_id == user_id).first()

    @staticmethod
    def get_leaderboard(db: Session, limit: int = 10):
        return db.query(Score).order_by(Score.score.desc()).limit(limit).all() 