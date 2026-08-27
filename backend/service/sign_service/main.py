from fastapi import FastAPI

from websocket.sign import router


app = FastAPI(
    title="EchoSign Sign Service",
    version="1.0.0",
)


app.include_router(router)


@app.get("/health")
def health_check():
    return {
        "service": "sign-service",
        "status": "healthy",
    }