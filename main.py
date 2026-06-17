from fastapi import FastAPI
from database import engine, Base
from routes.routes import router
from services.twilio_service import router_wpp


Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}

app.include_router(router)
app.include_router(router_wpp)
