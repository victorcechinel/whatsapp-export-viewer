from __future__ import annotations

import os
import subprocess
import sys
import threading
import webbrowser
from calendar import Calendar, month_name
from datetime import date, datetime
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
FONT_FAMILY = "TkDefaultFont"


def format_gui_date(value: date, language: str) -> str:
    return value.strftime("%m/%d/%Y") if normalize_language(language) == "en" else value.strftime("%d/%m/%Y")


def parse_gui_date(value: str, language: str) -> date:
    fmt = "%m/%d/%Y" if normalize_language(language) == "en" else "%d/%m/%Y"
    return datetime.strptime(value, fmt).date()


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
        self.popup: tk.Toplevel | None = None
        self.frame = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightcolor=GREEN, highlightthickness=1)
        self.label = tk.Label(self.frame, textvariable=self.variable, anchor=tk.W, bg=PANEL, fg=TEXT, font=(FONT_FAMILY, 13, "bold"), padx=14)
        self.label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=10)
        self.arrow = tk.Label(self.frame, text="v", bg=PANEL, fg=MUTED, font=(FONT_FAMILY, 11, "bold"), width=3)
        self.arrow.pack(side=tk.RIGHT, fill=tk.Y)
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
        self.close_popup()

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
        self.close_popup()
        if self.command:
            self.command()

    def open_menu(self, _event=None) -> None:
        if self.state == "disabled" or not self.values:
            return
        if self.popup and self.popup.winfo_exists():
            self.close_popup()
            return
        self.popup = tk.Toplevel(self.frame)
        self.popup.overrideredirect(True)
        self.popup.configure(bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        self.popup.transient(self.frame.winfo_toplevel())
        width = self.frame.winfo_width()
        height = min(max(len(self.values), 1) * 42, 280)
        x = self.frame.winfo_rootx()
        y = self.frame.winfo_rooty() + self.frame.winfo_height() + 4
        self.popup.geometry(f"{width}x{height}+{x}+{y}")
        for index, value in enumerate(self.values):
            item = tk.Label(
                self.popup,
                text=value,
                bg="#eef6f2" if value == self.variable.get() else PANEL,
                fg=TEXT,
                anchor=tk.W,
                font=(FONT_FAMILY, 12, "bold" if value == self.variable.get() else "normal"),
                padx=14,
                pady=10,
            )
            item.pack(fill=tk.X)
            item.bind("<Button-1>", lambda _event, item_value=value: self.select(item_value))
            item.bind("<Enter>", lambda event: event.widget.configure(bg="#eef6f2"))
            item.bind("<Leave>", lambda event, item_value=value: event.widget.configure(bg="#eef6f2" if item_value == self.variable.get() else PANEL))
        self.popup.bind("<FocusOut>", lambda _event: self.close_popup())
        self.popup.focus_force()

    def close_popup(self) -> None:
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        self.popup = None


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
            highlightthickness=0,
            font=(FONT_FAMILY, 13),
        )
        self.entry.pack(fill=tk.BOTH, expand=True, padx=14, pady=11)

    def grid(self, *args, **kwargs) -> None:
        self.frame.grid(*args, **kwargs)


class DateInput:
    def __init__(self, parent: tk.Widget, variable: tk.StringVar, language_getter) -> None:
        self.variable = variable
        self.language_getter = language_getter
        self.frame = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightcolor=GREEN, highlightthickness=1)
        self.entry = tk.Entry(
            self.frame,
            textvariable=variable,
            bg=PANEL,
            fg=TEXT,
            insertbackground=TEXT,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            font=(FONT_FAMILY, 13),
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(14, 6), pady=11)
        self.button = tk.Label(self.frame, text="Cal", bg="#eef6f2", fg=GREEN, font=(FONT_FAMILY, 10, "bold"), padx=10, pady=7)
        self.button.pack(side=tk.RIGHT, padx=(0, 8))
        self.button.configure(cursor="hand2")
        self.button.bind("<Button-1>", self.open_picker)

    def grid(self, *args, **kwargs) -> None:
        self.frame.grid(*args, **kwargs)

    def open_picker(self, _event=None) -> None:
        selected = None
        try:
            selected = parse_gui_date(self.variable.get().strip(), self.language_getter())
        except ValueError:
            selected = date.today()
        CalendarPopup(self.frame, selected, self.language_getter, self.set_date)

    def set_date(self, value: date) -> None:
        self.variable.set(format_gui_date(value, self.language_getter()))


