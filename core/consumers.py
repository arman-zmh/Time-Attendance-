import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        print("✅ FAKE DEVICE CONNECTED SUCCESSFULLY!")
        
        # Send a quick welcome message so your script's first 'recv()' works
        await self.send(text_data=json.dumps({"status": "connected", "message": "Welcome device!"}))

        # OPTIONAL: Send a test command after 2 seconds to test your script's while loop
        asyncio.create_task(self.send_test_command())

    async def disconnect(self, close_code):
        print("❌ Device disconnected.")

    async def receive(self, text_data):
        # This receives the JSON messages from your fake ai06.py script
        data = json.loads(text_data)
        print(f"📩 RECEIVED FROM DEVICE: {data}")

        # Handle the responses your script sends back
        if data.get("ret") == "setuserinfo":
            print(f"👉 Device confirmed setting user info for ID: {data.get('userid')}")
        elif data.get("ret") == "deleteuser":
            print(f"👉 Device confirmed deleting user.")

    async def send_test_command(self):
        # Wait 2 seconds, then send a command to the device to test the loop
        await asyncio.sleep(2)
        print("📤 Sending test 'setuserinfo' command to device...")
        await self.send(text_data=json.dumps({
            "cmd": "setuserinfo",
            "userid": "TEST_USER_999"
        }))
