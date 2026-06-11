from __future__ import annotations

import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from .builder import build_export, inspect_export
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
        self.date_from = tk.StringVar()
        self.date_to = tk.StringVar()
        self.auto_open = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value=self.text["ready"])
        self.preview = tk.StringVar(value="")
        self.progress = tk.IntVar(value=0)
        self.generated_index: Path | None = None
        self.generated_current_page = False
        self.build_ui()
        self.zip_path.trace_add("write", lambda *_args: self.mark_inputs_changed())
        self.output_path.trace_add("write", lambda *_args: self.mark_inputs_changed())
        self.owner.trace_add("write", lambda *_args: self.mark_inputs_changed())
        self.date_from.trace_add("write", lambda *_args: self.mark_inputs_changed())
        self.date_to.trace_add("write", lambda *_args: self.mark_inputs_changed())
        self.update_generate_state()

    def tr(self, key: str) -> str:
        return self.text.get(key, key)

    def build_ui(self) -> None:
        self.root.title(self.tr("app_title"))
        self.root.geometry("900x720")
        self.root.minsize(760, 640)
        self.root.configure(bg="#eaf4ef")
        self.configure_styles()

        shell = tk.Frame(self.root, bg="#f7f8f7", highlightbackground="#d6e2de", highlightthickness=1)
        shell.pack(fill=tk.BOTH, expand=True, padx=28, pady=28)

        header = tk.Frame(shell, bg="#075e54", height=86)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        controls = tk.Frame(header, bg="#075e54")
        controls.pack(side=tk.LEFT, padx=(28, 18))
        for index, color in enumerate(("#c7dddd", "#9fc0bb", "#729994")):
            dot = tk.Canvas(controls, width=18, height=18, bg="#075e54", highlightthickness=0)
            dot.create_oval(3, 3, 15, 15, fill=color, outline=color)
            dot.grid(row=0, column=index, padx=4)
        tk.Label(header, text=self.tr("app_title"), bg="#075e54", fg="white", font=("TkDefaultFont", 24, "bold")).pack(side=tk.LEFT)

        frame = tk.Frame(shell, bg="#f7f8f7", padx=34, pady=28)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)

        self.labels: dict[str, ttk.Label] = {}
        self.buttons: dict[str, ttk.Button] = {}
        self.date_format_labels: list[ttk.Label] = []
        row = 0

        self.labels["zip_file"] = self.form_label(frame, self.tr("zip_file"), row, 0)
        ttk.Entry(frame, textvariable=self.zip_path, style="App.TEntry").grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 16), ipady=10)
        self.buttons["choose_zip"] = ttk.Button(frame, text=self.tr("choose_zip"), command=self.choose_zip)
        self.buttons["choose_zip"].grid(row=row + 1, column=2, padx=(12, 0), pady=(0, 16), sticky=tk.NS)
        row += 2

        self.labels["output_folder"] = self.form_label(frame, self.tr("output_folder"), row, 0)
        ttk.Entry(frame, textvariable=self.output_path, style="App.TEntry").grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 16), ipady=10)
        self.buttons["choose_output"] = ttk.Button(frame, text=self.tr("choose_output"), command=self.choose_output)
        self.buttons["choose_output"].grid(row=row + 1, column=2, padx=(12, 0), pady=(0, 16), sticky=tk.NS)
        row += 2

        self.labels["owner"] = self.form_label(frame, self.tr("owner"), row, 0)
        self.owner_box = ttk.Combobox(frame, textvariable=self.owner, values=[], state="disabled", style="App.TCombobox")
        self.owner_box.grid(row=row + 1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 16), ipady=8)
        self.owner_box.bind("<<ComboboxSelected>>", lambda _event: self.update_generate_state())
        row += 2

        self.labels["language"] = self.form_label(frame, self.tr("language"), row, 0)
        language_box = ttk.Combobox(frame, textvariable=self.language, values=SUPPORTED_LANGUAGES, state="readonly", style="App.TCombobox")
        language_box.grid(row=row + 1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 16), ipady=8)
        language_box.bind("<<ComboboxSelected>>", lambda _event: self.change_language())
        row += 2

        dates = tk.Frame(frame, bg="#f7f8f7")
        dates.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 18))
        dates.columnconfigure(0, weight=1)
        dates.columnconfigure(1, weight=1)
        date_from_box = tk.Frame(dates, bg="#f7f8f7")
        date_from_box.grid(row=0, column=0, sticky=tk.EW, padx=(0, 10))
        date_to_box = tk.Frame(dates, bg="#f7f8f7")
        date_to_box.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        self.labels["date_from"] = self.form_label(date_from_box, self.tr("date_from"), 0, 0)
        ttk.Entry(date_from_box, textvariable=self.date_from, style="App.TEntry").grid(row=1, column=0, sticky=tk.EW, pady=(0, 4), ipady=10)
        date_from_format = ttk.Label(date_from_box, text=self.tr("date_format"), style="Hint.TLabel")
        date_from_format.grid(row=2, column=0, sticky=tk.W)
        self.date_format_labels.append(date_from_format)
        date_from_box.columnconfigure(0, weight=1)
        self.labels["date_to"] = self.form_label(date_to_box, self.tr("date_to"), 0, 0)
        ttk.Entry(date_to_box, textvariable=self.date_to, style="App.TEntry").grid(row=1, column=0, sticky=tk.EW, pady=(0, 4), ipady=10)
        date_to_format = ttk.Label(date_to_box, text=self.tr("date_format"), style="Hint.TLabel")
        date_to_format.grid(row=2, column=0, sticky=tk.W)
        self.date_format_labels.append(date_to_format)
        date_to_box.columnconfigure(0, weight=1)
        row += 1

        self.preview_card = tk.Frame(frame, bg="white", highlightbackground="#d8e8e5", highlightthickness=1, padx=18, pady=14)
        self.preview_card.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 18))
        self.preview_label = tk.Label(self.preview_card, textvariable=self.preview, justify=tk.LEFT, wraplength=760, bg="white", fg="#5f6f69", font=("TkDefaultFont", 13))
        self.preview_label.pack(fill=tk.X)
        row += 1

        self.check_auto_open = ttk.Checkbutton(frame, text=self.tr("auto_open"), variable=self.auto_open, style="App.TCheckbutton")
        self.check_auto_open.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 14))
        row += 1

        self.progress_bar = ttk.Progressbar(frame, variable=self.progress, maximum=5, mode="determinate", style="App.Horizontal.TProgressbar")
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 20))
        row += 1

        actions = tk.Frame(frame, bg="#f7f8f7")
        actions.grid(row=row, column=0, columnspan=3, sticky=tk.E, pady=(0, 16))
        self.buttons["generate"] = ttk.Button(actions, text=self.tr("generate"), command=self.generate, style="Primary.TButton")
        self.buttons["generate"].pack(side=tk.LEFT, ipadx=18, ipady=8)
        self.buttons["open_output"] = ttk.Button(actions, text=self.tr("open_output"), command=self.open_output, style="Secondary.TButton")
        self.buttons["open_browser"] = ttk.Button(actions, text=self.tr("open_browser"), command=self.open_browser, style="Secondary.TButton")
        row += 1

        ttk.Label(frame, textvariable=self.status, style="Hint.TLabel").grid(row=row, column=0, columnspan=3, sticky=tk.W)

    def configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("TkDefaultFont", 13), background="#f7f8f7", foreground="#12211c")
        style.configure("TLabel", background="#f7f8f7", foreground="#5f6f69", font=("TkDefaultFont", 15, "bold"))
        style.configure("Hint.TLabel", background="#f7f8f7", foreground="#5f6f69", font=("TkDefaultFont", 11))
        style.configure("App.TEntry", fieldbackground="white", foreground="#12211c", bordercolor="#d7dedb", lightcolor="#d7dedb", darkcolor="#d7dedb", borderwidth=1, relief="flat", padding=(12, 8), font=("TkDefaultFont", 16, "bold"))
        style.configure("App.TCombobox", fieldbackground="white", foreground="#12211c", bordercolor="#d7dedb", arrowcolor="#5f6f69", padding=(12, 8), font=("TkDefaultFont", 16, "bold"))
        style.configure("App.TCheckbutton", background="#f7f8f7", foreground="#5f6f69", font=("TkDefaultFont", 12))
        style.configure("Primary.TButton", background="#075e54", foreground="white", bordercolor="#075e54", focusthickness=0, padding=(18, 10), font=("TkDefaultFont", 18, "bold"))
        style.map("Primary.TButton", background=[("disabled", "#9bb5af"), ("active", "#0a7668")], foreground=[("disabled", "#edf4f1")])
        style.configure("Secondary.TButton", background="white", foreground="#075e54", bordercolor="#c9d9d6", padding=(16, 10), font=("TkDefaultFont", 15))
        style.map("Secondary.TButton", background=[("active", "#f0f7f4")])
        style.configure("TButton", padding=(12, 8), font=("TkDefaultFont", 12, "bold"))
        style.configure("App.Horizontal.TProgressbar", troughcolor="#d9e5e1", background="#00a884", bordercolor="#d9e5e1", lightcolor="#00a884", darkcolor="#00a884")

    def form_label(self, parent: tk.Widget, text: str, row: int, column: int) -> ttk.Label:
        label = ttk.Label(parent, text=text)
        label.grid(row=row, column=column, sticky=tk.W, pady=(0, 8))
        return label

    def hide_generated_actions(self) -> None:
        self.buttons["open_output"].pack_forget()
        self.buttons["open_browser"].pack_forget()

    def show_generated_actions(self) -> None:
        self.buttons["open_output"].pack(side=tk.LEFT, padx=(8, 0))
        self.buttons["open_browser"].pack(side=tk.LEFT, padx=(8, 0))

    def mark_inputs_changed(self) -> None:
        self.generated_current_page = False
        self.generated_index = None
        self.hide_generated_actions()
        self.update_generate_state()

    def update_generate_state(self) -> None:
        if "generate" not in self.buttons:
            return
        ready = bool(self.zip_path.get() and self.output_path.get() and self.owner.get() and not self.generated_current_page)
        self.buttons["generate"].configure(state=tk.NORMAL if ready else tk.DISABLED)

    def change_language(self) -> None:
        self.text = load_translations(self.language.get())
        self.root.title(self.tr("app_title"))
        for key, label in self.labels.items():
            label.configure(text=self.tr(key))
        for key, button in self.buttons.items():
            button.configure(text=self.tr(key))
        for label in self.date_format_labels:
            label.configure(text=self.tr("date_format"))
        self.check_auto_open.configure(text=self.tr("auto_open"))
        if self.status.get() in {"Ready.", "Pronto.", "Listo."}:
            self.status.set(self.tr("ready"))
        self.generated_current_page = False
        self.generated_index = None
        self.hide_generated_actions()
        self.update_generate_state()

    def choose_zip(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("WhatsApp ZIP", "*.zip"), ("All files", "*.*")])
        if path:
            self.zip_path.set(path)
            self.owner.set("")
            self.preview.set("")
            self.progress.set(0)
            self.generated_index = None
            self.hide_generated_actions()
            self.owner_box.configure(values=[], state="disabled")
            self.status.set(self.tr("loading_preview"))
            if not self.output_path.get():
                self.output_path.set(str(Path(path).with_suffix("")))
            thread = threading.Thread(target=self._load_participants_worker, args=(Path(path),), daemon=True)
            thread.start()

    def _load_participants_worker(self, zip_path: Path) -> None:
        try:
            preview = inspect_export(zip_path)
        except Exception as exc:  # pragma: no cover - UI surface
            self.root.after(0, lambda: self._participants_failed(exc))
            return
        self.root.after(0, lambda: self._participants_loaded(zip_path, preview))

    def _participants_loaded(self, zip_path: Path, preview: dict[str, object]) -> None:
        if Path(self.zip_path.get()) != zip_path:
            return
        participants = list(preview.get("participants", []))
        self.owner_box.configure(values=participants, state="readonly" if participants else "disabled")
        media = preview.get("media", {})
        media_counts = media if isinstance(media, dict) else {}
        self.preview.set(
            self.tr("preview_template").format(
                total=preview.get("total_messages", 0),
                first=preview.get("first_date", "-") or "-",
                last=preview.get("last_date", "-") or "-",
                participants=len(participants),
                images=media_counts.get("images", 0),
                videos=media_counts.get("videos", 0),
                audios=media_counts.get("audios", 0),
                documents=media_counts.get("documents", 0),
            )
        )
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
            self.progress.set(0)
            self.generated_index = None
            self.hide_generated_actions()

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
        self.progress.set(0)
        self.status.set(self.tr("generate") + "...")
        thread = threading.Thread(target=self._generate_worker, daemon=True)
        thread.start()

    def _progress(self, step: int, message: str) -> None:
        self.root.after(0, lambda: self._set_progress(step, message))

    def _set_progress(self, step: int, message: str) -> None:
        self.progress.set(step)
        self.status.set(self.tr("progress_template").format(step=step, total=5, message=self.tr(message)))

    def _generate_worker(self) -> None:
        try:
            build_export(
                Path(self.zip_path.get()),
                Path(self.output_path.get()),
                owner=self.owner.get() or None,
                language=self.language.get(),
                date_from=self.date_from.get() or None,
                date_to=self.date_to.get() or None,
                progress_callback=self._progress,
            )
        except Exception as exc:  # pragma: no cover - UI surface
            self.root.after(0, lambda: self._generation_failed(exc))
            return
        self.root.after(0, self._generation_succeeded)

    def _generation_succeeded(self) -> None:
        self.generated_index = Path(self.output_path.get()).expanduser() / "index.html"
        self.generated_current_page = True
        self.progress.set(5)
        self.show_generated_actions()
        self.status.set(self.tr("success"))
        self.update_generate_state()
        if self.auto_open.get():
            self.open_browser()

    def _generation_failed(self, exc: Exception) -> None:
        self.generated_index = None
        self.generated_current_page = False
        self.progress.set(0)
        self.hide_generated_actions()
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
