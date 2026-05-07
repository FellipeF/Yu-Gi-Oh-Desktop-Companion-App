import tkinter as tk
from tkinter import messagebox

from database.queries import get_cards_count, get_duelists_count, get_user_decks_count
from datetime import date, datetime
from typing import Optional
from services.api_client import ApiClient

class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        button_font = "Arial, 10"
        button_width = 24
        button_pady = 8

        #Contents on center of Frame
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(expand = True)

        self.title_label = tk.Label(self.content_frame, font=("Arial", 20, "bold"))
        self.title_label.pack(pady=(10, 8))

        self.subtitle_label = tk.Label(self.content_frame, font=("Arial", 11))
        self.subtitle_label.pack(pady=(0,20))

        self.buttons_frame = tk.Frame(self.content_frame)
        self.buttons_frame.pack(pady= (0,20))

        self.cards_button = tk.Button(
            self.buttons_frame,
            font=button_font,
            width=button_width,
            pady=button_pady,
            command=lambda: controller.show_frame("CardsFrame")
        )
        self.cards_button.pack(pady=button_pady)

        self.new_cards_button = tk.Button(
            self.buttons_frame,
            font=button_font,
            width=button_width,
            pady=button_pady,
            command=self.show_new_cards
        )
        self.new_cards_button.pack(pady=button_pady)

        self.duelists_button = tk.Button(
            self.buttons_frame,
            font=button_font,
            width=button_width,
            pady=button_pady,
            command=lambda: controller.show_frame("DuelistsFrame")
        )
        self.duelists_button.pack(pady=button_pady)

        self.user_decks_button = tk.Button(
            self.buttons_frame,
            font=button_font,
            width=button_width,
            pady=button_pady,
            command=lambda: controller.show_frame("CustomDecksFrame")
        )
        self.user_decks_button.pack(pady=button_pady)

        self.stats_label = tk.Label(self.content_frame, font=("Arial", 10))
        self.stats_label.pack(pady=(25))

        self.footer_frame = tk.Frame(self)
        self.footer_frame.pack(side="bottom", fill="x", pady=10)

        self.footer_label = tk.Label(self.footer_frame, font=("Arial, 9"))
        self.footer_label.pack()

        self.refresh_ui()

    def show_new_cards(self):
        info = ApiClient().read_info_file() or {}
        new_cards_ids = info.get("new_cards", [])

        if not new_cards_ids:
            # When the dataset is downloaded for the first time and all cards are new.
            messagebox.showinfo(self.controller.t("no_new_cards_added"), self.controller.t("no_new_cards"))
            return

        self.controller.show_new_cards_by_ids(new_cards_ids)

    def get_dataset_version_text(self) -> str:
        info = ApiClient().read_info_file()

        if not info:
            return self.controller.t("dataset_version_unknown")

        lang_info = info.get(self.controller.current_language, {})

        dataset_version = lang_info.get("database_version") # Check api_client for explanation
        last_update = lang_info.get("last_update")

        if not dataset_version:
            return self.controller.t("dataset_version_unknown")

        if last_update:
            normalized = self.normalize_date(last_update)

            if normalized:
                last_update = self.format_date(normalized)

        if last_update:
            return (
                f"{self.controller.t('dataset_version')}: {dataset_version} | "
                f"{self.controller.t('last_update')}: {last_update}"
            )

        return f"{self.controller.t('dataset_version')}: {dataset_version}"

    def normalize_date(self, date_str: str) -> Optional[date]: #Since in a error returns None
        """In case the API updates in a future date using the user date as a reference."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return None

        today = date.today()

        if date_obj > today:
            return today

        return date_obj

    def format_date(self, date_obj: date) -> str:
        """For non-american folks"""

        if self.controller.current_language == "en":
            return date_obj.strftime("%Y-%m-%d")
        else:
            return date_obj.strftime("%d/%m/%Y")

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("home_title"))
        self.subtitle_label.config(text=self.controller.t("home_subtitle"))

        self.cards_button.config(text=self.controller.t("check_cards"))
        self.duelists_button.config(text=self.controller.t("duelists"))
        self.user_decks_button.config(text=self.controller.t("custom_decks"))
        self.new_cards_button.config(text=self.controller.t("show_new_cards"))

        cards_count = get_cards_count()
        duelists_count = get_duelists_count()
        user_decks_count = get_user_decks_count()

        t = self.controller.t

        stats_text = (
            f"{t('cards_total')}: {cards_count}   |   "
            f"{t('duelists_total')}: {duelists_count}   |   "
            f"{t('user_decks_total')}: {user_decks_count}"
        )

        self.stats_label.config(text=stats_text)

        self.footer_label.config(
            text=f"{self.get_dataset_version_text()}"
        )