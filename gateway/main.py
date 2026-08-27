from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.translation import router as translation_router
from routes.sign import router as sign_router
from routes.trial import router as trial_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="EchoSign API Gateway"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(translation_router)
app.include_router(sign_router)
app.include_router(trial_router)


@app.get("/health")
async def health():
    return {
        "service": "gateway",
        "status": "healthy",
    }