import httpx

from fastapi import APIRouter, Request, Response


router = APIRouter(
    tags=["Auth"],
)


AUTH_SERVICE_URL = "http://auth-service:8001"


async def forward(
    request: Request,
    path: str,
):
    body = await request.body()

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() != "host"
    }

    async with httpx.AsyncClient() as client:

        response = await client.request(
            method=request.method,
            url=f"{AUTH_SERVICE_URL}{path}",
            content=body,
            headers=headers,
            params=request.query_params,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )


@router.api_route(
    "/auth/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ],
)
async def auth_proxy(
    path: str,
    request: Request,
):

    return await forward(
        request,
        f"/auth/{path}",
    )