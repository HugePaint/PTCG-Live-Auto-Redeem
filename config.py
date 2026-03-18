from pathlib import Path
import sys
import pyautogui


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

VERSION = "0.0.3"
MAIN_WINDOW_TITLE = f"PTCG Live Auto Redeem v{VERSION}"
DEBUG_STATUS = 1

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
    "code_success": TEMPLATE_DIR / "code_success.png",
    "code_fail": TEMPLATE_DIR / "code_fail.png",
    "duplicate": TEMPLATE_DIR / "duplicate.png",
}

INPUT_BOX_IMG = TEMPLATE_PATHS["input_box"]
SUBMIT_BUTTON_IMG = TEMPLATE_PATHS["submit_button"]
REDEEM_BUTTON_IMG = TEMPLATE_PATHS["redeem_button"]

SUCCESS_IMG = TEMPLATE_PATHS["success"]
RECAPTCHA_IMG = TEMPLATE_PATHS["recaptcha"]
CODE_SUCCESS_IMG = TEMPLATE_PATHS["code_success"]
CODE_FAIL_IMG = TEMPLATE_PATHS["code_fail"]
DUPLICATE_IMG = TEMPLATE_PATHS["duplicate"]

# =========================
# 运行配置
# =========================
WINDOW_TITLE_KEYWORD = "Redeem Pokémon TCG Live Codes"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

START_DELAY = 1.0
CONFIDENCE = 0.9
SEARCH_TIMEOUT = 3.1
STATUS_TIMEOUT = 5.0
STATUS_POLL_INTERVAL = 1.0

RANDOM_DELAY_MIN = 0.1
RANDOM_DELAY_MAX = 1.2

AFTER_CLICK_WAIT = 0.1
AFTER_PASTE_WAIT = 0.1
AFTER_SUBMIT_WAIT = 3.0
AFTER_REDEEM_WAIT = 3.0

ERROR_REFRESH_WAIT = 8.0

REGION_PADDING_LEFT = 10
REGION_PADDING_TOP = 120
REGION_PADDING_RIGHT = 10
REGION_PADDING_BOTTOM = 20
