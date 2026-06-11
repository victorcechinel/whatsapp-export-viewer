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

BG = "#eaf4ef"
SURFACE = "#f7f8f7"
PANEL = "#ffffff"
GREEN = "#075e54"
GREEN_DARK = "#064d45"
TEXT = "#12211c"
MUTED = "#5f6f69"
LINE = "#d7e2de"
PROGRESS_BG = "#d9e5e1"
PROGRESS_FG = "#00a884"


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


class StyledSelect:
    def __init__(self, parent: tk.Widget, variable: tk.StringVar, values: list[str] | tuple[str, ...] | None = None, command=None) -> None:
        self.variable = variable
        self.command = command
        self.values = list(values or [])
        self.state = "normal"
        self.frame = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightcolor=GREEN, highlightthickness=1)
        self.label = tk.Label(self.frame, textvariable=self.variable, anchor=tk.W, bg=PANEL, fg=TEXT, font=("TkDefaultFont", 15, "bold"), padx=14)
        self.label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=12)
        self.arrow = tk.Label(self.frame, text="v", bg=PANEL, fg=MUTED, font=("TkDefaultFont", 13, "bold"), width=3)
        self.arrow.pack(side=tk.RIGHT, fill=tk.Y)
        self.menu = tk.Menu(self.frame, tearoff=0, bg=PANEL, fg=TEXT, activebackground="#eef6f2", activeforeground=TEXT, borderwidth=0, font=("TkDefaultFont", 13))
        for widget in (self.frame, self.label, self.arrow):
            widget.bind("<Button-1>", self.open_menu)
            widget.configure(cursor="hand2")
        self.set_values(self.values)

    def grid(self, *args, **kwargs) -> None:
        self.frame.grid(*args, **kwargs)

    def configure(self, **kwargs) -> None:
        if "values" in kwargs:
            self.set_values(list(kwargs.pop("values")))
        if "state" in kwargs:
            self.set_state(kwargs.pop("state"))
        if kwargs:
            self.frame.configure(**kwargs)

    def bind(self, *_args, **_kwargs) -> None:
        return None

    def set_values(self, values: list[str]) -> None:
        self.values = values
        self.menu.delete(0, tk.END)
        for value in self.values:
            self.menu.add_command(label=value, command=lambda item=value: self.select(item))

    def set_state(self, state: str) -> None:
        self.state = state
        disabled = state == "disabled"
        background = "#eef2ef" if disabled else PANEL
        foreground = "#9aa7a2" if disabled else TEXT
        arrow_foreground = "#9aa7a2" if disabled else MUTED
        cursor = "arrow" if disabled else "hand2"
        for widget in (self.frame, self.label, self.arrow):
            widget.configure(cursor=cursor)
        self.frame.configure(bg=background, highlightbackground=LINE)
        self.label.configure(bg=background, fg=foreground)
        self.arrow.configure(bg=background, fg=arrow_foreground)

    def select(self, value: str) -> None:
        self.variable.set(value)
        if self.command:
            self.command()

    def open_menu(self, _event=None) -> None:
        if self.state == "disabled" or not self.values:
            return
        self.menu.tk_popup(self.frame.winfo_rootx(), self.frame.winfo_rooty() + self.frame.winfo_height())


class StyledEntry:
    def __init__(self, parent: tk.Widget, variable: tk.StringVar) -> None:
        self.frame = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightcolor=GREEN, highlightthickness=1)
        self.entry = tk.Entry(
            self.frame,
            textvariable=variable,
            bg=PANEL,
            fg=TEXT,
            insertbackground=TEXT,
            relief=tk.FLAT,
            borderwidth=0,
            font=("TkDefaultFont", 15),
        )
        self.entry.pack(fill=tk.BOTH, expand=True, padx=14, pady=13)

    def grid(self, *args, **kwargs) -> None:
        self.frame.grid(*args, **kwargs)


