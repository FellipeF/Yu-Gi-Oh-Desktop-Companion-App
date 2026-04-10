import tkinter as tk
import threading
from tkinter import ttk

from PIL import Image, ImageTk

from database.queries import (
    get_user_deck_by_id,
    get_cards_by_user_deck,
    add_card_to_user_deck,
    remove_card_from_user_deck,
    update_user_deck_card_quantity,
)
from ui.card_details_window import CardDetailsWindow
from utils.card_image_loader import load_card_pil_image
from config import CARD_WIDTH, CARD_HEIGHT
from utils.resource_path import resource_path


class CustomDeckEditorFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self.current_found_cards = []
        self.current_deck_cards = []

        self.active_card_id = None
        self.selected_deck_card_id = None
        self.selected_deck_card_name = None

        self.tk_image = None
        self.placeholder_image = ImageTk.PhotoImage(
            Image.open(resource_path("images/placeholder.jpg")).resize((CARD_WIDTH, CARD_HEIGHT))
        )
        self.displayed_deck_cards = []

        self.title_label = tk.Label(self, font=("Arial", 14))
        self.title_label.pack(pady=(10, 2))

        self.deck_info_label = tk.Label(self, font=("Arial", 11))
        self.deck_info_label.pack(pady=(0, 15))

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Side - Card List and Search
        left_frame = tk.Frame(main_container, width=420)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_frame.pack_propagate(False)

        self.search_label = tk.Label(left_frame, font=("Tahoma", 12))
        self.search_label.pack(anchor="w", pady=(0,5))

        self.search_var = tk.StringVar()
        # Implementing debounce
        self._filter_after_id = None
        self.search_var.trace_add("write", self.on_search_text_changed)

        self.search_entry = tk.Entry(left_frame, textvariable=self.search_var, width=40, font=("Tahoma", 12))
        self.search_entry.pack(anchor="w", pady=(0,8))

        search_container = tk.Frame(left_frame)
        search_container.pack(fill="both", expand=True)

        self.search_results_list = tk.Listbox(
            search_container,
            width=40,
            height=18,
            font=("Tahoma", 12),
            exportselection=False
        )
        self.search_results_list.pack(side="left", fill="both", expand=True)

        self.search_scroll = ttk.Scrollbar(
            search_container,
            orient="vertical",
            command=self.search_results_list.yview
        )
        self.search_scroll.pack(side="right", fill="y")

        self.search_results_list.config(yscrollcommand=self.search_scroll.set)

        self.search_results_list.bind("<<ListboxSelect>>", self.show_card_image)

        # CENTER - Card preview and actions
        center_frame = tk.Frame(main_container, width=CARD_WIDTH + 40)
        center_frame.pack(side="left", fill="both", expand=False, padx=(0,10))
        center_frame.pack_propagate(False)

        image_container = tk.Frame(center_frame, width=CARD_WIDTH, height=CARD_HEIGHT)
        image_container.pack(expand=True)
        image_container.pack_propagate(False)

        self.image_label = tk.Label(image_container, text="", anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.show_card_details_button = tk.Button(
            center_frame,
            font=("Tahoma", 12),
            command=self.open_card_details_window
        )
        self.show_card_details_button.pack(pady=(0, 8))
        self.show_card_details_button.pack_forget()

        self.add_to_deck_button = tk.Button(
            center_frame,
            font=("Tahoma", 12),
            command=self.add_selected_card_to_deck
        )
        self.add_to_deck_button.pack(pady=(0, 8))
        self.add_to_deck_button.pack_forget()

        # Right Side - Current selected deck cards
        right_frame = tk.Frame(main_container, width=420)
        right_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        right_frame.pack_propagate(False)

        self.deck_cards_label = tk.Label(right_frame, font=("Tahoma", 12))
        self.deck_cards_label.pack(pady=(0, 5))

        deck_container = tk.Frame(right_frame, height=450)
        deck_container.pack(fill="x", expand=False)
        deck_container.pack_propagate(False)

        self.deck_cards_list = tk.Listbox(
            deck_container,
            width=45,
            height=18,
            font=("Tahoma", 12),
            exportselection=False
        )
        self.deck_cards_list.pack(side="left", fill="both", expand=True)

        self.deck_scroll = ttk.Scrollbar(
            deck_container,
            orient="vertical",
            command=self.deck_cards_list.yview
        )
        self.deck_scroll.pack(side="right", fill="y")

        self.deck_cards_list.config(yscrollcommand=self.deck_scroll.set)

        self.deck_cards_list.bind("<<ListboxSelect>>", self.on_deck_card_selected)

        deck_buttons_frame = tk.Frame(right_frame)
        deck_buttons_frame.pack(pady=10)

        self.remove_one_button = tk.Button(
            deck_buttons_frame,
            font=("Tahoma", 12),
            command=self.remove_one_copy
        )
        self.remove_one_button.grid(row=0, column=0, padx=5)

        self.remove_card_button = tk.Button(
            deck_buttons_frame,
            font=("Tahoma", 12),
            command=self.remove_selected_card_from_deck
        )
        self.remove_card_button.grid(row=0, column=1, padx=5)

        # Bottom buttons
        bottom_buttons = tk.Frame(self)
        bottom_buttons.pack(pady=10)

        self.return_button = tk.Button(
            bottom_buttons,
            font=("Tahoma", 12),
            command=self.go_back
        )
        self.return_button.grid(row=0, column=0, padx=5)

        self.refresh_ui()
        self.filter_cards()

    def refresh_ui(self):
        """Controls Text when frame appears and when switching language"""
        previous_search_card_id = self.active_card_id
        previous_deck_card_id = self.selected_deck_card_id
        previous_deck_card_name = self.selected_deck_card_name

        self.search_label.config(text=self.controller.t("search_card"))
        self.deck_cards_label.config(text=self.controller.t("deck_cards"))

        if self.tk_image is None and self.image_label.cget("image") == "":
            self.image_label.config(text=self.controller.t("select_card"))

        self.show_card_details_button.config(text=self.controller.t("card_details"))
        self.add_to_deck_button.config(text=self.controller.t("add_to_deck"))
        self.remove_one_button.config(text=self.controller.t("remove_one"))
        self.remove_card_button.config(text=self.controller.t("remove_card"))
        self.return_button.config(text=self.controller.t("return"))

        # Change currently populated list for current deck and card list while restoring choice
        self.filter_cards()
        self.load_user_deck()

        self.restore_search_selection(previous_search_card_id)
        self.restore_deck_selection(previous_deck_card_id, previous_deck_card_name)

    def load_user_deck(self):
        """Load currently selected deck and contents. """
        deck_id = self.controller.current_user_deck_id

        # No need to check if deck_id exists, since user only enters this Frame if they select a deck from Custom Decks

        deck = get_user_deck_by_id(deck_id)

        if not deck:
            # Prevents error if deck list is empty
            return

        _deck_id, deck_name, is_used = deck
        main_count, extra_count = self.get_deck_card_counts(deck_id)

        used_text = self.controller.t("yes") if is_used else self.controller.t("no")

        self.title_label.config(
            text=f"{self.controller.t('editing_deck')}: {deck_name}"
        )

        self.deck_info_label.config(
            text=f"{self.controller.t('main_deck')} : {main_count} | "
                 f"{self.controller.t('extra_deck')}: {extra_count}\n"
                 f"{self.controller.t('used')}: {used_text}", font=("Tahoma", 12)
        )

        self.load_deck_cards()

    def get_deck_card_counts(self, deck_id: int) -> tuple[int, int]:
        """Returns count of main deck cards and extra deck cards separated"""
        cards = get_cards_by_user_deck(deck_id, self.controller.current_language)

        main_count = 0
        extra_count = 0

        for card_id, card_name, quantity, card_type, section in cards:
            if section == "extra":
                extra_count +=quantity
            else:
                main_count += quantity

        return main_count, extra_count

    def on_search_text_changed(self, *args):
        if self._filter_after_id is not None:
            self.after_cancel(self._filter_after_id)

        self._filter_after_id = self.after(250, self.filter_cards)

    def filter_cards(self):
        """Controls search box"""
        self._filter_after_id = None
        name = self.search_var.get()
        language = self.controller.current_language

        previous_card_id = self.active_card_id

        if name.strip():
            self.current_found_cards = self.controller.card_search_service.search(
                text=name,
                language_code=language,
            )
        else:
            self.current_found_cards = self.controller.card_search_service.get_all_cards(language)

        self.search_results_list.delete(0, tk.END)

        for card in self.current_found_cards:
            self.search_results_list.insert(tk.END, card[1])

        #self.update_scroll_visibility(self.search_results_list, self.search_scroll)
        self.restore_search_selection(previous_card_id)

    def load_deck_cards(self):
        """Loads cards that belong to the currently selected deck"""
        deck_id = self.controller.current_user_deck_id

        if not deck_id:
            return

        self.current_deck_cards = get_cards_by_user_deck(
            deck_id,
            self.controller.current_language
        )

        self.deck_cards_list.delete(0, tk.END)
        self.displayed_deck_cards = []
        current_section = None
        current_group = None

        for card_id, card_name, quantity, card_type, section in self.current_deck_cards:
            if section != current_section:
                label = self.controller.t("main_deck") if section == "main" else self.controller.t("extra_deck")
                self.deck_cards_list.insert(tk.END, f"=== {label.upper()} ===")
                self.displayed_deck_cards.append(None)
                current_section = section
                current_group = None

            group_label = self._card_group_label(card_type, section)

            if group_label and group_label != current_group:
                self.deck_cards_list.insert(tk.END, f"--- {group_label.upper()} ---")

                index = self.deck_cards_list.size() - 1
                color = self._get_group_color(group_label)
                self.deck_cards_list.itemconfig(index, fg=color)

                self.displayed_deck_cards.append(None)
                current_group = group_label

            self.deck_cards_list.insert(tk.END, f"{quantity}x {card_name}")
            self.displayed_deck_cards.append((card_id, card_name, quantity, card_type, section))

        self.update_scroll_visibility(self.deck_cards_list, self.deck_scroll)

    def _card_group_label(self, card_type: str | None, deck_section: str) -> str:
        if deck_section == "extra":
            return None

        # Throws "TypeError: argument of type 'NoneType' is not iterable" if not here
        if not card_type:
            return self.controller.t("other_cards")

        # Effect/Normal/Pendulum Monsters fall under the same category when sorting
        if "Monster" in card_type:
            return self.controller.t("monsters")

        if card_type == "Spell Card":
            return self.controller.t("spells")

        if card_type == "Trap Card":
            return self.controller.t("traps")

        # Just in case
        return self.controller.t("other_cards")

    def _get_group_color(self, group_label: str) -> str:
        """Colors for type of cards section separators"""
        if group_label == self.controller.t("spells"):
            return "#1d8f6a"
        if group_label == self.controller.t("traps"):
            return "#8e44ad"
        if group_label == self.controller.t("monsters"):
            return "#c97a2b"

        return "black"

    def show_card_image(self, event):
        """Load card image async"""
        selection = self.search_results_list.curselection()
        if not selection:
            return

        card = self.current_found_cards[selection[0]]
        card_id = card[0]

        self.active_card_id = card_id

        threading.Thread(
            target=self.load_image_async,
            args=(card_id,),
            daemon=True
        ).start()

    def load_image_async(self, card_id):
        pil_img = load_card_pil_image(card_id, CARD_WIDTH, CARD_HEIGHT)

        if pil_img is None:
            return

        self.after(0, self.update_image_label, pil_img)

    def update_image_label(self, pil_img):
        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.tk_image, text="")
        self.show_card_details_button.pack(pady=(0, 8))
        self.add_to_deck_button.pack(pady=(0, 8))

    def open_card_details_window(self):
        if not self.active_card_id:
            return

        CardDetailsWindow(self.controller, self.active_card_id)

    def add_selected_card_to_deck(self):
        """Adds one copy of selected card to the user deck"""
        deck_id = self.controller.current_user_deck_id

        if not deck_id or not self.active_card_id:
            return

        success = add_card_to_user_deck(
            deck_id=deck_id,
            card_id=self.active_card_id,
            quantity=1
        )

        if not success:
            return

        # Preserves selection in both lists
        self.refresh_deck_view(preserve_search=True, preserve_deck=True, target_deck_card_id = self.active_card_id)

    def on_deck_card_selected(self, event):
        """Stores currently selected card from the user's deck list and loads image"""
        selection = self.deck_cards_list.curselection()

        if not selection:
            self.selected_deck_card_id = None
            self.selected_deck_card_name = None
            return

        card = self.displayed_deck_cards[selection[0]]
        if card is None:
            self.deck_cards_list.selection_clear(selection[0])
            return

        card_id, card_name, quantity, card_type, section = card
        self.selected_deck_card_id = card_id
        self.selected_deck_card_name = card_name
        self.active_card_id = card_id

        if not card_id:
            self.tk_image = None
            self.image_label.config(image=self.placeholder_image, text="")
            self.image_label.image = self.placeholder_image
            self.show_card_details_button.pack_forget()
            self.add_to_deck_button.pack_forget()
            return

        threading.Thread(
            target=self.load_image_async,
            args=(card_id,),
            daemon=True  # Background Processing
        ).start()


    def remove_one_copy(self):
        deck_id = self.controller.current_user_deck_id

        if not deck_id or (self.selected_deck_card_id is None and not self.selected_deck_card_name):
            return

        selected = None
        for card_id, card_name, quantity, card_type, section in self.current_deck_cards:
            if card_id == self.selected_deck_card_id and card_name == self.selected_deck_card_name:
                selected = (card_id, card_name, quantity, card_type, section)
                break

        if not selected:
            return

        card_id, card_name, quantity, _, _ = selected

        new_quantity = quantity - 1

        update_user_deck_card_quantity(
            deck_id=deck_id,
            quantity=new_quantity,
            card_id=card_id,
            card_name=None if card_id is not None else card_name
        )

        self.refresh_deck_view(preserve_search=True, preserve_deck=True)

    def remove_selected_card_from_deck(self):
        """Removes all copies of card from deck"""
        deck_id = self.controller.current_user_deck_id

        if not deck_id or (self.selected_deck_card_id is None and not self.selected_deck_card_name):
            return

        remove_card_from_user_deck(
            deck_id=deck_id,
            card_id=self.selected_deck_card_id,
            card_name=None if self.selected_deck_card_id is not None else self.selected_deck_card_name
        )

        self.refresh_deck_view(preserve_search=True, preserve_deck=True)

    def refresh_deck_view(self, preserve_search=True, preserve_deck=True, target_deck_card_id = None):
        """Refreshes deck area while preserving previous selections if one copy of card is removed"""
        previous_search_card_id = self.active_card_id if preserve_search else None

        if target_deck_card_id is not None:
            previous_deck_card_id = target_deck_card_id
            previous_deck_card_name = None
        else:
            previous_deck_card_id = self.selected_deck_card_id if preserve_deck else None
            previous_deck_card_name = self.selected_deck_card_name if preserve_deck else None

        self.load_user_deck()

        if preserve_search:
            self.restore_search_selection(previous_search_card_id)

        if preserve_deck:
            self.restore_deck_selection(previous_deck_card_id, previous_deck_card_name)

    def restore_search_selection(self, previous_card_id):
        """Restores previous search selection after list is refreshed"""
        if not previous_card_id:
            return

        for index, card in enumerate(self.current_found_cards):
            if card[0] == previous_card_id:
                self.search_results_list.selection_clear(0, tk.END)
                self.search_results_list.selection_set(index)
                self.search_results_list.activate(index)
                self.search_results_list.see(index)
                self.active_card_id = previous_card_id

                return

    def restore_deck_selection(self, previous_card_id, previous_card_name=None):
        """Restores deck selection if deck list is refreshed. When adding cards by the left side, we add by ID instead"""
        if previous_card_id is None and not previous_card_name:
            return

        for index, card in enumerate(self.displayed_deck_cards):
            if card is None:
                continue

            card_id, card_name, quantity, card_type, section = card
            match_by_id = previous_card_id is not None and card_id == previous_card_id
            match_by_name = previous_card_id is None and previous_card_name and card_name == previous_card_name

            if match_by_id or match_by_name:
                self.deck_cards_list.selection_clear(0, tk.END)
                self.deck_cards_list.selection_set(index)
                self.deck_cards_list.activate(index)
                self.deck_cards_list.see(index)
                self.selected_deck_card_id = card_id
                self.selected_deck_card_name = card_name
                return

        self.selected_deck_card_id = None
        self.selected_deck_card_name = None

    def go_back(self):
        """Returns to User Decks Screen and loads all their decks"""
        self.controller.frames["CustomDecksFrame"].load_user_decks()
        self.controller.show_frame("CustomDecksFrame")

    def update_scroll_visibility(self, listbox, scrollbar):
        """Hide scrollbar when all items fit in the listbox."""
        listbox.update_idletasks()
        first, last = listbox.yview()

        if first <= 0.0 and last >= 1.0:
            scrollbar.pack_forget()
        else:
            scrollbar.pack(side="right", fill="y")