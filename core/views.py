import asyncio
import json
import base64
import websockets
from django.shortcuts import render
from django.http import HttpResponse


async def send_to_ai06(user_id, name, position, image_file):
    uri = "ws://127.0.0.1:8001/ws"

    # خواندن فایل و تبدیل به base64
    image_bytes = image_file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "action": "add_user",
        "user_id": user_id,
        "name": name,
        "position": position,
        "image": image_base64,
    }

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(payload))
        response = await websocket.recv()
        return response


def add_user_view(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        name = request.POST.get("name")
        position = request.POST.get("position")
        image_file = request.FILES.get("image_file")

        if not image_file:
            return render(request, "core/staff_page.html", {
                "error": "لطفاً تصویر را انتخاب کنید"
            })

        try:
            response = asyncio.run(
                send_to_ai06(user_id, name, position, image_file)
            )
            return render(request, "core/staff_page.html", {
                "success": "کاربر با موفقیت ثبت شد",
                "response": response
            })
        except Exception as e:
            return render(request, "core/staff_page.html", {
                "error": f"خطا: {str(e)}"
            })

    return render(request, "core/staff_page.html")
