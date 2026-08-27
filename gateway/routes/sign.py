import asyncio

import websockets

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)


router = APIRouter(
    tags=["Sign"],
)


SIGN_SERVICE_URL = (
    "ws://sign-service:8002/ws/sign"
)


@router.websocket("/ws/sign")
async def sign_proxy(
    websocket: WebSocket,
):

    await websocket.accept()

    try:

        async with websockets.connect(
            SIGN_SERVICE_URL
        ) as sign_socket:

            async def client_to_sign():

                try:

                    while True:

                        message = (
                            await websocket.receive()
                        )

                        if "text" in message:

                            await sign_socket.send(
                                message["text"]
                            )

                        elif "bytes" in message:

                            await sign_socket.send(
                                message["bytes"]
                            )

                except WebSocketDisconnect:

                    pass

            async def sign_to_client():

                try:

                    while True:

                        message = (
                            await sign_socket.recv()
                        )

                        if isinstance(
                            message,
                            bytes,
                        ):

                            await websocket.send_bytes(
                                message
                            )

                        else:

                            await websocket.send_text(
                                message
                            )

                except websockets.exceptions.ConnectionClosed:

                    pass

            await asyncio.gather(
                client_to_sign(),
                sign_to_client(),
            )

    except Exception as e:

        print(
            "Sign gateway error:",
            repr(e),
        )

        try:

            await websocket.close()

        except Exception:

            pass