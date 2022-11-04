from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from routers import upwork
from routers import signup
from routers import login
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upwork.router)
app.include_router(signup.router)
app.include_router(login.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}



