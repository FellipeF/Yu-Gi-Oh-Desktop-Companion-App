import os
import sys
import tkinter as tk
import locale
import traceback
import webbrowser
import requests
import subprocess
import tempfile
import threading

from tkinter import ttk, messagebox

from tkinterweb import HtmlFrame

from config import APP_WIDTH, APP_HEIGHT, CURRENT_VERSION, LATEST_DB_CHANGE, CARD_WIDTH, CARD_HEIGHT, GITHUB_REPO
from database.seed.seed_all import seed_all
from database.seed.seed_cards import populate_cards
from database.database import create_tables, get_connection, run_migrations
from database.drop_hardcoded_tables import drop_hardcoded_tables
from database.seed.database_changes import (
    is_db_the_same,
    set_latest_db_change,
    is_dataset_the_same,
    set_latest_dataset_seeded
)
from frames.custom_deck_editor_frame import CustomDeckEditorFrame
from frames.home_frame import HomeFrame
from frames.cards_frame import CardsFrame
from frames.duelists_frame import DuelistsFrame
from frames.custom_decks_frame import CustomDecksFrame
from frames.loading_frame import LoadingFrame
from services.api_client import ApiClient
from ui.card_details_window import CardDetailsWindow
from ui.downloading_dialog import DownloadingDialog
from ui.ui_text import ui_text
from ui.loading_modal import LoadingDialog
from utils.image_handler import ImageHandler
from utils.resource_path import resource_path
from pathlib import Path
from services.card_search_service import CardSearchService
from services.app_update import AppUpdater

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.image_handler = ImageHandler(CARD_WIDTH, CARD_HEIGHT)
        self.cards_info_cache = None

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
        self.title(f"Yu-Gi-Oh! Desktop Companion App {CURRENT_VERSION}")
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

            create_tables()

            api = ApiClient()
            online_dataset_version = None

            try:
                online_dataset_details = api.get_dataset_details()
                online_dataset_version = online_dataset_details.get("database_version")
            except Exception:
                online_dataset_version = None

            needs_db_reset = not is_db_the_same(LATEST_DB_CHANGE)
            needs_dataset_reset = (
                    online_dataset_version is not None and not is_dataset_the_same(online_dataset_version)
            )

            if needs_dataset_reset:
                self.after(0, lambda: self.loading_frame.set_status(self.t("loading_cards")))
                # Downloads the new EN dataset before dropping tables, allowing the app to show new cards
                api.load_cards("en")

            if needs_db_reset or needs_dataset_reset:
                drop_hardcoded_tables()
                create_tables()

                if needs_db_reset:
                    set_latest_db_change(LATEST_DB_CHANGE)

            run_migrations()

            self.after(0, lambda: self.loading_frame.set_status(self.t("loading_cards")))

            seed_all()

            if needs_dataset_reset and online_dataset_version:
                set_latest_dataset_seeded(online_dataset_version)

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

        self.cards_info_cache = ApiClient().read_info_file()

        self.after(300, self.post_init_tasks) # Solves racing conditions and avoids unknown dataset version

    def post_init_tasks(self):
        self.check_and_show_new_cards()
        self.check_app_update()

    def check_and_show_new_cards(self):
        api = ApiClient()
        info = api.read_info_file() or {}

        if not isinstance(info, dict) or "en" not in info: #Solves Incomplete initialization issues.
            return

        new_cards_ids = info.get("new_cards", [])

        if not new_cards_ids:
            return

        already_seen = info.get("new_cards_seen", False)

        if already_seen:
            return

        self.show_new_cards_by_ids(new_cards_ids)
        info["new_cards_seen"] = True
        api.write_info_file(info)

    def show_new_cards_by_ids(self, new_cards_ids):
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
        """, (self.current_language, *new_cards_ids)) #Avoids duplicates while also implementing fallback.

        cards = cursor.fetchall()
        conn.close()

        if cards:
            self.show_new_cards_window(cards, len(new_cards_ids), new_cards_ids)

    def show_new_cards_window(self, cards, total_count, all_ids):
        window = tk.Toplevel(self)
        window.title(self.t("new_cards_added"))
        window.resizable(False, False)

        width = 920
        height = 760
        columns = 4
        thumb_width = 150
        thumb_height = 222

        self.center_window(window, width, height)

        tk.Label(
            window,
            text=f"{total_count} {self.t('cards_added')}",
            font=("Arial", 16, "bold")
        ).pack(pady=(15, 2))

        tk.Label(
            window,
            text=self.t("click_for_more_details"),
            font=("Arial", 11),
        ).pack(pady=(0, 12))

        main_container = tk.Frame(window)
        main_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)

        cards_grid = tk.Frame(canvas)

        def update_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        cards_grid.bind("<Configure>", update_scrollregion)

        canvas_window = canvas.create_window((0, 0), window=cards_grid, anchor="n")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def open_card_details(card_id):
            CardDetailsWindow(self, card_id)

        def on_card_image_loaded(card_id, tk_img, label):
            if not label.winfo_exists():
                return

            if tk_img is None:
                tk_img = self.image_handler.get_placeholder(thumb_width, thumb_height)

            label.image = tk_img
            label.config(image=tk_img, text="")

        for index, (card_id, name) in enumerate(cards):
            row = index // columns
            col = index % columns

            card_frame = tk.Frame(
                cards_grid,
                width=190,
                height=310,
                bg="#f2f2f2",
                highlightbackground="#b0b0b0",
                highlightthickness=1,
                padx=10,
                pady=10,
                cursor="hand2"
            )
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="n")
            card_frame.pack_propagate(False)

            image_frame = tk.Frame(
                card_frame,
                width=thumb_width,
                height=thumb_height,
                bg="#1f1f1f",
                highlightbackground="#000000",
                highlightthickness=1,
                cursor="hand2"
            )
            image_frame.pack()
            image_frame.pack_propagate(False)

            image_label = tk.Label(
                image_frame,
                text=self.t("loading"),
                bg="#1f1f1f",
                fg="white",
                cursor="hand2"
            )
            image_label.pack(fill="both", expand=True)

            name_label = tk.Label(
                card_frame,
                text=name,
                wraplength=165,
                justify="center",
                font=("Tahoma", 12),
                bg="#f2f2f2",
                cursor="hand2"
            )
            name_label.pack(fill="x", pady=(6, 0))

            def on_enter(event, frame=card_frame):
                frame.config(bg="#e8e8e8", highlightbackground="#555555")

            def on_leave(event, frame=card_frame):
                frame.config(bg="#f2f2f2", highlightbackground="#b0b0b0")

            for widget in (card_frame, image_frame, image_label, name_label):
                widget.bind("<Button-1>", lambda e, cid=card_id: open_card_details(cid))
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

            self.image_handler.load_thumbnail_async(
                window,
                card_id,
                thumb_width,
                thumb_height,
                lambda cid, tk_img, label=image_label: on_card_image_loaded(cid, tk_img, label)
            )

        buttons_frame = tk.Frame(window)
        buttons_frame.pack(pady=(0, 15))

        close_button = tk.Button(
            buttons_frame,
            text="OK",
            width=10,
            command=window.destroy
        )
        close_button.pack()

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        def on_close():
            canvas.unbind_all("<MouseWheel>")
            window.destroy()

        # Prevents canvas.yview_scroll(int(-1 * (event.delta / 120)), "units") Tkinter Exception
        # This is used to unbind the Mouse Wheel on the whole app when the X is pressed.

        window.protocol("WM_DELETE_WINDOW", on_close)
        close_button.config(command=on_close)

        window.transient(self)
        window.focus()

    def check_app_update(self):
        threading.Thread(
            target=self._check_app_update_worker,
            daemon=True
        ).start()

    def _check_app_update_worker(self):
        try:
            updater = AppUpdater(GITHUB_REPO, CURRENT_VERSION)
            has_update, url, changelog, download_url = updater.is_update_available()

            if has_update:
                self.after(0, lambda: self.show_update_dialog (url, changelog, download_url))
        except Exception as e:
            print(f"Update Check Error: {e}") #TODO: Show this to user

    def show_update_dialog(self, url, changelog, download_url):
        modal = tk.Toplevel(self)
        modal.title(self.t("update_available_title"))

        self.center_window(modal, 700, 600)
        modal.resizable(False, False)

        tk.Label(
            modal,
            text=self.t("update_available_message"),
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        html_container = tk.Frame(modal, height=280)
        html_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        html_container.pack_propagate(False)

        html_frame = HtmlFrame(html_container, messages_enabled=False)
        html_frame.load_html(changelog)
        html_frame.pack(fill="both", expand=True)

        buttons_frame = tk.Frame(modal)
        buttons_frame.pack(pady=(5, 12))

        if download_url:
            tk.Button(
                buttons_frame,
                text=self.t("download_update"),
                command=lambda: self.start_download_thread(download_url)
            ).pack(side="left", padx=5)

        #Fallback
        tk.Button(
            buttons_frame,
            text=self.t("open_in_browser"),
            command=lambda: webbrowser.open(url)
        ).pack(side="left", padx=5)

        tk.Button(
            buttons_frame,
            text=self.t("ignore"),
            command=modal.destroy
        ).pack(side="left", padx=5)

        modal.transient(self)

    def start_download_thread(self, url):
        self.loading_dialog = DownloadingDialog(
            self,
            title=self.t("downloading_update"),
            status=self.t("downloading_update")
        )
        self.attributes("-disabled", True)

        threading.Thread(
            target=self.download_update_worker,
            args=(url,),
            daemon=True
        ).start()

    def download_update_worker(self, url):
        save_path = os.path.join(tempfile.gettempdir(), "ygo_update_installer.exe") #TODO: Digital Signature

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total = int(response.headers.get('content-length') or 0)
            if total <= 0:
                self.after(0, lambda: self.loading_dialog.set_indeterminate())
            downloaded = 0

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    if total > 0:
                        progress = downloaded / total * 100
                        self.after(0, lambda p=progress: self.update_download_progress(p))

            self.after(0, lambda: self.download_finished(save_path))

        except Exception as e:
            self.after(0, lambda: self.download_failed(e))

    def update_download_progress(self, progress):
        if self.loading_dialog:
            self.loading_dialog.set_progress(progress)

    def download_finished(self, path):
        self.attributes("-disabled", False)

        if self.loading_dialog:
            self.loading_dialog.destroy()
            self.loading_dialog = None

        messagebox.showinfo(
            self.t("download_complete"),
            self.t("update_downloaded")
        )

        updater_path = os.path.join(os.path.dirname(sys.executable), "updater.exe") #Prevents updater not being found by Installer

        if not os.path.exists(updater_path):
            messagebox.showerror(
                self.t("error"),
                "Updater not found!"
            )
            return

        try:
            subprocess.Popen(
                [
                    updater_path,
                    "--installer", path,
                    "--pid", str(os.getpid())
                ],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )

            self.after(1500, self.force_exit) # Kills process instead of destroying tkinter app.

        except Exception as e:
            messagebox.showerror(
                self.t("error"),
                f"{self.t('update_fail')}\n{e}"
            )

    def force_exit(self):
        os._exit(0)

    def download_failed(self, error):
        self.attributes("-disabled", False)
        if self.loading_dialog:
            self.loading_dialog.stop()
            self.loading_dialog.destroy()
            self.loading_dialog = None

        messagebox.showerror(
            self.t("error"),
            f"{self.t('update_fail')}\n{error}"
        )

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
