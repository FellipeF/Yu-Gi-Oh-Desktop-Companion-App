import tkinter as tk
from tkinter import ttk
from config import APP_WIDTH, APP_HEIGHT, CURRENT_VERSION
from database.seed.seed_all import seed_all
from database.seed.seed_cards import populate_cards
from database.database import create_tables
from frames.home_frame import HomeFrame
from frames.cards_frame import CardsFrame
from frames.duelists_frame import DuelistsFrame
from frames.duelist_details_frame import DuelistDetailsFrame
from ui.translations import translations
from utils.resource_path import resource_path

# TODO: User Start App on his native language, DB is already protected for it. Current OS Language? User chooses first? Leave this as it is?
# TODO: Button to read the CFF - Card Consistency File in /docs folder

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.iconbitmap(resource_path("icon.ico"))
        self.start_app_and_configure()
        self.start_database()
        self.create_top_bar()
        self.create_home_frame()

        for F in (HomeFrame, CardsFrame, DuelistsFrame, DuelistDetailsFrame):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.update_ui_language()
        self.show_frame("HomeFrame")

    def start_app_and_configure(self):
        self.current_language = "en"
        self.app_width = APP_WIDTH
        self.app_height = APP_HEIGHT
        self.title(f"Yu-Gi-Oh! Card Database v{CURRENT_VERSION}")
        self.resizable(False, False)
        self.frames = {}

        style = ttk.Style()
        style.theme_use("alt")

        self.center_screen()

    def center_screen(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.app_width // 2)
        y = (screen_height // 2) - (self.app_height // 2)
        self.geometry(f"{self.app_width}x{self.app_height}+{x}+{y}")

    def start_database(self):
        create_tables()
        seed_all(self.current_language)

    def create_top_bar(self):
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x")

        self.language_var = tk.StringVar(value=self.current_language)

        self.language_label = tk.Label(top_bar)
        self.language_label.pack(side="left", padx=5)

        tk.OptionMenu(
            top_bar,
            self.language_var,
            "en",
            "pt",
            command=self.change_language
        ).pack(side="left")

    def create_home_frame(self):
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

    def change_language(self, lang):
        self.current_language = lang
        self.language_var.set(lang)

        populate_cards(lang)

        self.update_ui_language()
        #In case user knows the name only in the original version, allow to search for the card and preserve his selection.
        self.frames["CardsFrame"].load_cards(preserve_selection=True)

    def update_ui_language(self):
        self.language_label.config(text=self.t("language"))

        for frame in self.frames.values():
            if hasattr(frame, "refresh_ui"):
                frame.refresh_ui()

            if hasattr(frame, "load_duelist") and frame.current_duelist_id:
                frame.load_duelist()

    def t (self, key):
        return translations.get(self.current_language, {}).get(key, key)