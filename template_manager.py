from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyautogui
from PIL import Image, ImageGrab, ImageTk

from automation import get_browser_window, get_search_region
from config import TEMPLATE_PATHS, TEMPLATE_BACKUP_DIR, WINDOW_TITLE_KEYWORD


CONFIDENCE_CANDIDATES = [0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50]


@dataclass
class TemplateTestResult:
    found: bool
    best_confidence: Optional[float]
    location: Optional[tuple[int, int]]
    detail: str


class TemplateManager:
    def __init__(self):
        self.template_paths = TEMPLATE_PATHS
        self.staged_images: dict[str, Image.Image] = {}

    def get_template_names(self) -> list[str]:
        return list(self.template_paths.keys())

    def get_template_path(self, name: str) -> Path:
        return self.template_paths[name]

    def get_current_image(self, name: str) -> Optional[Image.Image]:
        path = self.get_template_path(name)
        if not path.exists():
            return None
        return Image.open(path).copy()

    def get_staged_image(self, name: str) -> Optional[Image.Image]:
        return self.staged_images.get(name)

    def stage_from_file(self, name: str, file_path: str) -> Image.Image:
        img = Image.open(file_path).convert("RGB")
        self.staged_images[name] = img
        return img

    def stage_from_clipboard(self, name: str) -> Image.Image:
        grabbed = ImageGrab.grabclipboard()
        if grabbed is None:
            raise RuntimeError("剪贴板中没有图片。")
        if isinstance(grabbed, list):
            raise RuntimeError("剪贴板中是文件列表，不是图片。请直接复制图片。")
        img = grabbed.convert("RGB")
        self.staged_images[name] = img
        return img

    def discard_staged(self, name: str) -> None:
        if name in self.staged_images:
            del self.staged_images[name]

    def discard_all_staged(self) -> None:
        self.staged_images.clear()

    def save_staged(self, name: str) -> Path:
        if name not in self.staged_images:
            raise RuntimeError("这个模板当前没有待保存修改。")

        target = self.get_template_path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        TEMPLATE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        if target.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = TEMPLATE_BACKUP_DIR / f"{target.stem}_{timestamp}{target.suffix}"
            shutil.copy2(target, backup_path)

        self.staged_images[name].save(target)
        del self.staged_images[name]
        return target

    def save_all_staged(self) -> list[Path]:
        saved = []
        for name in list(self.staged_images.keys()):
            saved.append(self.save_staged(name))
        return saved

    def get_region_for_debug(self, keyword: str = WINDOW_TITLE_KEYWORD):
        window = get_browser_window(keyword)
        return get_search_region(window)

    def test_template(
        self,
        name: str,
        keyword: str = WINDOW_TITLE_KEYWORD,
        use_staged: bool = False,
    ) -> TemplateTestResult:
        region = self.get_region_for_debug(keyword)
        image_source = None

        if use_staged and name in self.staged_images:
            temp_path = Path("_temp_debug_template.png")
            self.staged_images[name].save(temp_path)
            image_source = temp_path
        else:
            image_source = self.get_template_path(name)

        if not image_source.exists():
            return TemplateTestResult(
                found=False,
                best_confidence=None,
                location=None,
                detail="模板文件不存在",
            )

        best = None
        best_pos = None

        try:
            for conf in CONFIDENCE_CANDIDATES:
                pos = pyautogui.locateCenterOnScreen(
                    str(image_source),
                    confidence=conf,
                    grayscale=False,
                    region=region,
                )
                if pos is not None:
                    best = conf
                    best_pos = (pos.x, pos.y)
                    break
        finally:
            if use_staged and image_source.name == "_temp_debug_template.png" and image_source.exists():
                try:
                    image_source.unlink()
                except Exception:
                    pass

        if best is not None:
            return TemplateTestResult(
                found=True,
                best_confidence=best,
                location=best_pos,
                detail=f"找到，最佳 confidence={best:.2f}，位置={best_pos}",
            )

        return TemplateTestResult(
            found=False,
            best_confidence=None,
            location=None,
            detail="未找到",
        )

    def test_all_templates(
        self,
        keyword: str = WINDOW_TITLE_KEYWORD,
        prefer_staged: bool = True,
    ) -> dict[str, TemplateTestResult]:
        results = {}

        for name in self.get_template_names():
            use_staged = prefer_staged and (name in self.staged_images)

            try:
                results[name] = self.test_template(
                    name,
                    keyword=keyword,
                    use_staged=use_staged,
                )
            except Exception as e:
                results[name] = TemplateTestResult(
                    found=False,
                    best_confidence=None,
                    location=None,
                    detail=f"检测异常: {e}",
                )

        return results

    def build_preview(self, img: Image.Image, max_size=(240, 140)):
        preview = img.copy()
        preview.thumbnail(max_size)
        return ImageTk.PhotoImage(preview)

    def open_templates_folder(self):
        path = Path(next(iter(self.template_paths.values()))).parent.resolve()
        os.startfile(path)

    def open_backup_folder(self):
        TEMPLATE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(TEMPLATE_BACKUP_DIR.resolve())
