# ai06_service.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from PIL import Image
import pandas as pd
import base64
import os
import json
import uvicorn
from io import BytesIO

# =========================================
# CONFIG
# =========================================

PHOTO_DIR = "EnrollPhoto"
EXCEL_FILE = "Staff.xlsx"

os.makedirs(PHOTO_DIR, exist_ok=True)

# =========================================
# FASTAPI
# =========================================

app = FastAPI()

# =========================================
# HELPERS
# =========================================

def make_filename(user_id):
    return f"LF{int(user_id):08d}.jpg"


def save_user(user_id, name, position, image_bytes):

    # ---------- image ----------
    image = Image.open(image_bytes).convert("RGB")

    # AI06 size
    image = image.resize((480, 640))

    filename = make_filename(user_id)

    image_path = os.path.join(PHOTO_DIR, filename)

    image.save(image_path, "JPEG", quality=90)

    # ---------- excel ----------
    if os.path.exists(EXCEL_FILE):

        df = pd.read_excel(EXCEL_FILE)

    else:

        df = pd.DataFrame(columns=["ID", "Name", "Position"])

    # remove old
    df = df[df["ID"] != user_id]

    # add new
    df.loc[len(df)] = [user_id, name, position]

    # save
    df.to_excel(EXCEL_FILE, index=False)

    return filename


def delete_user(user_id):

    # ---------- remove from excel ----------
    if os.path.exists(EXCEL_FILE):

        df = pd.read_excel(EXCEL_FILE)

        df = df[df["ID"] != user_id]

        df.to_excel(EXCEL_FILE, index=False)

    # ---------- remove image ----------
    filename = make_filename(user_id)

    image_path = os.path.join(PHOTO_DIR, filename)

    if os.path.exists(image_path):

        os.remove(image_path)

    return filename


# =========================================
# ROOT
# =========================================

@app.get("/")
async def root():

    return {
        "status": "AI06 Service Running"
    }


# =========================================
# WEBSOCKET
# =========================================

"""@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):

    await ws.accept()

    print("Client connected")

    try:

        while True:

            data = await ws.receive_text()
            print(f"Received raw data: {data}") # لاگ اضافه شده

            message = json.loads(data)

            action = message.get("action")
            print(f"Action detected: {action}") # لاگ اضافه شده
            # =====================================
            # ADD USER
            # =====================================

            if action == "add_user":

                user_id = message["user_id"]

                name = message["name"]

                position = message["position"]

                image_base64 = message["image"]

                # decode image
                image_data = base64.b64decode(image_base64)

                image_bytes = BytesIO(image_data)

                filename = save_user(
                    user_id,
                    name,
                    position,
                    image_bytes
                )

                await ws.send_text(json.dumps({
                    "status": "success",
                    "action": "add_user",
                    "user_id": user_id,
                    "photo": filename
                }))

            # =====================================
            # DELETE USER
            # =====================================

            elif action == "delete_user":

                user_id = message["user_id"]

                filename = delete_user(user_id)

                await ws.send_text(json.dumps({
                    "status": "success",
                    "action": "delete_user",
                    "user_id": user_id,
                    "photo_deleted": filename
                }))

            # =====================================
            # UNKNOWN
            # =====================================

            else:

                await ws.send_text(json.dumps({
                    "status": "error",
                    "message": "unknown action"
                }))

    except Exception as e:
        print(f"WebSocket Error: {repr(e)}") # برای دیدن خطاهای احتمالی در حین پردازش
    finally:
        print("Client disconnected")"""

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Client connected")

    try:
        while True:
            data = await ws.receive_text()
            print("Raw data received")

            message = json.loads(data)
            action = message.get("action")
            print("Action detected:", action)

            if action == "add_user":
                print("Entering add_user branch")

                user_id = message["user_id"]
                name = message["name"]
                position = message["position"]
                image_base64 = message["image"]

                print("Decoding image...")
                image_data = base64.b64decode(image_base64)
                image_bytes = BytesIO(image_data)

                print("Calling save_user...")
                filename = save_user(user_id, name, position, image_bytes)

                print("save_user finished:", filename)

                await ws.send_text(json.dumps({
                    "status": "success",
                    "action": "add_user",
                    "user_id": user_id,
                    "photo": filename
                }))

                print("Response sent to client")

            elif action == "delete_user":
                print("Entering delete_user branch")
                user_id = message["user_id"]
                filename = delete_user(user_id)

                await ws.send_text(json.dumps({
                    "status": "success",
                    "action": "delete_user",
                    "user_id": user_id,
                    "photo_deleted": filename
                }))

            else:
                print("Unknown action")
                await ws.send_text(json.dumps({
                    "status": "error",
                    "message": "unknown action"
                }))

    except WebSocketDisconnect as e:
        print("WebSocketDisconnect:", e)

    except Exception as e:
        print("WebSocket Error:", repr(e))

    finally:
        print("Client disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

# =====================