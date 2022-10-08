
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from routers import upwork

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upwork.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}



