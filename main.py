from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from middleware import add_request_id_and_process_time
from logger import get_logger
from routes import router

logger = get_logger(__name__)

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(add_request_id_and_process_time)
@app.get("/")
def read_root():
    return {"message": "Welcome to the String Analysis API"}
app.include_router(router,prefix="/strings", tags=["strings API"])

