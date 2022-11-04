from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from db.db_sql import SessionLocal
from logics.crud import add_user_in_db
from schemas import SignupInfo
from datetime import timedelta
from logics.json_web_token import create_jwt_access_token

router = APIRouter(
    prefix="/signup",
    tags=["Signup"]
)


def get_db():
    db = None
    try:
        db = SessionLocal()
        return db
    finally:
        db.close()


@router.post("/email")
async def signup(signup_info: SignupInfo, db: Session = Depends(get_db)):
    user_id, first_name = add_user_in_db(db, signup_info)
    if user_id:
        token = create_jwt_access_token(user_id, timedelta(20))
        return JSONResponse(
            content={
                "token": token,
                "first_name": first_name.capitalize(),
                "message": "signup successfully"
            },
            status_code=201
        )
    else:
        return JSONResponse(
            content={"message": "email already used"},
            status_code=200
        )
