from fastapi import FastAPI
from routes import auth

app = FastAPI(
    title="EchoSign Auth Service",
    version="1.0.0",
)

app.include_router(auth.router)


@app.get("/health")
def health():
    return {
        "service": "auth-service",
        "status": "healthy",
    }