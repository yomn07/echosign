from fastapi import FastAPI
from routes import translation_router, landmarks_router
app = FastAPI(
    title="EchoSign Translation & Landmark Service",
    version="1.0.0",
)

app.include_router(
    translation_router,
)

app.include_router(
    landmarks_router,
)


@app.get("/health")
def health():
    return {
        "service": "translation-landmark-service",
        "status": "healthy",
    }