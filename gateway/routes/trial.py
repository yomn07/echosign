import httpx

from fastapi import (
    APIRouter,
    Request,
    Response,
)


router = APIRouter(
    tags=["Trial"],
)


TRIAL_SERVICE_URL = (
    "http://trial-service:8004"
)

@router.api_route(
    "/trial/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ],
)
async def trial_proxy(
    path: str,
    request: Request,
):

    body = await request.body()


    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() != "host"
    }

    async with httpx.AsyncClient() as client:

        upstream = await client.request(
            method=request.method,

            url=(
                f"{TRIAL_SERVICE_URL}"
                f"/trial/{path}"
            ),

            content=body,

            headers=headers,

            params=request.query_params,
        )
    response = Response(
        content=upstream.content,

        status_code=upstream.status_code,

        media_type=upstream.headers.get(
            "content-type"
        ),
    )


    set_cookie_headers = (
        upstream.headers.get_list(
            "set-cookie"
        )
    )


    for cookie in set_cookie_headers:

        response.headers.append(
            "set-cookie",
            cookie,
        )


    if "cache-control" in upstream.headers:

        response.headers["cache-control"] = (
            upstream.headers[
                "cache-control"
            ]
        )


    return response
