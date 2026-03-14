import tkinter as tk
from PIL import Image, ImageTk
import threading

from utils import cache_image

from database.queries import search_cards
from database.queries import (
    get_user_deck_by_id,
    get_cards_by_user_deck,
    add_card_to_user_deck,
    remove_card_from_user_deck,
    update_user_deck_card_quantity,
)
from ui.card_details_window import CardDetailsWindow

CARD_WIDTH = 320
CARD_HEIGHT = 470


class CustomDeckEditorFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self.current_found_cards = []
        self.current_deck_cards = []

        self.selected_search_card_id = None
        self.selected_deck_card_id = None
        self.selected_deck_card_name = None

        self.tk_image = None

        self.title_label = tk.Label(self, font=("Arial", 14))
        self.title_label.pack(pady=(10, 2))

        self.deck_info_label = tk.Label(self, font=("Arial", 11))
        self.deck_info_label.pack(pady=(0, 15))

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT SIDE - Search cards
        left_frame = tk.Frame(main_container, width=300)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        left_frame.pack_propagate(False)

        self.search_label = tk.Label(left_frame)
        self.search_label.pack(pady=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_cards)

        self.search_entry = tk.Entry(left_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(pady=(0, 8))

        self.search_results_list = tk.Listbox(left_frame, width=40, height=18)
        self.search_results_list.pack(fill="both", expand=True)
        self.search_results_list.bind("<<ListboxSelect>>", self.on_search_card_selected)

        # CENTER - Card preview and actions
        center_frame = tk.Frame(main_container, width=360)
        center_frame.pack(side="left", fill="y", padx=5)
        center_frame.pack_propagate(False)

        image_container = tk.Frame(center_frame, width=CARD_WIDTH, height=CARD_HEIGHT)
        image_container.pack(pady=(10, 6))
        image_container.pack_propagate(False)

        self.image_label = tk.Label(image_container, text="", anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.show_card_details_button = tk.Button(
            center_frame,
            command=self.open_card_details_window
        )
        self.show_card_details_button.pack(pady=(0, 8))
        self.show_card_details_button.pack_forget()

        self.add_to_deck_button = tk.Button(
            center_frame,
            command=self.add_selected_card_to_deck
        )
        self.add_to_deck_button.pack(pady=(0, 8))
        self.add_to_deck_button.pack_forget()

        # RIGHT SIDE - Current deck cards
        right_frame = tk.Frame(main_container, width=300)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        left_frame.pack_propagate(False)

        self.deck_cards_label = tk.Label(right_frame)
        self.deck_cards_label.pack(pady=(0, 5))

        self.deck_cards_list = tk.Listbox(right_frame, width=45, height=18)
        self.deck_cards_list.pack(fill="both", expand=True)
        self.deck_cards_list.bind("<<ListboxSelect>>", self.on_deck_card_selected)

        deck_buttons_frame = tk.Frame(right_frame)
        deck_buttons_frame.pack(pady=10)

        self.remove_one_button = tk.Button(
            deck_buttons_frame,
            command=self.remove_one_copy
        )
        self.remove_one_button.grid(row=0, column=0, padx=5)

        self.remove_card_button = tk.Button(
            deck_buttons_frame,
            command=self.remove_selected_card_from_deck
        )
        self.remove_card_button.grid(row=0, column=1, padx=5)

        # Bottom buttons
        bottom_buttons = tk.Frame(self)
        bottom_buttons.pack(pady=10)

        self.return_button = tk.Button(
            bottom_buttons,
            command=self.go_back
        )
        self.return_button.grid(row=0, column=0, padx=5)

        self.refresh_ui()

    def refresh_ui(self):
        """Controls Text when frame appears and when switching language"""
        self.title_label.config(text=self.controller.t("custom_deck_editor"))
        self.search_label.config(text=self.controller.t("search_cards"))
        self.deck_cards_label.config(text=self.controller.t("deck_cards"))
        self.image_label.config(text=self.controller.t("select_card"))
        self.show_card_details_button.config(text=self.controller.t("card_details"))
        self.add_to_deck_button.config(text=self.controller.t("add_to_deck"))
        self.remove_one_button.config(text=self.controller.t("remove_one"))
        self.remove_card_button.config(text=self.controller.t("remove_card"))
        self.return_button.config(text=self.controller.t("return"))

        self.load_user_deck()

    def load_user_deck(self):
        deck_id = self.controller.current_user_deck_id

        if not deck_id:
            self.deck_info_label.config(text=self.controller.t("no_deck_selected"))
            return

        deck = get_user_deck_by_id(deck_id)

        if not deck:
            self.deck_info_label.config(text=self.controller.t("deck_not_found"))
            return

        _deck_id, deck_name, is_used = deck
        total_cards = self.get_current_total_cards(deck_id)

        used_text = self.controller.t("yes") if is_used else self.controller.t("no")

        self.deck_info_label.config(
            text=f"{deck_name} | {self.controller.t('total_cards')}: {total_cards} | {self.controller.t('used')}: {used_text}"
        )

        self.load_deck_cards()
        self.filter_cards()

    def get_current_total_cards(self, deck_id: int) -> int:
        cards = get_cards_by_user_deck(deck_id, self.controller.current_language)
        return sum(card[2] for card in cards)

    def filter_cards(self, *args):
        name = self.search_var.get()
        language = self.controller.current_language

        self.current_found_cards = search_cards(name=name, language=language)

        self.search_results_list.delete(0, tk.END)

        for card in self.current_found_cards:
            self.search_results_list.insert(tk.END, card[1])

    def load_deck_cards(self):
        deck_id = self.controller.current_user_deck_id

        if not deck_id:
            return

        self.current_deck_cards = get_cards_by_user_deck(
            deck_id,
            self.controller.current_language
        )

        self.deck_cards_list.delete(0, tk.END)

        for card_id, card_name, quantity in self.current_deck_cards:
            self.deck_cards_list.insert(tk.END, f"{card_name} x{quantity}")

    def on_search_card_selected(self, event):
        selection = self.search_results_list.curselection()

        if not selection:
            return

        card = self.current_found_cards[selection[0]]
        card_id = card[0]

        self.selected_search_card_id = card_id

        threading.Thread(
            target=self.load_image_async,
            args=(card_id,),
            daemon=True
        ).start()

    def load_image_async(self, card_id):
        img_path = cache_image.get_card_image(card_id)

        if not img_path:
            return

        img = Image.open(img_path).resize((CARD_WIDTH, CARD_HEIGHT))
        tk_img = ImageTk.PhotoImage(img)

        self.after(0, self.update_image_label, tk_img)

    def update_image_label(self, tk_img):
        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")
        self.show_card_details_button.pack(pady=(0, 8))
        self.add_to_deck_button.pack(pady=(0, 8))

    def open_card_details_window(self):
        if not self.selected_search_card_id:
            return

        CardDetailsWindow(self.controller, self.selected_search_card_id)

    def add_selected_card_to_deck(self):
        deck_id = self.controller.current_user_deck_id

        if not deck_id or not self.selected_search_card_id:
            return

        success = add_card_to_user_deck(
            deck_id=deck_id,
            card_id=self.selected_search_card_id,
            quantity=1
        )

        if not success:
            return

        self.load_user_deck()

    def on_deck_card_selected(self, event):
        selection = self.deck_cards_list.curselection()

        if not selection:
            self.selected_deck_card_id = None
            self.selected_deck_card_name = None
            return

        card_id, card_name, quantity = self.current_deck_cards[selection[0]]
        self.selected_deck_card_id = card_id
        self.selected_deck_card_name = card_name

    def remove_one_copy(self):
        deck_id = self.controller.current_user_deck_id

        if not deck_id or (self.selected_deck_card_id is None and not self.selected_deck_card_name):
            return

        selected = None
        for card_id, card_name, quantity in self.current_deck_cards:
            if card_id == self.selected_deck_card_id and card_name == self.selected_deck_card_name:
                selected = (card_id, card_name, quantity)
                break

        if not selected:
            return

        card_id, card_name, quantity = selected

        new_quantity = quantity - 1

        update_user_deck_card_quantity(
            deck_id=deck_id,
            quantity=new_quantity,
            card_id=card_id,
            card_name=None if card_id is not None else card_name
        )

        self.load_user_deck()

    def remove_selected_card_from_deck(self):
        deck_id = self.controller.current_user_deck_id

        if not deck_id or (self.selected_deck_card_id is None and not self.selected_deck_card_name):
            return

        remove_card_from_user_deck(
            deck_id=deck_id,
            card_id=self.selected_deck_card_id,
            card_name=None if self.selected_deck_card_id is not None else self.selected_deck_card_name
        )

        self.load_user_deck()

    def go_back(self):
        self.controller.frames["CustomDecksFrame"].load_user_decks()
        self.controller.show_frame("CustomDecksFrame")