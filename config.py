from pathlib import Path
import pyautogui

# =========================
# 路径配置
# =========================
RESULTS_FILE = Path("results.txt")
TEMPLATE_DIR = Path("templates")
DEBUG_DIR = Path("debug_screenshots")

INPUT_BOX_IMG = TEMPLATE_DIR / "input_box.png"
SUBMIT_BUTTON_IMG = TEMPLATE_DIR / "submit_button.png"
REDEEM_BUTTON_IMG = TEMPLATE_DIR / "redeem_button.png"

SUCCESS_IMG = TEMPLATE_DIR / "success.png"
RECAPTCHA_IMG = TEMPLATE_DIR / "recaptcha.png"
REDEEMED_IMG = TEMPLATE_DIR / "redeemed.png"
DUPLICATE_IMG = TEMPLATE_DIR / "duplicate.png"
ERROR_IMG = TEMPLATE_DIR / "error.png"

# =========================
# 运行配置
# =========================
WINDOW_TITLE_KEYWORD = "Redeem Pokémon TCG Live Codes"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

START_DELAY = 3.0
CONFIDENCE = 0.75
SEARCH_TIMEOUT = 8.0
STATUS_TIMEOUT = 10.0
STATUS_POLL_INTERVAL = 0.4

AFTER_CLICK_WAIT = 0.4
AFTER_PASTE_WAIT = 0.3
AFTER_SUBMIT_WAIT = 1.2
AFTER_REDEEM_WAIT = 1.5

REGION_PADDING_LEFT = 10
REGION_PADDING_TOP = 120
REGION_PADDING_RIGHT = 10
REGION_PADDING_BOTTOM = 20
