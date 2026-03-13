import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import pyautogui

from automation import activate_window, get_browser_window, get_search_region, process_code
from config import START_DELAY, WINDOW_TITLE_KEYWORD
from logger_utils import append_failed_code, append_result, ensure_dirs, save_debug_screenshot
from template_manager import TemplateManager


class TemplateDebugWindow:
    def __init__(self, master, log_callback, window_keyword_getter):
        self.master = master
        self.log = log_callback
        self.window_keyword_getter = window_keyword_getter
        self.manager = TemplateManager()

        self.top = tk.Toplevel(master)
        self.top.title("图像调试菜单")
        self.top.geometry("1180x720")

        self.current_preview = None
        self.staged_preview = None

        self.build_ui()
        self.refresh_template_list()

    def build_ui(self):
        toolbar = ttk.Frame(self.top, padding=10)
        toolbar.pack(fill="x")

        ttk.Label(toolbar, text="窗口标题关键字:").pack(side="left")
        self.keyword_var = tk.StringVar(value=self.window_keyword_getter())
        ttk.Entry(toolbar, textvariable=self.keyword_var, width=36).pack(side="left", padx=(6, 12))

        ttk.Button(toolbar, text="检测全部模板", command=self.test_all_templates).pack(side="left", padx=4)
        ttk.Button(toolbar, text="检测选中模板", command=self.test_selected_template).pack(side="left", padx=4)
        ttk.Button(toolbar, text="从剪贴板替换", command=self.replace_from_clipboard).pack(side="left", padx=4)
        ttk.Button(toolbar, text="从 PNG 替换", command=self.replace_from_file).pack(side="left", padx=4)
        ttk.Button(toolbar, text="保存选中模板", command=self.save_selected_template).pack(side="left", padx=4)
        ttk.Button(toolbar, text="保存全部修改", command=self.save_all_templates).pack(side="left", padx=4)
        ttk.Button(toolbar, text="撤销选中暂存", command=self.discard_selected_staged).pack(side="left", padx=4)

        extra_bar = ttk.Frame(self.top, padding=(10, 0, 10, 10))
        extra_bar.pack(fill="x")

        ttk.Button(extra_bar, text="打开 templates 文件夹", command=self.open_templates_folder).pack(side="left", padx=4)
        ttk.Button(extra_bar, text="打开备份文件夹", command=self.open_backup_folder).pack(side="left", padx=4)
        ttk.Button(extra_bar, text="刷新列表", command=self.refresh_template_list).pack(side="left", padx=4)

        main_pane = ttk.Panedwindow(self.top, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left_frame = ttk.LabelFrame(main_pane, text="模板列表")
        right_frame = ttk.LabelFrame(main_pane, text="模板预览")

        main_pane.add(left_frame, weight=3)
        main_pane.add(right_frame, weight=2)

        columns = ("name", "size", "staged", "found", "confidence", "detail")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings")
        self.tree.heading("name", text="模板名")
        self.tree.heading("size", text="尺寸")
        self.tree.heading("staged", text="已暂存修改")
        self.tree.heading("found", text="存在")
        self.tree.heading("confidence", text="最佳置信度")
        self.tree.heading("detail", text="详情")

        self.tree.column("name", width=120, anchor="w")
        self.tree.column("size", width=100, anchor="center")
        self.tree.column("staged", width=90, anchor="center")
        self.tree.column("found", width=70, anchor="center")
        self.tree.column("confidence", width=100, anchor="center")
        self.tree.column("detail", width=380, anchor="w")

        scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_template)

        preview_frame = ttk.Frame(right_frame, padding=10)
        preview_frame.pack(fill="both", expand=True)

        ttk.Label(preview_frame, text="当前模板").grid(row=0, column=0, sticky="w")
        ttk.Label(preview_frame, text="待保存模板").grid(row=0, column=1, sticky="w", padx=(20, 0))

        self.current_label = ttk.Label(preview_frame)
        self.current_label.grid(row=1, column=0, sticky="nw", pady=(8, 0))

        self.staged_label = ttk.Label(preview_frame)
        self.staged_label.grid(row=1, column=1, sticky="nw", padx=(20, 0), pady=(8, 0))

        self.info_text = tk.Text(preview_frame, height=18, width=50, state="disabled")
        self.info_text.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(12, 0))

        preview_frame.columnconfigure(0, weight=1)
        preview_frame.columnconfigure(1, weight=1)
        preview_frame.rowconfigure(2, weight=1)

    def get_selected_name(self):
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.item(selected[0], "values")[0]

    def refresh_template_list(self):
        existing_rows = {self.tree.item(item, "values")[0]: item for item in self.tree.get_children()}
        for name in self.manager.get_template_names():
            current = self.manager.get_current_image(name)
            size_text = "-"
            if current:
                size_text = f"{current.width}x{current.height}"
            staged = "是" if self.manager.get_staged_image(name) else "否"

            values = (name, size_text, staged, "-", "-", "-")
            if name in existing_rows:
                self.tree.item(existing_rows[name], values=values)
            else:
                self.tree.insert("", "end", values=values)

    def set_info(self, text):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", text)
        self.info_text.configure(state="disabled")

    def on_select_template(self, _event=None):
        name = self.get_selected_name()
        if not name:
            return

        current = self.manager.get_current_image(name)
        staged = self.manager.get_staged_image(name)

        self.current_preview = None
        self.staged_preview = None

        if current:
            self.current_preview = self.manager.build_preview(current)
            self.current_label.configure(image=self.current_preview, text="")
        else:
            self.current_label.configure(image="", text="当前文件不存在")

        if staged:
            self.staged_preview = self.manager.build_preview(staged)
            self.staged_label.configure(image=self.staged_preview, text="")
        else:
            self.staged_label.configure(image="", text="无暂存修改")

        info = [
            f"模板名: {name}",
            f"文件路径: {self.manager.get_template_path(name)}",
        ]
        if current:
            info.append(f"当前模板尺寸: {current.width}x{current.height}")
        if staged:
            info.append(f"待保存模板尺寸: {staged.width}x{staged.height}")

        self.set_info("\n".join(info))

    def update_row_result(self, name, found, confidence, detail):
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            if values[0] == name:
                values[3] = "是" if found else "否"
                values[4] = f"{confidence:.2f}" if confidence is not None else "-"
                values[5] = detail
                values[2] = "是" if self.manager.get_staged_image(name) else "否"
                self.tree.item(item, values=values)
                break

    def test_all_templates(self):
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入窗口标题关键字。")
            return

        results = self.manager.test_all_templates(keyword=keyword, prefer_staged=True)

        failed_count = 0
        found_count = 0

        for name, result in results.items():
            self.update_row_result(name, result.found, result.best_confidence, result.detail)
            if result.found:
                found_count += 1
            if result.detail.startswith("检测异常:"):
                failed_count += 1

        self.log(
            f"已完成全部模板检测。共 {len(results)} 个模板，"
            f"找到 {found_count} 个，异常 {failed_count} 个。"
        )

    def test_selected_template(self):
        name = self.get_selected_name()
        if not name:
            messagebox.showwarning("提示", "请先选择一个模板。")
            return

        keyword = self.keyword_var.get().strip()
        result = None
        try:
            result = self.manager.test_template(
                name,
                keyword=keyword,
                use_staged=(self.manager.get_staged_image(name) is not None),
            )
            self.update_row_result(name, result.found, result.best_confidence, result.detail)
            self.log(f"模板检测完成: {name} -> {result.detail}")
        except Exception as e:
            messagebox.showerror("检测失败", str(e))

    def replace_from_clipboard(self):
        name = self.get_selected_name()
        if not name:
            messagebox.showwarning("提示", "请先选择一个模板。")
            return
        try:
            self.manager.stage_from_clipboard(name)
            self.refresh_template_list()
            self.on_select_template()
            self.log(f"已从剪贴板替换模板: {name}")
        except Exception as e:
            messagebox.showerror("替换失败", str(e))

    def replace_from_file(self):
        name = self.get_selected_name()
        if not name:
            messagebox.showwarning("提示", "请先选择一个模板。")
            return

        file_path = filedialog.askopenfilename(
            title="选择 PNG 模板",
            filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            self.manager.stage_from_file(name, file_path)
            self.refresh_template_list()
            self.on_select_template()
            self.log(f"已从文件替换模板: {name}")
        except Exception as e:
            messagebox.showerror("替换失败", str(e))

    def save_selected_template(self):
        name = self.get_selected_name()
        if not name:
            messagebox.showwarning("提示", "请先选择一个模板。")
            return

        try:
            path = self.manager.save_staged(name)
            self.refresh_template_list()
            self.on_select_template()
            self.log(f"已保存模板: {name} -> {path}")
            messagebox.showinfo("保存成功", f"模板已保存：\n{path}\n旧文件已自动备份。")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def save_all_templates(self):
        try:
            saved = self.manager.save_all_staged()
            self.refresh_template_list()
            self.on_select_template()
            self.log(f"已保存全部模板，共 {len(saved)} 个。")
            messagebox.showinfo("保存成功", f"已保存 {len(saved)} 个模板，旧文件已自动备份。")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def discard_selected_staged(self):
        name = self.get_selected_name()
        if not name:
            messagebox.showwarning("提示", "请先选择一个模板。")
            return
        self.manager.discard_staged(name)
        self.refresh_template_list()
        self.on_select_template()
        self.log(f"已撤销暂存修改: {name}")

    def open_templates_folder(self):
        try:
            self.manager.open_templates_folder()
        except Exception as e:
            messagebox.showerror("打开失败", str(e))

    def open_backup_folder(self):
        try:
            self.manager.open_backup_folder()
        except Exception as e:
            messagebox.showerror("打开失败", str(e))


class RedeemApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PTCGL Code Redeemer")
        self.root.geometry("1200x760")

        self.stop_requested = False
        self.worker_thread = None
        self.status_counts = {
            "SUCCESS": 0,
            "RECAPTCHA": 0,
            "REDEEMED": 0,
            "DUPLICATE": 0,
            "ERROR": 0,
            "STOPPED": 0,
        }

        self.build_ui()

    def remove_code_from_input(self, code: str):
        """
        从输入框中删除指定的一行 code
        """
        self.root.after(0, self._remove_code_from_input, code)

    def _remove_code_from_input(self, code: str):
        lines = self.code_text.get("1.0", tk.END).splitlines()

        new_lines = []
        removed = False

        for line in lines:
            if not removed and line.strip() == code:
                removed = True
                continue
            new_lines.append(line)

        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", "\n".join(new_lines))

    def build_ui(self):
        self.build_menu()

        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="窗口标题关键字:").grid(row=0, column=0, sticky="w")
        self.window_keyword_var = tk.StringVar(value=WINDOW_TITLE_KEYWORD)
        self.window_keyword_entry = ttk.Entry(top_frame, textvariable=self.window_keyword_var, width=40)
        self.window_keyword_entry.grid(row=0, column=1, sticky="we", padx=(6, 12))

        ttk.Label(top_frame, text="开始延迟(秒):").grid(row=0, column=2, sticky="w")
        self.start_delay_var = tk.StringVar(value=str(START_DELAY))
        self.start_delay_entry = ttk.Entry(top_frame, textvariable=self.start_delay_var, width=8)
        self.start_delay_entry.grid(row=0, column=3, sticky="w", padx=(6, 12))

        self.start_button = ttk.Button(top_frame, text="开始兑换", command=self.start_run)
        self.start_button.grid(row=0, column=4, padx=6)

        self.stop_button = ttk.Button(top_frame, text="停止", command=self.stop_run)
        self.stop_button.grid(row=0, column=5, padx=6)

        self.clear_button = ttk.Button(top_frame, text="清空输入", command=self.clear_input)
        self.clear_button.grid(row=0, column=6, padx=6)

        top_frame.columnconfigure(1, weight=1)

        input_frame = ttk.LabelFrame(self.root, text="待兑换 Code（每行一个）", padding=10)
        input_frame.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        self.code_text = tk.Text(input_frame, height=10, wrap="none")
        self.code_text.pack(fill="both", expand=True)

        status_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        status_frame.pack(fill="x")

        self.summary_var = tk.StringVar(
            value="总数: 0 | SUCCESS: 0 | RECAPTCHA: 0 | REDEEMED: 0 | DUPLICATE: 0 | ERROR: 0 | STOPPED: 0"
        )
        ttk.Label(status_frame, textvariable=self.summary_var).pack(anchor="w")

        middle_pane = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        middle_pane.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        table_frame = ttk.LabelFrame(middle_pane, text="实时结果")
        log_frame = ttk.LabelFrame(middle_pane, text="运行日志")

        middle_pane.add(table_frame, weight=3)
        middle_pane.add(log_frame, weight=2)

        columns = ("index", "code", "status", "detail", "time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        self.tree.heading("index", text="#")
        self.tree.heading("code", text="Code")
        self.tree.heading("status", text="状态")
        self.tree.heading("detail", text="详情")
        self.tree.heading("time", text="时间")

        self.tree.column("index", width=50, anchor="center")
        self.tree.column("code", width=260, anchor="w")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("detail", width=420, anchor="w")
        self.tree.column("time", width=160, anchor="center")

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self.log_text = tk.Text(log_frame, height=10, state="disabled", wrap="word")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    def build_menu(self):
        menubar = tk.Menu(self.root)
        debug_menu = tk.Menu(menubar, tearoff=0)
        debug_menu.add_command(label="打开图像调试菜单", command=self.open_template_debug_window)
        menubar.add_cascade(label="图像调试", menu=debug_menu)
        self.root.config(menu=menubar)

    def open_template_debug_window(self):
        TemplateDebugWindow(
            self.root,
            log_callback=self.log,
            window_keyword_getter=lambda: self.window_keyword_var.get().strip(),
        )

    def clear_input(self):
        self.code_text.delete("1.0", tk.END)

    def log(self, message: str):
        now = datetime.now().strftime("%H:%M:%S")
        full = f"[{now}] {message}\n"
        self.root.after(0, self._append_log, full)

    def _append_log(self, text: str):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def add_result_row(self, index: int, code: str, status: str, detail: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.root.after(0, self._insert_result_row, index, code, status, detail, now)

    def _insert_result_row(self, index: int, code: str, status: str, detail: str, now: str):
        self.tree.insert("", tk.END, values=(index, code, status, detail, now))
        if status in self.status_counts:
            self.status_counts[status] += 1
        else:
            self.status_counts["ERROR"] += 1
        self.update_summary()

    def update_summary(self):
        total = sum(self.status_counts.values())
        text = (
            f"总数: {total} | "
            f"SUCCESS: {self.status_counts['SUCCESS']} | "
            f"RECAPTCHA: {self.status_counts['RECAPTCHA']} | "
            f"REDEEMED: {self.status_counts['REDEEMED']} | "
            f"DUPLICATE: {self.status_counts['DUPLICATE']} | "
            f"ERROR: {self.status_counts['ERROR']} | "
            f"STOPPED: {self.status_counts['STOPPED']}"
        )
        self.summary_var.set(text)

    def reset_runtime_ui(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for key in self.status_counts:
            self.status_counts[key] = 0
        self.update_summary()

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def get_codes_from_input(self) -> list[str]:
        raw = self.code_text.get("1.0", tk.END)
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def stop_run(self):
        self.stop_requested = True
        self.log("已请求停止，当前 code 处理完后将中止。")

    def start_run(self):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning("提示", "任务正在运行中。")
            return

        codes = self.get_codes_from_input()
        if not codes:
            messagebox.showwarning("提示", "请输入至少一条 code。")
            return

        try:
            start_delay = float(self.start_delay_var.get().strip())
            if start_delay < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "开始延迟必须是非负数字。")
            return

        self.reset_runtime_ui()
        self.stop_requested = False

        keyword = self.window_keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入窗口标题关键字。")
            return

        self.worker_thread = threading.Thread(
            target=self.run_redeem_task,
            args=(codes, keyword, start_delay),
            daemon=True,
        )
        self.worker_thread.start()

    def run_redeem_task(self, codes: list[str], keyword: str, start_delay: float):
        ensure_dirs()

        try:
            self.log(f"读取到 {len(codes)} 个待处理 code。")
            self.log(f"{start_delay} 秒后开始。")
            self.log("将鼠标移动到左上角可触发 PyAutoGUI failsafe。")

            time.sleep(start_delay)

            window = get_browser_window(keyword)
            self.log(f"找到窗口: {window.title}")
            self.log(
                f"窗口位置: left={window.left}, top={window.top}, "
                f"width={window.width}, height={window.height}"
            )

            activate_window(window)
            region = get_search_region(window)
            self.log(f"搜索区域: {region}")

            for i, code in enumerate(codes, start=1):
                if self.stop_requested:
                    self.log("任务已停止。")
                    self.add_result_row(i, code, "STOPPED", "用户请求停止，未处理")
                    append_result(code, "STOPPED", "用户请求停止，未处理")
                    continue

                self.log(f"[{i}/{len(codes)}] 开始处理: {code}")

                try:
                    status, detail = process_code(code, i, len(codes), region)

                    if status != "SUCCESS":
                        screenshot_path = save_debug_screenshot(code, status.lower(), region)
                        detail = f"{detail} | 截图: {screenshot_path}"

                except pyautogui.FailSafeException:
                    status = "STOPPED"
                    detail = "触发 PyAutoGUI failsafe，脚本终止"
                    self.log(detail)
                    self.add_result_row(i, code, status, detail)
                    append_result(code, status, detail)
                    append_failed_code(code)
                    break

                except Exception as e:
                    status = "ERROR"
                    screenshot_path = save_debug_screenshot(code, "exception", region)
                    detail = f"脚本异常: {e} | 截图: {screenshot_path}"
                    pyautogui.press("f5")
                    time.sleep(8.0)

                append_result(code, status, detail)
                self.add_result_row(i, code, status, detail)
                
                if status == "SUCCESS":
                    self.remove_code_from_input(code)
                else:
                    is_new_failed = append_failed_code(code)
                    if is_new_failed:
                        self.log(f"[{i}/{len(codes)}] 已加入 failed_codes.txt: {code}")
                    else:
                        self.log(f"[{i}/{len(codes)}] failed_codes.txt 中已存在: {code}")
                
                self.log(f"[{i}/{len(codes)}] 完成: {code} -> {status}")

                if self.stop_requested:
                    self.log("收到停止请求，任务结束。")
                    break

            self.log("任务完成。results.txt 已更新。")

        except Exception as e:
            self.log(f"运行失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("运行失败", str(e)))
