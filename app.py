import tkinter as tk
import threading
import locale
import traceback
import webbrowser

from tkinter import ttk, messagebox
from config import APP_WIDTH, APP_HEIGHT, CURRENT_VERSION, LATEST_DB_CHANGE
from database.seed.seed_cards import populate_cards
from database.database import create_tables, get_connection  # , run_migrations
from database.drop_hardcoded_tables import drop_hardcoded_tables
from database.seed.database_changes import (is_db_the_same, set_latest_db_change)
from frames.custom_deck_editor_frame import CustomDeckEditorFrame
from frames.home_frame import HomeFrame
from frames.cards_frame import CardsFrame
from frames.duelists_frame import DuelistsFrame
from frames.custom_decks_frame import CustomDecksFrame
from frames.loading_frame import LoadingFrame
from services.api_client import ApiClient
from ui.card_details_window import CardDetailsWindow
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
        self.title(f"Yu-Gi-Oh! Desktop Companion App v{CURRENT_VERSION}")
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

    def center_window(self, window, width, height):
        # For the toplevel new cards window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        window.geometry(f"{width}x{height}+{x}+{y}")

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
            populate_cards("en")

            if self.current_language != "en":
                self.after(0, lambda: self.loading_frame.set_status(self.t("loading_translations")))
                populate_cards(self.current_language)

            self.after(0, self.finish_initialization)

        except Exception as e:
            # When exceptions is created, we need to "freeze it" before using it instead of passing straight to lambda
            # Prevents:
            # NameError: cannot access free variable 'e' where it is not associated with a value in enclosing scope
            traceback.print_exc()
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

        self.check_and_show_new_cards()

    def check_and_show_new_cards(self):
        api = ApiClient()
        info = api.read_info_file() or {}
        new_cards_ids = info.get("new_cards", [])

        if not new_cards_ids:
            return

        conn = get_connection()
        cursor = conn.cursor()

        placeholders = ",".join(["?"] * len(new_cards_ids))

        cursor.execute(f"""
            SELECT c.id, COALESCE(t1.name, t2.name)
            FROM cards c
            LEFT JOIN cards_translations t1
                ON c.id = t1.card_id AND t1.language_code = ?
            LEFT JOIN cards_translations t2
                ON c.id = t2.card_id AND t2.language_code = 'en'
            WHERE c.id IN ({placeholders})
            LIMIT 20
        """, (self.current_language, *new_cards_ids)) #Avoids duplicates while also implementing fallback.

        cards = cursor.fetchall()
        conn.close()

        self.show_new_cards_modal(cards, len(new_cards_ids), new_cards_ids)

        # Once they are seen, no need to show new cards everytime app starts.
        info["new_cards"] = []
        api.write_info_file(info)

    def show_new_cards_modal(self, cards, total_count, all_ids):
        modal = tk.Toplevel(self)
        modal.title(self.t("new_cards_added"))

        width = 650
        height = 650
        self.center_window(modal, width, height)

        (tk.Label(modal,
                 text=f"{total_count} {self.t('cards_added')}",
                 font=("Arial", 12, "bold"))
         .pack(pady=10))

        container = tk.Frame(modal)
        container.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        modal.after(10, lambda: self._populate_new_cards_on_window(scrollable_frame, cards)) #Prevents performance bottlenecks

        if total_count > len(cards):
            tk.Button(
                modal,
                text=self.t("see_all"),
                command=lambda: self.show_all_new_cards_modal(all_ids)
            ).pack(pady=5)

        tk.Button(modal, text="OK", command=modal.destroy).pack(pady=10)

        modal.transient(self)

    def _populate_new_cards_on_window(self, parent, cards):
        for card_id, name in cards:
            frame = tk.Frame(parent)
            frame.pack(fill="x", pady=2)

            tk.Label(
                frame,
                text=name,
                anchor="w",
                font=("Tahoma", 14)
            ).pack(side="left", fill="x", expand=True)

            tk.Button(
                frame,
                text=self.t("card_details"),
                command=lambda cid=card_id: CardDetailsWindow(self, cid)
            ).pack(side="right", padx=40)

    def show_all_new_cards_modal(self, card_ids):
        modal = tk.Toplevel(self)
        modal.title(self.t("all_new_cards"))

        self.center_window(modal, 500, 600)

        conn = get_connection()
        cursor = conn.cursor()

        placeholders = ",".join(["?"] * len(card_ids))

        cursor.execute(f"""
            SELECT c.id, COALESCE(t1.name, t2.name)
            FROM cards c
            LEFT JOIN cards_translations t1
                ON c.id = t1.card_id AND t1.language_code = ?
            LEFT JOIN cards_translations t2
                ON c.id = t2.card_id AND t2.language_code = 'en'
            WHERE c.id IN ({placeholders})
        """, (self.current_language, *card_ids))

        cards = cursor.fetchall()
        conn.close()

        for card_id, name in cards:
            frame = tk.Frame(modal)
            frame.pack(fill="x", padx=10, pady=2)

            tk.Label(frame, text=name).pack(side="left")

            tk.Button(
                frame,
                text=self.t("card_details"),
                command=lambda cid=card_id: CardDetailsWindow(self, cid)
            ).pack(side="right")

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
