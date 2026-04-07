import tkinter as tk
import threading
import locale
import webbrowser

from tkinter import ttk, messagebox
from config import APP_WIDTH, APP_HEIGHT, CURRENT_VERSION
from database.seed.seed_all import seed_all
from database.seed.seed_cards import populate_cards
from database.database import create_tables#, run_migrations
from database.drop_hardcoded_tables import drop_hardcoded_tables
from database.seed.database_changes import (LATEST_DB_CHANGE, is_db_the_same, set_latest_db_change)
from frames.custom_deck_editor_frame import CustomDeckEditorFrame
from frames.home_frame import HomeFrame
from frames.cards_frame import CardsFrame
from frames.duelists_frame import DuelistsFrame
from frames.custom_decks_frame import CustomDecksFrame
from frames.loading_frame import LoadingFrame
from ui.ui_text import ui_text
from ui.loading_modal import LoadingDialog
from utils.resource_path import resource_path
from pathlib import Path
from services.card_search_service import CardSearchService

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.withdraw() #Prevents screen showing up before setting up configuration

        self.iconbitmap(resource_path("icon.ico"))
        self.start_app_and_configure()
        self.create_header()
        self.create_main_container()

        self.loading_frame = LoadingFrame(self.container, self)
        self.loading_frame.grid(row=0, column=0, sticky="nsew")
        self.frames["LoadingFrame"] = self.loading_frame

        self.update_ui_language()
        self.show_frame("LoadingFrame")

        self.deiconify()
        self.loading_frame.start()

        self.after(100, self.start_initialization_thread)

    def start_app_and_configure(self):
        """Styles, title, current OS language and Cache"""
        self.current_language = self.detect_os_language()
        self.card_search_service = CardSearchService()
        self.app_width = APP_WIDTH
        self.app_height = APP_HEIGHT
        self.title(f"Yu-Gi-Oh! Card Database v{CURRENT_VERSION}")
        self.resizable(False, False)
        self.frames = {}
        self.current_frame_name = None
        self.current_user_deck_id = None
        self.is_changing_language = False #Prevents user switching language if language is already being switched
        self.loading_dialog = None

        style = ttk.Style()
        style.theme_use("alt")

        self.center_screen()

    def detect_os_language(self) -> str:
        try:
            system_locale = locale.getlocale()[0]
        except Exception:
            system_locale = None

        if not system_locale:
            return "en"

        system_locale = system_locale.lower()

        if system_locale.startswith("pt"):
            return "pt"

        return "en"

    def center_screen(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.app_width // 2)
        y = (screen_height // 2) - (self.app_height // 2)
        self.geometry(f"{self.app_width}x{self.app_height}+{x}+{y}")

    def create_header(self):
        header = tk.Frame(self)
        header.pack(fill="x")

        self.language_var = tk.StringVar(value=self.current_language)

        # Preparing language menu here, but it won't be shown yet to prevent user from switching language when data is
        # being downloaded
        self.language_label = tk.Label(header)
        self.language_label.pack_forget()

        self.language_menu = tk.OptionMenu(
            header,
            self.language_var,
            "en",
            "pt",
            command=self.change_language
        )
        self.language_menu.pack_forget()

        self.docs_button = tk.Button(
            header,
            text=self.t("read_docs"),
            command=self.open_docs
        )
        self.docs_button.pack(side="right", padx=10)

    def open_docs(self):
        docs_path = resource_path("docs/CCF.html")
        webbrowser.open(Path(docs_path).resolve().as_uri())

    def create_main_container(self):
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

    def start_initialization_thread(self):
        threading.Thread(
            target=self.initialize_application,
            daemon=True
        ).start()

    def initialize_application(self):
        """Creates database and seeds them. Since the API is not complete in other languages, fetching the 'en' language
        is still needed to show all cards."""
        try:
            self.after(0, lambda: self.loading_frame.set_status(self.t("loading_database")))

            # For now, we're only dealing with changes on the hardcoded tables, so no need to do a big migration on it.
            # But we do check if there has been an update first to avoid useless DROP query.

            create_tables()
            #run_migrations()

            if not is_db_the_same():
                drop_hardcoded_tables()
                create_tables()
                self.after(0, lambda: self.loading_frame.set_status(self.t("loading_cards")))
                set_latest_db_change(LATEST_DB_CHANGE)
            else:
                self.after(0, lambda: self.loading_frame.set_status(self.t("loading_cards")))
            seed_all("en")

            if self.current_language != "en":
                self.after(0, lambda: self.loading_frame.set_status(self.t("loading_translations")))
                populate_cards(self.current_language)

            self.after(0, self.finish_initialization)

        except Exception as e:
            # When exceptions is created, we need to "freeze it" before using it instead of passing straight to lambda
            # Prevents:
            # NameError: cannot access free variable 'e' where it is not associated with a value in enclosing scope
            error = e
            self.after(0, lambda: self.handle_initialization_error (error))

    def handle_initialization_error(self, error):
        self.loading_frame.stop()
        self.loading_frame.set_status(f"{self.t('loading_error')}: {error}")

    def finish_initialization(self):
        for F in (HomeFrame, CardsFrame, DuelistsFrame, CustomDecksFrame, CustomDeckEditorFrame):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.loading_frame.stop()

        self.update_ui_language()

        self.language_label.pack(side="left", padx=5)
        self.language_menu.pack(side = "left")

        self.show_frame("HomeFrame")

    def update_ui_language(self):
        """Calls the refresh_ui in each Frame that switches text to the currently selected language."""
        self.language_label.config(text=self.t("language"))
        self.docs_button.config(text=self.t("read_docs"))

        for frame in self.frames.values():
            if hasattr(frame, "refresh_ui"):
                frame.refresh_ui()

            if hasattr(frame, "load_duelist") and hasattr(frame, "current_duelist_id") and frame.current_duelist_id:
                frame.load_duelist()

    def t (self, key):
        """Gets text from ui/ui_text.py file and implements fallback in case language key doesn't exist."""
        return ui_text.get(self.current_language, {}).get(key, key)

    def show_frame(self, name):
        self.current_frame_name = name
        frame = self.frames[name]
        frame.tkraise()

    def change_language(self, lang):
        """Changes language and populates the cards in that language. _should_skip_cards_seed inside seed_cards already
        guarantees that another seed won't occur if DB version matches API and if Translation Table is already filled"""
        if self.is_changing_language:
            return

        if lang == self.current_language:
            return

        previous_frame = self.current_frame_name or "HomeFrame"

        self.is_changing_language = True
        self.language_var.set(lang)
        self.language_menu.config(state="disabled")

        self.loading_dialog = LoadingDialog(
            self,
            title=self.t("changing_language_title"),
            status=self.t("changing_language")
        )
        self.loading_dialog.start()

        threading.Thread(
            target=self.change_language_async,
            args=(lang, previous_frame),
            daemon=True
        ).start()

    def change_language_async(self, lang, previous_frame):
            try:
                populate_cards(lang)
                self.after(0, lambda: self.finish_language_change(lang, previous_frame))
            except Exception as e:
                self.after(0, lambda: self.handle_language_change_error(e, previous_frame))

    def finish_language_change(self, lang, previous_frame):
        self.current_language = lang
        self.language_var.set(lang)

        if self.loading_dialog:
            self.loading_dialog.stop()
            self.loading_dialog.destroy()
            self.loading_dialog = None

        self.update_ui_language()

        if "CardsFrame" in self.frames:
            self.frames["CardsFrame"].load_cards(preserve_selection=True)

        if (
                "CustomDeckEditorFrame" in self.frames
                and hasattr(self.frames["CustomDeckEditorFrame"], "load_user_deck")
                and self.current_user_deck_id
        ):
            self.frames["CustomDeckEditorFrame"].load_user_deck()

        self.language_menu.config(state="normal")
        self.is_changing_language = False
        self.show_frame(previous_frame)

    def handle_language_change_error(self, error, previous_frame):
        if self.loading_dialog:
            self.loading_dialog.stop()
            self.loading_dialog.destroy()
            self.loading_dialog = None

        self.language_menu.config(state="normal")
        self.is_changing_language = False
        self.language_var.set(self.current_language)

        self.show_frame(previous_frame)

        messagebox.showerror(self.t("error"), f"{self.t('language_change_failed')}\n{error}")
