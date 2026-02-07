from fastapi import FastAPI
from app.api.v1.routes import router as incidents_router


app = FastAPI()
app.include_router(incidents_router)


