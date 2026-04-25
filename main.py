#!/usr/bin/env python3
"""
Web Image Downloader — tkinter GUI
Usage: python3.12 main.py
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
from urllib.parse import urlparse

from downloader.extractor import FetchError
from downloader.zipper import build_zip


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Web Image Downloader")
        self.resizable(True, True)
        self.minsize(640, 480)
        self._build_ui()
        self._log_queue: queue.Queue = queue.Queue()
        self._poll_logs()

    # ── UI 構築 ──────────────────────────────────────────
    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 5}

        # URL 行
        url_frame = tk.Frame(self)
        url_frame.pack(fill="x", **pad)
        tk.Label(url_frame, text="URL:").pack(side="left")
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        url_entry.bind("<Return>", lambda _: self._start())

        # 保存先行
        dir_frame = tk.Frame(self)
        dir_frame.pack(fill="x", **pad)
        tk.Label(dir_frame, text="保存先:").pack(side="left")
        self.dir_var = tk.StringVar(value=os.path.expanduser("~"))
        dir_entry = tk.Entry(dir_frame, textvariable=self.dir_var, width=52)
        dir_entry.pack(side="left", fill="x", expand=True, padx=(4, 4))
        tk.Button(dir_frame, text="参照", command=self._browse).pack(side="left")

        # ボタン行
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", **pad)
        self.dl_btn = tk.Button(
            btn_frame, text="ダウンロード開始",
            bg="#2563eb", fg="white", font=("", 11, "bold"),
            activebackground="#1d4ed8", activeforeground="white",
            command=self._start,
        )
        self.dl_btn.pack(side="left")
        self.status_var = tk.StringVar(value="待機中")
        tk.Label(btn_frame, textvariable=self.status_var, fg="#64748b").pack(side="left", padx=12)

        # プログレスバー
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=(0, 4))

        # ログエリア
        tk.Label(self, text="進捗ログ:", anchor="w").pack(fill="x", padx=10)
        self.log_box = scrolledtext.ScrolledText(
            self, height=20, state="disabled",
            font=("Courier", 10), bg="#f8fafc",
        )
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── ディレクトリ選択 ─────────────────────────────────
    def _browse(self) -> None:
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    # ── ダウンロード開始 ─────────────────────────────────
    def _start(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            self._append_log("URLを入力してください。\n")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_var.set(url)

        self.dl_btn.config(state="disabled")
        self.progress.start(12)
        self.status_var.set("ダウンロード中...")
        self._clear_log()

        threading.Thread(
            target=self._run_download,
            args=(url, self.dir_var.get()),
            daemon=True,
        ).start()

    def _run_download(self, url: str, output_dir: str) -> None:
        def log(msg: str) -> None:
            self._log_queue.put(msg + "\n")

        try:
            zip_buf, count = build_zip(url, on_progress=log)
        except FetchError as e:
            self._log_queue.put(f"エラー: {e}\n")
            self._log_queue.put(None)  # sentinel
            return
        except Exception as e:
            self._log_queue.put(f"予期しないエラー: {e}\n")
            self._log_queue.put(None)
            return

        if count == 0:
            self._log_queue.put("対象となる画像が見つかりませんでした。\n")
            self._log_queue.put(None)
            return

        hostname = urlparse(url).hostname or "images"
        filename = f"{hostname}-images.zip"
        os.makedirs(output_dir, exist_ok=True)
        zip_path = os.path.join(output_dir, filename)
        zip_buf.seek(0)
        with open(zip_path, "wb") as f:
            f.write(zip_buf.read())

        self._log_queue.put(f"\n✓ 完了: {count} 枚の画像\n")
        self._log_queue.put(f"✓ 保存先: {zip_path}\n")
        self._log_queue.put(None)  # sentinel = done

    # ── ログポーリング ────────────────────────────────────
    def _poll_logs(self) -> None:
        try:
            while True:
                msg = self._log_queue.get_nowait()
                if msg is None:
                    # ダウンロード完了
                    self.progress.stop()
                    self.dl_btn.config(state="normal")
                    self.status_var.set("完了")
                else:
                    self._append_log(msg)
        except queue.Empty:
            pass
        self.after(100, self._poll_logs)

    def _append_log(self, text: str) -> None:
        self.log_box.config(state="normal")
        self.log_box.insert("end", text)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _clear_log(self) -> None:
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
