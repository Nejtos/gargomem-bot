"""
Previously, function captcha_resolver() used a trained neural network model (YOLO) to solve
image-based captchas. The model would analyze the captcha image, detect objects,
sort them according to their positions, and determine the correct order to click
the buttons. The detected objects were grouped into rows and columns, and buttons
marked as 'reversed' were clicked before confirming the captcha.

This older approach is no longer needed because the captcha has changed. Now,
we can solve it directly by reading the text on the buttons and selecting those
containing a star '*' symbol.

The old YOLO-based version of this function is kept commented out below for reference.
"""

# from ultralytics import YOLO

import asyncio
import random
import base64
import os
from bot.core.driver import MyDriver


async def is_captcha_active():
    driver = await MyDriver().get_driver()
    script = """
        (function() {
            const captchaElement = document.querySelector(
                '.pre-captcha.show, .border-window.ui-draggable.captcha-window.transparent.window-on-peak.no-exit-button'
            );
            const isCaptchaPresent = captchaElement !== null;
            return isCaptchaPresent;
        })();
    """
    is_captcha = await driver.evaluate(script, isolated_context=False)
    if is_captcha:
        return True
    return False


async def captcha(captcha_event):
    driver = await MyDriver().get_driver()
    prof_index = await MyDriver().get_profNum()
    captcha_attempts = 0
    max_attempts = 3
    await asyncio.sleep(random.uniform(1.24, 1.63))
    try:
        parent = await driver.query_selector(".pre-captcha.show")
        if parent:
            btn = await parent.query_selector(".button.small.green")
            if btn:
                label = await btn.query_selector("div.label")
                if label and "Rozwiąż teraz" in await label.inner_text():
                    await btn.click()
            await asyncio.sleep(random.uniform(0.7, 0.9))
    except Exception as e:
        print(f"Error: {e}")

    while captcha_attempts < max_attempts:
        captcha_attempts += 1

        if (
            not await driver.query_selector(".captcha__image img")
            or captcha_attempts >= max_attempts
        ):
            captcha_event.clear()
            break

        try:
            img_handle = await driver.wait_for_selector(
                ".captcha__image img", timeout=2000
            )
        except TimeoutError:
            print("Captcha solved (timeout occurred)")
            captcha_event.clear()
            break
        except Exception as e:
            print(f"Captcha solved (other exception: {e})")
            captcha_event.clear()
            break

        src_data = await img_handle.evaluate("el => el.getAttribute('src')")

        _, base64_data = src_data.split(",")

        image_content = base64.b64decode(base64_data)

        folder_path = "images"
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"captcha_image_{prof_index}.jpg")
        with open(file_path, "wb") as f:
            f.write(image_content)

        await asyncio.sleep(random.uniform(0.8, 1.21))
        print("Solving captcha...")
        await captcha_resolver()
        await asyncio.sleep(random.uniform(0.45, 0.6))


async def captcha_resolver():
    driver = await MyDriver().get_driver()

    buttons = await driver.locator(
        "div.captcha__buttons > div.button.small.green"
    ).all()

    star_buttons = [btn for btn in buttons if "*" in (await btn.inner_text())]

    clockwise = random.choice([True, False])
    if not clockwise:
        star_buttons.reverse()

    for btn in star_buttons:
        await btn.wait_for(state="visible", timeout=2000)
        await btn.click()
        await asyncio.sleep(random.uniform(0.55, 0.8))

    confirm = driver.locator(
        "div.captcha__confirm > div.button.small.green", has_text="Potwierdzam"
    ).first
    await confirm.wait_for(state="visible", timeout=2000)
    await confirm.click()
    await asyncio.sleep(random.uniform(0.2, 0.4))


"""
async def captcha_resolver():
    driver = await MyDriver().get_driver()
    profIndex = await MyDriver().get_profNum()
    model_path = "bot/data/best.pt"

    image_path = f"./images/captcha_image_{profIndex}.jpg"

    model = YOLO(model_path)

    results = model(source=image_path, conf=0.70)
    res_plotted = results[0].plot()

    detected_objects = []

    for result in results:
        boxes = result.boxes
        for box in boxes:
            detected_objects.append((box.cls, box.xyxy[0]))

    detected_objects.sort(key=lambda x: (x[1][1] + x[1][3]) / 2)

    num_columns = 3
    num_rows = 2

    grouped_objects = [[] for _ in range(num_rows)]
    for obj in detected_objects:
        row_index = 0 if obj[1][1] + obj[1][3] < res_plotted.shape[0] else 1
        grouped_objects[row_index].append(obj)

    for group in grouped_objects:
        group.sort(key=lambda x: (x[1][0] + x[1][2]) / 2)

    sorted_labels = [
        result.names[int(obj[0])] for row in grouped_objects for obj in row
    ]

    order = {}
    for i, label in enumerate(sorted_labels):
        row = i // num_columns
        col = i % num_columns
        key = chr(ord("A") + row * num_columns + col)
        order[key] = label

    reverted_keys = [key for key, value in order.items() if value.lower() == "reversed" and key <= 'F']

    for key in reverted_keys:
        btn = driver.locator(
            "div.captcha__buttons > div.button.small.green",
            has_text=f"Część {key}"
        ).first
        await btn.wait_for(state="visible", timeout=2000)
        await btn.click()
        await asyncio.sleep(random.uniform(0.55, 0.8))

    confirm = driver.locator(
        "div.captcha__confirm > div.button.small.green",
        has_text="Potwierdzam"
    ).first
    await confirm.wait_for(state="visible", timeout=2000)
    await confirm.click()
    await asyncio.sleep(random.uniform(0.2, 0.4))
"""
