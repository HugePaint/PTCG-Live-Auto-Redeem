from pathlib import Path
import sys
import pyautogui


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()

RESULTS_FILE = Path("results.txt")
FAILED_CODES_FILE = Path("failed_codes.txt")

TEMPLATE_DIR = BASE_DIR / "templates"
DEBUG_DIR = Path("debug_screenshots")
TEMPLATE_BACKUP_DIR = Path("template_backups")


TEMPLATE_PATHS = {
    "input_box": TEMPLATE_DIR / "input_box.png",
    "submit_button": TEMPLATE_DIR / "submit_button.png",
    "redeem_button": TEMPLATE_DIR / "redeem_button.png",
    "success": TEMPLATE_DIR / "success.png",
    "recaptcha": TEMPLATE_DIR / "recaptcha.png",
    "redeemed": TEMPLATE_DIR / "redeemed.png",
    "duplicate": TEMPLATE_DIR / "duplicate.png",
    "error": TEMPLATE_DIR / "error.png",
}

INPUT_BOX_IMG = TEMPLATE_PATHS["input_box"]
SUBMIT_BUTTON_IMG = TEMPLATE_PATHS["submit_button"]
REDEEM_BUTTON_IMG = TEMPLATE_PATHS["redeem_button"]

SUCCESS_IMG = TEMPLATE_PATHS["success"]
RECAPTCHA_IMG = TEMPLATE_PATHS["recaptcha"]
REDEEMED_IMG = TEMPLATE_PATHS["redeemed"]
DUPLICATE_IMG = TEMPLATE_PATHS["duplicate"]
ERROR_IMG = TEMPLATE_PATHS["error"]

# =========================
# 运行配置
# =========================
WINDOW_TITLE_KEYWORD = "Redeem Pokémon TCG Live Codes"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

START_DELAY = 1.0
CONFIDENCE = 0.75
SEARCH_TIMEOUT = 8.0
STATUS_TIMEOUT = 10.0
STATUS_POLL_INTERVAL = 0.4

RANDOM_DELAY_MIN = 0.2
RANDOM_DELAY_MAX = 1.1

AFTER_CLICK_WAIT = 0.1
AFTER_PASTE_WAIT = 0.1
AFTER_SUBMIT_WAIT = 3.0
AFTER_REDEEM_WAIT = 2.0

REGION_PADDING_LEFT = 10
REGION_PADDING_TOP = 120
REGION_PADDING_RIGHT = 10
REGION_PADDING_BOTTOM = 20
