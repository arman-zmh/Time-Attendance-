import asyncio
import websockets
import json

LINUX_IP = "10.9.30.158"

async def fake_device():

    uri = f"ws://{LINUX_IP}:7788/ws"

    async with websockets.connect(uri) as ws:

        
        await ws.send(json.dumps({
            "cmd": "reg",
            "sn": "AI06_TEST_001"
        }))

        print(await ws.recv())

        while True:

            msg = await ws.recv()
            data = json.loads(msg)

            print("RECEIVED:", data)

            
            if data.get("cmd") == "setuserinfo":

                await ws.send(json.dumps({
                    "ret": "setuserinfo",
                    "result": True,
                    "userid": data["userid"]
                }))

            elif data.get("cmd") == "deleteuser":

                await ws.send(json.dumps({
                    "ret": "deleteuser",
                    "result": True
                }))

asyncio.run(fake_device())