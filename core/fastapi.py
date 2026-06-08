from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import asyncio

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ FAKE DEVICE CONNECTED SUCCESSFULLY!")
    
    await websocket.send_text(json.dumps({"status": "connected", "message": "Welcome!"}))
    
    # Start the background task
    asyncio.create_task(send_test_command(websocket))

    try:
        while True:
            text_data = await websocket.receive_textData()
            data = json.loads(text_data)
            print(f"📩 RECEIVED FROM DEVICE: {data}")

            if data.get("cmd") == "reg":
                print(f"📝 Registering device: {data.get('sn')}")
                await websocket.send_text(json.dumps({"status": "registered"}))
                
            elif data.get("ret") == "setuserinfo":
                print(f"👉 Device confirmed user: {data.get('userid')}")
                
    except WebSocketDisconnect:
        print("❌ Device disconnected.")

async def send_test_command(websocket: WebSocket):
    await asyncio.sleep(2)
    await websocket.send_text(json.dumps({"cmd": "setuserinfo", "userid": "TEST_USER_999"}))