class StyledButton:
    def __init__(self, parent: tk.Widget, text: str, command, variant: str = "secondary") -> None:
        self.command = command
        self.variant = variant
        self.state = tk.NORMAL
        self.colors = self._colors(variant)
        self.frame = tk.Frame(parent, bg=self.colors["bg"], highlightbackground=self.colors["border"], highlightthickness=1 if variant == "secondary" else 0)
        self.label = tk.Label(
            self.frame,
            text=text,
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            font=("TkDefaultFont", 20 if variant == "primary" else 13, "bold"),
            padx=36 if variant == "primary" else 18,
            pady=16 if variant == "primary" else 12,
        )
        self.label.pack(fill=tk.BOTH, expand=True)
        for widget in (self.frame, self.label):
            widget.bind("<Button-1>", self.click)
            widget.bind("<Enter>", lambda _event: self.set_hover(True))
            widget.bind("<Leave>", lambda _event: self.set_hover(False))
            widget.configure(cursor="hand2")

    def _colors(self, variant: str) -> dict[str, str]:
        if variant == "primary":
            return {"bg": GREEN, "fg": "white", "active": GREEN_DARK, "disabled": "#9bb5af", "border": GREEN}
        return {"bg": PANEL, "fg": GREEN, "active": "#eef6f2", "disabled": "#edf4f1", "border": "#c9d9d6"}

    def grid(self, *args, **kwargs) -> None:
        self.frame.grid(*args, **kwargs)

    def pack(self, *args, **kwargs) -> None:
        self.frame.pack(*args, **kwargs)

    def pack_forget(self) -> None:
        self.frame.pack_forget()

    def configure(self, **kwargs) -> None:
        if "text" in kwargs:
            self.label.configure(text=kwargs.pop("text"))
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            disabled = self.state == tk.DISABLED
            background = self.colors["disabled"] if disabled else self.colors["bg"]
            foreground = "#edf4f1" if self.variant == "primary" and disabled else self.colors["fg"]
            self.frame.configure(bg=background)
            self.label.configure(bg=background, fg=foreground)
            for widget in (self.frame, self.label):
                widget.configure(cursor="arrow" if disabled else "hand2")
        if kwargs:
            self.frame.configure(**kwargs)

    def set_hover(self, active: bool) -> None:
        if self.state == tk.DISABLED:
            return
        background = self.colors["active"] if active else self.colors["bg"]
        self.frame.configure(bg=background)
        self.label.configure(bg=background)

    def click(self, _event=None) -> None:
        if self.state != tk.DISABLED:
            self.command()


