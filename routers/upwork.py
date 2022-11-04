
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from starlette.responses import JSONResponse
from logics.main import start_automation
from logics.crud import get_search_query_by_group, get_random_search_result, get_status_message_from_db, \
    delete_existing_data_using_same_query, get_upwork_data_by_id_and_query
from jose import jwt, JWTError
from logics.json_web_token import oauth2_bearer, SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from db.db_sql import SessionLocal
from db.db_sql import engine
from db import db_sql_models

db_sql_models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/upwork",
    tags=["Upwork"]
)


def get_db():
    db = None
    try:
        db = SessionLocal()
        return db
    finally:
        db.close()


@router.get("/get-data")
async def get_data(search_key: str, token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["id"]
    except JWTError:
        return HTTPException(
            status_code=404,
            detail={"Token Is Not Valid"}
        )
    data = get_upwork_data_by_id_and_query(db, user_id, search_key)
    return JSONResponse(
        content={"data": data, "proces_status": "processing"}, status_code=200
    )


@router.post("/start-scraping")
async def start_scraping(search_key: str, search_pages: int, background_tasks: BackgroundTasks,
                         token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["id"]
    except JWTError:
        return HTTPException(
            status_code=404,
            detail={"Token Is Not Valid"}
        )
    background_tasks.add_task(start_automation, db, user_id,
                              search_key, search_pages)
    delete_existing_data_using_same_query(db, user_id, search_key)

    return {
        "feedback": {
            "message": "Scraping Started",
            "status_message": "scraping_started"
        }
    }


@router.get("/status")
async def data_is_available(token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["id"]
    except JWTError:
        return HTTPException(
            status_code=404,
            detail={"Token Is Not Valid"}
        )

    status_message = get_status_message_from_db(db, user_id)
    if status_message is None:
        return JSONResponse(
            content={"status_message": False}, status_code=200
        )
    else:
        if status_message == "data":
            return JSONResponse(
                content={"status_message": True}, status_code=200
            )
        else:
            try:
                str_to_int = int(status_message)
                return JSONResponse(
                    content={"status_message": "page_scraped", "page_no": str_to_int}, status_code=200
                )
            except Exception as e:
                return JSONResponse(
                    content={"status_message": status_message}, status_code=200
                )


@router.get("/popular-searches")
async def popular_searches(db: Session = Depends(get_db)):
    search_result = get_search_query_by_group(db)
    if search_result:
        return JSONResponse(
            content={"top_searches": search_result},
            status_code=200
        )
    return JSONResponse(
        content={"top_searches": None},
        status_code=404
    )


@router.get("/extract")
async def extract_search_result_from_db(query: str, db: Session = Depends(get_db)):
    data = get_random_search_result(db, query)
    if data:
        return JSONResponse(
            content={"search_result": data},
            status_code=200
        )
    return JSONResponse(
        content={"search_result": None},
        status_code=200
    )

