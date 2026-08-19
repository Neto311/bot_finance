from fastapi import FastAPI
from database import engine, Base
from routes.routes import router
from services.twilio_service import router_wpp
from routes.minhas_economias_auth import me_router
from models.minhas_economias_token import MinhasEconomiasToken

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}

app.include_router(router)
app.include_router(router_wpp)
app.include_router(me_router)
