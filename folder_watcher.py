"""Watch a directory for new project folders and display their folder names."""

from __future__ import annotations

import json
import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_NAME = "Project Folder Watcher"
POLL_MS = 1500
STABLE_POLLS = 2
MAX_PROJECTS = 200
CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / "ProjectFolderWatcher" / "settings.json"


class FolderWatcherApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1280x720")
        self.root.minsize(520, 360)
        self.root.configure(bg="#f4f6f8")
        self.watch_path = ""
        self.known: set[str] = set()
        self.pending: dict[str, tuple[tuple[int, int], int]] = {}
        self.banner_after: str | None = None
        self._build_ui()
        self._load_settings()
        self.root.after(POLL_MS, self._poll)

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"), background="#f4f6f8")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), background="#f4f6f8", foreground="#56616f")
        style.configure("Banner.TLabel", font=("Segoe UI", 18, "bold"), background="#e7f3ff", foreground="#123a5a", padding=12)

        body = ttk.Frame(self.root, padding=20)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Solver1", style="Title.TLabel").pack(anchor="w")
        ttk.Label(body, text="프로젝트 관리", style="Sub.TLabel").pack(anchor="w", pady=(4, 15))

        row = ttk.Frame(body)
        row.pack(fill="x")
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(row, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="폴더 선택", command=self._choose_folder).pack(side="left", padx=(8, 0))
        self.status_var = tk.StringVar(value="감시할 폴더를 선택하세요.")
        ttk.Label(body, textvariable=self.status_var, style="Sub.TLabel").pack(anchor="w", pady=(10, 12))

        self.banner = ttk.Label(body, text="새 프로젝트가 감지되면 여기에 제목이 표시됩니다", style="Banner.TLabel", anchor="center", wraplength=580)
        self.banner.pack(fill="x", pady=(0, 16))

        ttk.Label(body, text="프로젝트 폴더", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
        list_frame = ttk.Frame(body)
        list_frame.pack(fill="both", expand=True)
        self.projects = ttk.Treeview(list_frame, columns=("detected", "path"), show="headings", height=9)
        self.projects.heading("detected", text="감지 시각")
        self.projects.heading("path", text="프로젝트 제목 / 폴더 경로")
        self.projects.column("detected", width=145, stretch=False)
        self.projects.column("path", width=420)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.projects.yview)
        self.projects.configure(yscrollcommand=scrollbar.set)
        self.projects.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _choose_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Resolve 프로젝트 폴더 선택", mustexist=True)
        if chosen:
            self._set_watch_path(chosen)

    def _load_settings(self) -> None:
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            path = saved.get("watch_path", "")
            if path and Path(path).is_dir():
                self._set_watch_path(path)
        except (OSError, ValueError, TypeError):
            pass

    def _set_watch_path(self, path: str) -> None:
        candidate = Path(path).expanduser()
        if not candidate.is_dir():
            messagebox.showerror(APP_NAME, "선택한 경로를 찾을 수 없습니다.")
            return
        self.watch_path = str(candidate.resolve())
        self.path_var.set(self.watch_path)
        self.known.clear()
        self.pending.clear()
        for item in self.projects.get_children():
            self.projects.delete(item)
        self._scan(initial=True)
        self.status_var.set(f"감시 중 · {self.watch_path}")
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps({"watch_path": self.watch_path}, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            self.status_var.set(f"감시 중 · 설정 저장 실패: {exc}")

    def _scan(self, initial: bool = False) -> None:
        if not self.watch_path:
            return
        try:
            children = list(Path(self.watch_path).iterdir())
        except OSError as exc:
            self.status_var.set(f"폴더에 접근할 수 없습니다: {exc}")
            return
        current = {str(child) for child in children if child.is_dir()}
        for removed in self.known - current:
            self.pending.pop(removed, None)
        for folder in current:
            try:
                info = os.stat(folder)
                signature = (info.st_mtime_ns, info.st_size)
            except OSError:
                continue
            if folder in self.known:
                continue
            previous = self.pending.get(folder)
            stable = STABLE_POLLS if initial else ((previous[1] + 1) if previous and previous[0] == signature else 1)
            self.pending[folder] = (signature, stable)
            if stable >= STABLE_POLLS:
                self.pending.pop(folder, None)
                self.known.add(folder)
                self._add_project(folder, announce=not initial)
        # The first scan seeds the known set; later scans announce only new folders.

    def _add_project(self, folder: str, announce: bool) -> None:
        title = Path(folder).name
        detected_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        self.projects.insert("", 0, values=(detected_at, f"{title}  —  {folder}"))
        while len(self.projects.get_children()) > MAX_PROJECTS:
            self.projects.delete(self.projects.get_children()[-1])
        if announce:
            self.banner.configure(text=f"새 프로젝트\n{title}")
            if self.banner_after:
                self.root.after_cancel(self.banner_after)
            self.banner_after = self.root.after(10000, lambda: self.banner.configure(text="새 프로젝트가 감지되면 여기에 제목이 표시됩니다"))
            self.root.bell()
            self.status_var.set(f"새 프로젝트 감지 · {title}")

    def _poll(self) -> None:
        self._scan()
        self.root.after(POLL_MS, self._poll)


def main() -> None:
    root = tk.Tk()
    FolderWatcherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
