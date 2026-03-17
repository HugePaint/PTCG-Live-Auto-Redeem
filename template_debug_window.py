import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from template_manager import TemplateManager


class TemplateDebugWindow:
    def __init__(self, master, log_callback, window_keyword_getter):
        self.master = master
        self.log = log_callback
        self.window_keyword_getter = window_keyword_getter
        self.manager = TemplateManager()

        self.top = tk.Toplevel(master)
        self.top.title("图像调试菜单")
        self.top.geometry("1440x720")

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

