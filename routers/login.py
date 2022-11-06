from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from db.db_sql import SessionLocal
from logics.crud import if_email_exist_in_db, get_password_from_email, get_first_name_from_user_id
from schemas import LoginInfo
from datetime import timedelta
from logics.json_web_token import create_jwt_access_token, oauth2_bearer, SECRET_KEY, ALGORITHM
from logics.bcrypt_process import verify_password

router = APIRouter(
    prefix="/login",
    tags=["Login"]
)


def get_db():
    db = None
    try:
        db = SessionLocal()
        return db
    finally:
        db.close()


@router.post("/email")
async def login(login_info: LoginInfo, db: Session = Depends(get_db)):
    found_email = if_email_exist_in_db(db, login_info.email)
    if found_email:
        user_id, hashed_password, first_name = get_password_from_email(db, login_info.email)
        if verify_password(login_info.password, hashed_password):
            token = create_jwt_access_token(user_id, timedelta(20))
            return JSONResponse(
                content={
                    "token": token,
                    "first_name": first_name.capitalize(),
                    "message": "logged in successfully",
                    "code": 1
                },
                status_code=200
            )
        return JSONResponse(
            content={"message": "email and password doesnt match", "code": 0},
            status_code=200
        )
    return JSONResponse(
        content={
            "message": "email not used to signup",
            "code": -1
        },
        status_code=200
    )


@router.get("/token")
async def validate_user_from_token(token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["id"]
        first_name = get_first_name_from_user_id(db, user_id)
        if first_name:
            return JSONResponse(
                content={
                    "status_message": "user_validated",
                    "first_name": first_name
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={"status_message": "user_not_validated"},
                status_code=200
            )
    except JWTError:
        return HTTPException(
            status_code=200,
            detail={"Token Is Not Valid"}
        )
