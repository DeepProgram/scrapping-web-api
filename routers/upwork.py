import json
import time
from fastapi import APIRouter, BackgroundTasks
import uuid
from starlette.responses import JSONResponse
from logics.data import get_upwork_data, if_data_exists
from logics.main import start_automation
from db.db_redis import connect_redis

router = APIRouter(
    prefix="/upwork",
    tags=["Upwork"]
)


@router.get("/get-data")
async def get_data(str_uuid: str):
    redis_db = connect_redis()
    if not redis_db:
        return JSONResponse(
            content={"message": "Internal Database Error"}, status_code=404
        )
    data = get_upwork_data(str_uuid, redis_db)
    redis_db = connect_redis()

    if data == -1:
        return JSONResponse(
            content={"message": "not allowed", "proces_status": "invalid"}, status_code=404
        )
    return JSONResponse(
        content={"data": json.loads(data), "proces_status": "processing"}, status_code=200
    )


@router.post("/start-scraping")
async def start_scraping(search_key: str, search_pages: int, background_tasks: BackgroundTasks):
    str_uuid = str(uuid.uuid4())
    redis_db = connect_redis()
    if not redis_db:
        return JSONResponse(
            content={"message": "Internal Database Error"}, status_code=404
        )
    background_tasks.add_task(start_automation, redis_db, str_uuid, search_key, search_pages)

    return {
        "feedback": {
            "message": "Scraping Started",
            "uuid": str_uuid,
        }
    }


@router.get("/status")
async def data_is_available(str_uuid: str):
    redis_db = connect_redis()
    if not redis_db:
        return JSONResponse(
            content={"message": "Internal Database Error"}, status_code=404
        )

    data_exists_value, data_status_code, data_status_text = if_data_exists(str_uuid, redis_db)
    if not data_exists_value:
        return JSONResponse(
            content={"status_message": False}, status_code=200
        )
    else:
        if data_status_code == 4:
            return JSONResponse(
                content={"status_message": "page_scraped", "page_no": data_status_text}, status_code=200
            )
        elif data_status_code == 5:
            return JSONResponse(
                content={"status_message": True}, status_code=200
            )
        else:
            return JSONResponse(
                content={"status_message": data_status_text}, status_code=200
            )