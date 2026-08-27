import httpx

from fastapi import APIRouter, Request, Response


router = APIRouter(
    tags=["Translation"],
)

TRANSLATION_SERVICE_URL = "http://translation-service:8003"


@router.api_route(
    "/translate",
    methods=["POST"],
)
async def translate(request: Request):
    body = await request.body()

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() != "host"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TRANSLATION_SERVICE_URL}/translate",
            content=body,
            headers=headers,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )


@router.api_route(
    "/landmark/{word}",
    methods=["GET"],
)
async def landmark(
    word: str,
    request: Request,
):
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() != "host"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TRANSLATION_SERVICE_URL}/landmark/{word}",
            headers=headers,
            params=request.query_params,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )