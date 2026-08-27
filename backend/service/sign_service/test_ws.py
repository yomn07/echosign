import asyncio
import websockets


async def test():
    uri = "ws://localhost:8001/ws/sign"

    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:

        print("Connected!")

        # Receive the first message from sign-service
        message = await websocket.recv()

        print("Received:")
        print(message)

        # Start recording
        await websocket.send(
            '{"action": "start"}'
        )

        message = await websocket.recv()

        print("After start:")
        print(message)


asyncio.run(test())