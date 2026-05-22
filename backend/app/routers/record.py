from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import supabase_service
from datetime import date

router = APIRouter()


class GameResult(BaseModel):
    game_id: str
    predicted_winner: str
    actual_winner: str


@router.get("")
def get_record():
    try:
        return supabase_service.get_record()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
def submit_result(result: GameResult):
    try:
        correct = result.predicted_winner == result.actual_winner
        supabase_service.save_game_result(
            game_id=result.game_id,
            game_date=str(date.today()),
            predicted_winner=result.predicted_winner,
            actual_winner=result.actual_winner,
            correct=correct,
        )
        return {"ok": True, "correct": correct}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