class StyledProgress:
    def __init__(self, parent: tk.Widget, variable: tk.IntVar, maximum: int) -> None:
        self.variable = variable
        self.maximum = maximum
        self.track = tk.Frame(parent, bg=PROGRESS_BG, height=14)
        self.fill = tk.Frame(self.track, bg=PROGRESS_FG, height=14)
        self.variable.trace_add("write", lambda *_args: self.update())
        self.track.bind("<Configure>", lambda _event: self.update())

    def grid(self, *args, **kwargs) -> None:
        self.track.grid(*args, **kwargs)
        self.track.grid_propagate(False)
        self.update()

    def update(self) -> None:
        width = self.track.winfo_width()
        if width <= 1:
            self.track.after(10, self.update)
            return
        ratio = max(0, min(self.variable.get(), self.maximum)) / self.maximum
        self.fill.place(x=0, y=0, width=int(width * ratio), relheight=1)


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
        self.root.geometry("1040x780")
        self.root.minsize(940, 700)
        self.root.configure(bg=BG)
        self.configure_styles()

        shell = tk.Frame(self.root, bg=SURFACE, highlightbackground="#d6e2de", highlightthickness=1)
        shell.pack(fill=tk.BOTH, expand=True, padx=34, pady=30)

        header = tk.Frame(shell, bg=GREEN, height=94)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        controls = tk.Frame(header, bg=GREEN)
        controls.pack(side=tk.LEFT, padx=(40, 24))
        for index, color in enumerate(("#c7dddd", "#9fc0bb", "#729994")):
            dot = tk.Canvas(controls, width=20, height=20, bg=GREEN, highlightthickness=0)
            dot.create_oval(3, 3, 17, 17, fill=color, outline=color)
            dot.grid(row=0, column=index, padx=5)
        tk.Label(header, text=self.tr("app_title"), bg=GREEN, fg="white", font=("TkDefaultFont", 30, "bold")).pack(side=tk.LEFT)

        frame = tk.Frame(shell, bg=SURFACE, padx=42, pady=34)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)

        self.labels: dict[str, tk.Label] = {}
        self.buttons: dict[str, StyledButton] = {}
        self.date_format_labels: list[tk.Label] = []
        row = 0

        self.labels["zip_file"] = self.form_label(frame, self.tr("zip_file"), row, 0)
        self.entry(frame, self.zip_path).grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 16))
        self.buttons["choose_zip"] = self.secondary_button(frame, self.tr("choose_zip"), self.choose_zip)
        self.buttons["choose_zip"].grid(row=row + 1, column=2, padx=(12, 0), pady=(0, 16), sticky=tk.NS)
        row += 2

        self.labels["output_folder"] = self.form_label(frame, self.tr("output_folder"), row, 0)
        self.entry(frame, self.output_path).grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 16))
        self.buttons["choose_output"] = self.secondary_button(frame, self.tr("choose_output"), self.choose_output)
        self.buttons["choose_output"].grid(row=row + 1, column=2, padx=(12, 0), pady=(0, 16), sticky=tk.NS)
        row += 2

        self.labels["owner"] = self.form_label(frame, self.tr("owner"), row, 0)
        self.owner_box = StyledSelect(frame, self.owner, [], command=self.update_generate_state)
        self.owner_box.configure(state="disabled")
        self.owner_box.grid(row=row + 1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 16))
        row += 2

        self.labels["language"] = self.form_label(frame, self.tr("language"), row, 0)
        self.language_box = StyledSelect(frame, self.language, SUPPORTED_LANGUAGES, command=self.change_language)
        self.language_box.grid(row=row + 1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 16))
        row += 2

        dates = tk.Frame(frame, bg=SURFACE)
        dates.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 18))
        dates.columnconfigure(0, weight=1)
        dates.columnconfigure(1, weight=1)
        date_from_box = tk.Frame(dates, bg=SURFACE)
        date_from_box.grid(row=0, column=0, sticky=tk.EW, padx=(0, 12))
        date_to_box = tk.Frame(dates, bg=SURFACE)
        date_to_box.grid(row=0, column=1, sticky=tk.EW, padx=(12, 0))
        self.labels["date_from"] = self.form_label(date_from_box, self.tr("date_from"), 0, 0)
        self.entry(date_from_box, self.date_from).grid(row=1, column=0, sticky=tk.EW, pady=(0, 6))
        date_from_format = self.hint_label(date_from_box, self.tr("date_format"))
        date_from_format.grid(row=2, column=0, sticky=tk.W)
        self.date_format_labels.append(date_from_format)
        date_from_box.columnconfigure(0, weight=1)
        self.labels["date_to"] = self.form_label(date_to_box, self.tr("date_to"), 0, 0)
        self.entry(date_to_box, self.date_to).grid(row=1, column=0, sticky=tk.EW, pady=(0, 6))
        date_to_format = self.hint_label(date_to_box, self.tr("date_format"))
        date_to_format.grid(row=2, column=0, sticky=tk.W)
        self.date_format_labels.append(date_to_format)
        date_to_box.columnconfigure(0, weight=1)
        row += 1

        self.preview_card = tk.Frame(frame, bg=PANEL, highlightbackground="#d8e8e5", highlightthickness=1, padx=20, pady=16)
        self.preview_card.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 18))
        self.preview_label = tk.Label(self.preview_card, textvariable=self.preview, justify=tk.LEFT, anchor=tk.W, wraplength=820, bg=PANEL, fg=MUTED, font=("TkDefaultFont", 15))
        self.preview_label.pack(fill=tk.X)
        row += 1

        self.check_auto_open = tk.Checkbutton(frame, text=self.tr("auto_open"), variable=self.auto_open, bg=SURFACE, fg=MUTED, activebackground=SURFACE, activeforeground=TEXT, selectcolor=PANEL, font=("TkDefaultFont", 13), borderwidth=0, highlightthickness=0)
        self.check_auto_open.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 14))
        row += 1

        self.progress_bar = StyledProgress(frame, self.progress, maximum=5)
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 20))
        row += 1

        actions = tk.Frame(frame, bg=SURFACE)
        actions.grid(row=row, column=0, columnspan=3, sticky=tk.E, pady=(0, 16))
        self.buttons["generate"] = self.primary_button(actions, self.tr("generate"), self.generate)
        self.buttons["generate"].pack(side=tk.LEFT)
        self.buttons["open_output"] = self.secondary_button(actions, self.tr("open_output"), self.open_output)
        self.buttons["open_browser"] = self.secondary_button(actions, self.tr("open_browser"), self.open_browser)
        row += 1

        tk.Label(frame, textvariable=self.status, bg=SURFACE, fg=MUTED, anchor=tk.W, font=("TkDefaultFont", 12)).grid(row=row, column=0, columnspan=3, sticky=tk.W)

    def configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")

    def entry(self, parent: tk.Widget, variable: tk.StringVar) -> StyledEntry:
        return StyledEntry(parent, variable)

    def primary_button(self, parent: tk.Widget, text: str, command) -> StyledButton:
        return StyledButton(parent, text, command, variant="primary")

    def secondary_button(self, parent: tk.Widget, text: str, command) -> StyledButton:
        return StyledButton(parent, text, command, variant="secondary")

    def form_label(self, parent: tk.Widget, text: str, row: int, column: int) -> tk.Label:
        label = tk.Label(parent, text=text, bg=SURFACE, fg=MUTED, font=("TkDefaultFont", 16, "bold"))
        label.grid(row=row, column=column, sticky=tk.W, pady=(0, 8))
        return label

    def hint_label(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(parent, text=text, bg=SURFACE, fg=MUTED, font=("TkDefaultFont", 11))

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
