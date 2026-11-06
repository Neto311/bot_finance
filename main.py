from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.minhas_economias_auth import me_router
from routes.routes import router
from routes.usuarios import usuarios_router
from services.twilio_service import router_wpp
from routes.auth import auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"], 
)

@app.get("/")
def health_check():
    return {"status": "ok"}

app.include_router(router)
app.include_router(router_wpp)
app.include_router(me_router)
app.include_router(usuarios_router)
app.include_router(auth_router)