class CalendarPopup:
    def __init__(self, anchor: tk.Widget, initial: date, language_getter, command) -> None:
        self.anchor = anchor
        self.language_getter = language_getter
        self.command = command
        self.year = initial.year
        self.month = initial.month
        self.popup = tk.Toplevel(anchor)
        self.popup.overrideredirect(True)
        self.popup.configure(bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        self.popup.transient(anchor.winfo_toplevel())
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 4
        self.popup.geometry(f"300x330+{x}+{y}")
        self.body = tk.Frame(self.popup, bg=PANEL, padx=12, pady=12)
        self.body.pack(fill=tk.BOTH, expand=True)
        self.popup.bind("<FocusOut>", lambda _event: self.close())
        self.render()
        self.popup.focus_force()

    def render(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()
        header = tk.Frame(self.body, bg=PANEL)
        header.grid(row=0, column=0, columnspan=7, sticky=tk.EW, pady=(0, 8))
        StyledMiniButton(header, "<", self.previous_month).pack(side=tk.LEFT)
        tk.Label(
            header,
            text=f"{month_name[self.month]} {self.year}",
            bg=PANEL,
            fg=TEXT,
            font=(FONT_FAMILY, 12, "bold"),
        ).pack(side=tk.LEFT, expand=True)
        StyledMiniButton(header, ">", self.next_month).pack(side=tk.RIGHT)

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] if normalize_language(self.language_getter()) == "en" else ["Se", "Te", "Qa", "Qi", "Se", "Sa", "Do"]
        for column, weekday in enumerate(weekdays):
            tk.Label(self.body, text=weekday, bg=PANEL, fg=MUTED, font=(FONT_FAMILY, 9, "bold"), width=4).grid(row=1, column=column, pady=(0, 4))

        today = date.today()
        calendar = Calendar(firstweekday=0)
        for row_index, week in enumerate(calendar.monthdatescalendar(self.year, self.month), start=2):
            for column, day in enumerate(week):
                in_month = day.month == self.month
                bg = "#eef6f2" if day == today else PANEL
                fg = TEXT if in_month else "#a5b1ad"
                cell = tk.Label(self.body, text=str(day.day), bg=bg, fg=fg, width=4, height=2, font=(FONT_FAMILY, 10, "bold" if in_month else "normal"))
                cell.grid(row=row_index, column=column, padx=1, pady=1)
                cell.configure(cursor="hand2")
                cell.bind("<Button-1>", lambda _event, value=day: self.pick(value))
                cell.bind("<Enter>", lambda event: event.widget.configure(bg="#dff3ea"))
                cell.bind("<Leave>", lambda event, value=day: event.widget.configure(bg="#eef6f2" if value == today else PANEL))

    def previous_month(self) -> None:
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.render()

    def next_month(self) -> None:
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.render()

    def pick(self, value: date) -> None:
        self.command(value)
        self.close()

    def close(self) -> None:
        if self.popup.winfo_exists():
            self.popup.destroy()


class StyledMiniButton:
    def __init__(self, parent: tk.Widget, text: str, command) -> None:
        self.button = tk.Label(parent, text=text, bg="#eef6f2", fg=GREEN, width=3, font=(FONT_FAMILY, 11, "bold"))
        self.button.configure(cursor="hand2")
        self.button.bind("<Button-1>", lambda _event: command())
        self.button.bind("<Enter>", lambda event: event.widget.configure(bg="#dff3ea"))
        self.button.bind("<Leave>", lambda event: event.widget.configure(bg="#eef6f2"))

    def pack(self, *args, **kwargs) -> None:
        self.button.pack(*args, **kwargs)


class StyledButton:
    def __init__(self, parent: tk.Widget, text: str, command, variant: str = "secondary") -> None:
        self.command = command
        self.variant = variant
        self.state = tk.NORMAL
        self.text = text
        self.hover = False
        self.colors = self._colors(variant)
        self.width = self.measure_width(text)
        self.height = 58 if variant == "primary" else 48
        self.canvas = tk.Canvas(
            parent,
            width=self.width,
            height=self.height,
            bg=SURFACE,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Enter>", lambda _event: self.set_hover(True))
        self.canvas.bind("<Leave>", lambda _event: self.set_hover(False))
        self.canvas.configure(cursor="hand2")
        self.draw()

    def _colors(self, variant: str) -> dict[str, str]:
        if variant == "primary":
            return {"bg": GREEN, "fg": "white", "active": GREEN_DARK, "disabled": "#9bb5af", "border": GREEN}
        return {"bg": PANEL, "fg": GREEN, "active": "#eef6f2", "disabled": "#edf4f1", "border": "#c9d9d6"}

    def measure_width(self, text: str) -> int:
        if self.variant == "primary":
            return max(250, min(360, len(text) * 14 + 88))
        return max(180, min(280, len(text) * 8 + 56))

    def grid(self, *args, **kwargs) -> None:
        self.canvas.grid(*args, **kwargs)

    def pack(self, *args, **kwargs) -> None:
        self.canvas.pack(*args, **kwargs)

    def pack_forget(self) -> None:
        self.canvas.pack_forget()

    def configure(self, **kwargs) -> None:
        if "text" in kwargs:
            self.text = kwargs.pop("text")
            self.width = self.measure_width(self.text)
            self.canvas.configure(width=self.width)
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            disabled = self.state == tk.DISABLED
            self.canvas.configure(cursor="arrow" if disabled else "hand2")
        if kwargs:
            self.canvas.configure(**kwargs)
        self.draw()

    def set_hover(self, active: bool) -> None:
        self.hover = active
        if self.state == tk.DISABLED:
            return
        self.draw()

    def click(self, _event=None) -> None:
        if self.state != tk.DISABLED:
            self.command()

    def draw(self) -> None:
        self.canvas.delete("all")
        disabled = self.state == tk.DISABLED
        fill = self.colors["disabled"] if disabled else self.colors["active"] if self.hover else self.colors["bg"]
        outline = self.colors["border"] if self.variant == "secondary" else fill
        foreground = "#edf4f1" if self.variant == "primary" and disabled else self.colors["fg"]
        self.rounded_rect(1, 1, self.width - 1, self.height - 1, 8, fill=fill, outline=outline)
        self.canvas.create_text(
            self.width / 2,
            self.height / 2,
            text=self.text,
            fill=foreground,
            font=(FONT_FAMILY, 17 if self.variant == "primary" else 12, "bold"),
        )

    def rounded_rect(self, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs) -> None:
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        self.canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


class StyledProgress:
    def __init__(self, parent: tk.Widget, variable: tk.IntVar, maximum: int) -> None:
        self.variable = variable
        self.maximum = maximum
        self.track = tk.Frame(parent, bg=PROGRESS_BG, height=10)
        self.fill = tk.Frame(self.track, bg=PROGRESS_FG, height=10)
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


class ScrollablePage:
    def __init__(self, root: tk.Tk) -> None:
        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0, borderwidth=0)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor=tk.NW)
        self.canvas.bind("<Configure>", self.resize)
        self.inner.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda _event: self.canvas.yview_scroll(-3, "units"))
        self.canvas.bind_all("<Button-5>", lambda _event: self.canvas.yview_scroll(3, "units"))

    def pack(self, *args, **kwargs) -> None:
        self.canvas.pack(*args, **kwargs)

    def resize(self, event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def update_scroll_region(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ViewerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language = tk.StringVar(value=system_language())
        self.current_language = self.language.get()
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
        width = min(1080, max(920, self.root.winfo_screenwidth() - 120))
        height = min(920, max(760, self.root.winfo_screenheight() - 120))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(860, 680)
        self.root.configure(bg=BG)
        self.configure_styles()

        page = ScrollablePage(self.root)
        page.pack(fill=tk.BOTH, expand=True)

        shell = tk.Frame(page.inner, bg=SURFACE, highlightbackground="#d6e2de", highlightthickness=1)
        shell.pack(fill=tk.BOTH, expand=True, padx=32, pady=28)

        header = tk.Frame(shell, bg=GREEN, height=78)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        controls = tk.Frame(header, bg=GREEN)
        controls.pack(side=tk.LEFT, padx=(38, 22))
        for index, color in enumerate(("#c7dddd", "#9fc0bb", "#729994")):
            dot = tk.Canvas(controls, width=18, height=18, bg=GREEN, highlightthickness=0)
            dot.create_oval(3, 3, 15, 15, fill=color, outline=color)
            dot.grid(row=0, column=index, padx=5)
        tk.Label(header, text=self.tr("app_title"), bg=GREEN, fg="white", font=(FONT_FAMILY, 26, "bold")).pack(side=tk.LEFT)

        frame = tk.Frame(shell, bg=SURFACE, padx=42, pady=28)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)

        self.labels: dict[str, tk.Label] = {}
        self.buttons: dict[str, StyledButton] = {}
        self.date_format_labels: list[tk.Label] = []
        row = 0

        self.labels["zip_file"] = self.form_label(frame, self.tr("zip_file"), row, 0)
        self.entry(frame, self.zip_path).grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 12))
        self.buttons["choose_zip"] = self.secondary_button(frame, self.tr("choose_zip"), self.choose_zip)
        self.buttons["choose_zip"].grid(row=row + 1, column=2, padx=(12, 0), pady=(0, 12), sticky=tk.NS)
        row += 2

        self.labels["output_folder"] = self.form_label(frame, self.tr("output_folder"), row, 0)
        self.entry(frame, self.output_path).grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 12))
        self.buttons["choose_output"] = self.secondary_button(frame, self.tr("choose_output"), self.choose_output)
        self.buttons["choose_output"].grid(row=row + 1, column=2, padx=(12, 0), pady=(0, 12), sticky=tk.NS)
        row += 2

        self.labels["owner"] = self.form_label(frame, self.tr("owner"), row, 0)
        self.owner_box = StyledSelect(frame, self.owner, [], command=self.update_generate_state)
        self.owner_box.configure(state="disabled")
        self.owner_box.grid(row=row + 1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 12))
        row += 2

        self.labels["language"] = self.form_label(frame, self.tr("language"), row, 0)
        self.language_box = StyledSelect(frame, self.language, SUPPORTED_LANGUAGES, command=self.change_language)
        self.language_box.grid(row=row + 1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 12))
        row += 2

        dates = tk.Frame(frame, bg=SURFACE)
        dates.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 14))
        dates.columnconfigure(0, weight=1)
        dates.columnconfigure(1, weight=1)
        date_from_box = tk.Frame(dates, bg=SURFACE)
        date_from_box.grid(row=0, column=0, sticky=tk.EW, padx=(0, 12))
        date_to_box = tk.Frame(dates, bg=SURFACE)
        date_to_box.grid(row=0, column=1, sticky=tk.EW, padx=(12, 0))
        self.labels["date_from"] = self.form_label(date_from_box, self.tr("date_from"), 0, 0)
        self.date_input(date_from_box, self.date_from).grid(row=1, column=0, sticky=tk.EW, pady=(0, 6))
        date_from_format = self.hint_label(date_from_box, self.tr("date_format"))
        date_from_format.grid(row=2, column=0, sticky=tk.W)
        self.date_format_labels.append(date_from_format)
        date_from_box.columnconfigure(0, weight=1)
        self.labels["date_to"] = self.form_label(date_to_box, self.tr("date_to"), 0, 0)
        self.date_input(date_to_box, self.date_to).grid(row=1, column=0, sticky=tk.EW, pady=(0, 6))
        date_to_format = self.hint_label(date_to_box, self.tr("date_format"))
        date_to_format.grid(row=2, column=0, sticky=tk.W)
        self.date_format_labels.append(date_to_format)
        date_to_box.columnconfigure(0, weight=1)
        row += 1

        self.preview_card = tk.Frame(frame, bg=PANEL, highlightbackground="#d8e8e5", highlightthickness=1, padx=20, pady=16)
        self.preview_card.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 14))
        self.preview_label = tk.Label(self.preview_card, textvariable=self.preview, justify=tk.LEFT, anchor=tk.W, wraplength=820, bg=PANEL, fg=MUTED, font=(FONT_FAMILY, 13))
        self.preview_label.pack(fill=tk.X)
        row += 1

        self.check_auto_open = tk.Checkbutton(frame, text=self.tr("auto_open"), variable=self.auto_open, bg=SURFACE, fg=MUTED, activebackground=SURFACE, activeforeground=TEXT, selectcolor=PANEL, font=(FONT_FAMILY, 12), borderwidth=0, highlightthickness=0)
        self.check_auto_open.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 12))
        row += 1

        self.progress_bar = StyledProgress(frame, self.progress, maximum=5)
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 16))
        row += 1

        actions = tk.Frame(frame, bg=SURFACE)
        actions.grid(row=row, column=0, columnspan=3, sticky=tk.E, pady=(0, 12))
        self.buttons["generate"] = self.primary_button(actions, self.tr("generate"), self.generate)
        self.buttons["generate"].pack(side=tk.LEFT)
        self.buttons["open_output"] = self.secondary_button(actions, self.tr("open_output"), self.open_output)
        self.buttons["open_browser"] = self.secondary_button(actions, self.tr("open_browser"), self.open_browser)
        row += 1

        tk.Label(frame, textvariable=self.status, bg=SURFACE, fg=MUTED, anchor=tk.W, font=(FONT_FAMILY, 11)).grid(row=row, column=0, columnspan=3, sticky=tk.W)

    def configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")

    def entry(self, parent: tk.Widget, variable: tk.StringVar) -> StyledEntry:
        return StyledEntry(parent, variable)

    def date_input(self, parent: tk.Widget, variable: tk.StringVar) -> DateInput:
        return DateInput(parent, variable, lambda: self.language.get())

    def primary_button(self, parent: tk.Widget, text: str, command) -> StyledButton:
        return StyledButton(parent, text, command, variant="primary")

    def secondary_button(self, parent: tk.Widget, text: str, command) -> StyledButton:
        return StyledButton(parent, text, command, variant="secondary")

    def form_label(self, parent: tk.Widget, text: str, row: int, column: int) -> tk.Label:
        label = tk.Label(parent, text=text, bg=SURFACE, fg=MUTED, font=(FONT_FAMILY, 14, "bold"))
        label.grid(row=row, column=column, sticky=tk.W, pady=(0, 8))
        return label

    def hint_label(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(parent, text=text, bg=SURFACE, fg=MUTED, font=(FONT_FAMILY, 10))

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
        old_language = self.current_language
        new_language = self.language.get()
        self.reformat_date_inputs(old_language, new_language)
        self.current_language = new_language
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

    def reformat_date_inputs(self, old_language: str, new_language: str) -> None:
        for variable in (self.date_from, self.date_to):
            value = variable.get().strip()
            if not value:
                continue
            try:
                parsed = parse_gui_date(value, old_language)
            except ValueError:
                continue
            variable.set(format_gui_date(parsed, new_language))

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
            self.root.after(0, lambda captured=exc: self._participants_failed(captured))
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
            self.root.after(0, lambda captured=exc: self._generation_failed(captured))
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
