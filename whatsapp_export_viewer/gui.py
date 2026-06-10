from __future__ import annotations

import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from .builder import build_export, discover_participants
from .i18n import SUPPORTED_LANGUAGES, load_translations, normalize_language, system_language

tk = None
ttk = None
filedialog = None
messagebox = None


def load_tkinter() -> bool:
    global tk, ttk, filedialog, messagebox
    try:
        import tkinter as tk_module
        from tkinter import filedialog as filedialog_module
        from tkinter import messagebox as messagebox_module
        from tkinter import ttk as ttk_module
    except ModuleNotFoundError:
        return False
    tk = tk_module
    ttk = ttk_module
    filedialog = filedialog_module
    messagebox = messagebox_module
    return True


class ViewerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language = tk.StringVar(value=system_language())
        self.text = load_translations(self.language.get())
        self.zip_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.owner = tk.StringVar()
        self.status = tk.StringVar(value=self.text["ready"])
        self.generated_index: Path | None = None
        self.build_ui()
        self.zip_path.trace_add("write", lambda *_args: self.update_generate_state())
        self.output_path.trace_add("write", lambda *_args: self.update_generate_state())
        self.owner.trace_add("write", lambda *_args: self.update_generate_state())
        self.update_generate_state()

    def tr(self, key: str) -> str:
        return self.text.get(key, key)

    def build_ui(self) -> None:
        self.root.title(self.tr("app_title"))
        self.root.geometry("720x420")
        self.root.minsize(620, 360)

        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        self.labels: dict[str, ttk.Label] = {}
        self.buttons: dict[str, ttk.Button] = {}
        row = 0

        self.labels["language"] = ttk.Label(frame, text=self.tr("language"))
        self.labels["language"].grid(row=row, column=0, sticky=tk.W, pady=6)
        language_box = ttk.Combobox(frame, textvariable=self.language, values=SUPPORTED_LANGUAGES, state="readonly")
        language_box.grid(row=row, column=1, sticky=tk.EW, pady=6)
        language_box.bind("<<ComboboxSelected>>", lambda _event: self.change_language())
        row += 1

        self.labels["zip_file"] = ttk.Label(frame, text=self.tr("zip_file"))
        self.labels["zip_file"].grid(row=row, column=0, sticky=tk.W, pady=6)
        ttk.Entry(frame, textvariable=self.zip_path).grid(row=row, column=1, sticky=tk.EW, pady=6)
        self.buttons["choose_zip"] = ttk.Button(frame, text=self.tr("choose_zip"), command=self.choose_zip)
        self.buttons["choose_zip"].grid(row=row, column=2, padx=(8, 0), pady=6)
        row += 1

        self.labels["output_folder"] = ttk.Label(frame, text=self.tr("output_folder"))
        self.labels["output_folder"].grid(row=row, column=0, sticky=tk.W, pady=6)
        ttk.Entry(frame, textvariable=self.output_path).grid(row=row, column=1, sticky=tk.EW, pady=6)
        self.buttons["choose_output"] = ttk.Button(frame, text=self.tr("choose_output"), command=self.choose_output)
        self.buttons["choose_output"].grid(row=row, column=2, padx=(8, 0), pady=6)
        row += 1

        self.labels["owner"] = ttk.Label(frame, text=self.tr("owner"))
        self.labels["owner"].grid(row=row, column=0, sticky=tk.W, pady=6)
        self.owner_box = ttk.Combobox(frame, textvariable=self.owner, values=[], state="disabled")
        self.owner_box.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=6)
        self.owner_box.bind("<<ComboboxSelected>>", lambda _event: self.update_generate_state())
        row += 1

        actions = ttk.Frame(frame)
        actions.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(18, 8))
        self.buttons["generate"] = ttk.Button(actions, text=self.tr("generate"), command=self.generate)
        self.buttons["generate"].pack(side=tk.LEFT)
        self.buttons["open_output"] = ttk.Button(actions, text=self.tr("open_output"), command=self.open_output)
        self.buttons["open_output"].pack(side=tk.LEFT, padx=(8, 0))
        self.buttons["open_browser"] = ttk.Button(actions, text=self.tr("open_browser"), command=self.open_browser, state=tk.DISABLED)
        self.buttons["open_browser"].pack(side=tk.LEFT, padx=(8, 0))
        row += 1

        ttk.Label(frame, textvariable=self.status).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=6)

    def update_generate_state(self) -> None:
        if "generate" not in self.buttons:
            return
        ready = bool(self.zip_path.get() and self.output_path.get() and self.owner.get())
        self.buttons["generate"].configure(state=tk.NORMAL if ready else tk.DISABLED)

    def change_language(self) -> None:
        self.text = load_translations(self.language.get())
        self.root.title(self.tr("app_title"))
        for key, label in self.labels.items():
            label.configure(text=self.tr(key))
        for key, button in self.buttons.items():
            button.configure(text=self.tr(key))
        if self.status.get() in {"Ready.", "Pronto.", "Listo."}:
            self.status.set(self.tr("ready"))

    def choose_zip(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("WhatsApp ZIP", "*.zip"), ("All files", "*.*")])
        if path:
            self.zip_path.set(path)
            self.owner.set("")
            self.generated_index = None
            self.buttons["open_browser"].configure(state=tk.DISABLED)
            self.owner_box.configure(values=[], state="disabled")
            self.status.set(self.tr("loading_participants"))
            if not self.output_path.get():
                self.output_path.set(str(Path(path).with_suffix("")))
            thread = threading.Thread(target=self._load_participants_worker, args=(Path(path),), daemon=True)
            thread.start()

    def _load_participants_worker(self, zip_path: Path) -> None:
        try:
            participants = discover_participants(zip_path)
        except Exception as exc:  # pragma: no cover - UI surface
            self.root.after(0, lambda: self._participants_failed(exc))
            return
        self.root.after(0, lambda: self._participants_loaded(zip_path, participants))

    def _participants_loaded(self, zip_path: Path, participants: list[str]) -> None:
        if Path(self.zip_path.get()) != zip_path:
            return
        self.owner_box.configure(values=participants, state="readonly" if participants else "disabled")
        if participants:
            self.status.set(self.tr("select_owner"))
        else:
            self.status.set(self.tr("no_participants"))
        self.update_generate_state()

    def _participants_failed(self, exc: Exception) -> None:
        self.owner.set("")
        self.owner_box.configure(values=[], state="disabled")
        self.status.set(f"{self.tr('error')}: {exc}")
        messagebox.showerror(self.tr("app_title"), f"{self.tr('error')}:\n{exc}")
        self.update_generate_state()

    def choose_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_path.set(path)
            self.generated_index = None
            self.buttons["open_browser"].configure(state=tk.DISABLED)

    def generate(self) -> None:
        if not self.zip_path.get():
            messagebox.showwarning(self.tr("app_title"), self.tr("missing_zip"))
            return
        if not self.output_path.get():
            messagebox.showwarning(self.tr("app_title"), self.tr("missing_output"))
            return
        if not self.owner.get():
            messagebox.showwarning(self.tr("app_title"), self.tr("missing_owner"))
            return
        self.buttons["generate"].configure(state=tk.DISABLED)
        self.status.set(self.tr("generate") + "...")
        thread = threading.Thread(target=self._generate_worker, daemon=True)
        thread.start()

    def _generate_worker(self) -> None:
        try:
            build_export(
                Path(self.zip_path.get()),
                Path(self.output_path.get()),
                owner=self.owner.get() or None,
                language=self.language.get(),
            )
        except Exception as exc:  # pragma: no cover - UI surface
            self.root.after(0, lambda: self._generation_failed(exc))
            return
        self.root.after(0, self._generation_succeeded)

    def _generation_succeeded(self) -> None:
        self.generated_index = Path(self.output_path.get()).expanduser() / "index.html"
        self.buttons["open_browser"].configure(state=tk.NORMAL)
        self.status.set(self.tr("success"))
        self.update_generate_state()

    def _generation_failed(self, exc: Exception) -> None:
        self.generated_index = None
        self.buttons["open_browser"].configure(state=tk.DISABLED)
        self.status.set(f"{self.tr('error')}: {exc}")
        messagebox.showerror(self.tr("app_title"), f"{self.tr('error')}:\n{exc}")
        self.update_generate_state()

    def open_output(self) -> None:
        path = self.output_path.get()
        if not path:
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)

    def open_browser(self) -> None:
        if not self.generated_index:
            return
        webbrowser.open(self.generated_index.resolve().as_uri())


def main() -> int:
    if not load_tkinter():
        print("Tkinter is not available in this Python installation. Use the CLI or install a Python build with Tk support.", file=sys.stderr)
        return 1
    root = tk.Tk()
    ViewerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
