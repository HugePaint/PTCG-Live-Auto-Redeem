import pyautogui
from pathlib import Path

CONFIDENCE = 0.8
TEMPLATE_DIR = Path("templates")

for name in ["input_box.png", "submit_button.png", "redeem_button.png"]:
    path = TEMPLATE_DIR / name
    pos = pyautogui.locateCenterOnScreen(str(path), confidence=CONFIDENCE)
    print(name, "=>", pos)
