from fastapi import FastAPI

from routes.minhas_economias_auth import me_router
from routes.routes import router
from routes.usuarios import usuarios_router
from services.twilio_service import router_wpp

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}

app.include_router(router)
app.include_router(router_wpp)
app.include_router(me_router)
app.include_router(usuarios_router)
