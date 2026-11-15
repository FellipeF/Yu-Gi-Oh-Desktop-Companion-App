import tkinter as tk

from tkinter import ttk
from ui.card_details_window import CardDetailsWindow
from ui.card_gallery import CardGallery
from config import CARD_WIDTH, CARD_HEIGHT
from utils.search_bar import SearchBar

class CardsFrame(tk.Frame):
    def __init__(self, parent, controller):
        """Frame where user can search for all available cards fetched from the API and stored in the Database"""
        super().__init__(parent)

        #TODO: Add Filters and Order by different parameters
        self.controller = controller
        self.image_handler = controller.image_handler

        self.current_cards = []
        self.tk_image = None
        self.selected_card_id = None

        # Implementing debounce
        self._filter_after_id = None

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=15, pady=10)

        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=0)
        main_container.rowconfigure(0, weight=0)
        main_container.rowconfigure(1, weight=1)

        #Left Side - Title and Search Box
        left_header = tk.Frame(main_container)
        left_header.grid(row=0, column=0, sticky="ew", padx=(0, 20), pady=(0, 8))

        self.title_label = tk.Label(left_header, font=("Arial", 14, "bold"), anchor="w")
        self.title_label.pack(side="left")

        self.search_var = tk.StringVar()

        self.search_bar = SearchBar(
            left_header,
            textvariable=self.search_var,
            placeholder=self.controller.t("search_for_card"),
            on_change=self.on_search_text_changed,
            width=50
        )
        self.search_bar.pack(anchor="w", fill="x")

        # Left Side - Cards Gallery
        gallery_container = tk.Frame(main_container)
        gallery_container.grid(row=1, column=0, sticky="nsew", padx=(0, 20))

        self.card_gallery = CardGallery(
            gallery_container,
            image_handler=self.image_handler,
            on_select=self.select_card,
            on_double_click=self.open_card_by_id,
        )

        self.card_gallery.pack(fill="both", expand=True)

        #Right Side - Card Preview
        right_frame = tk.Frame(main_container, width=320)
        right_frame.grid(row=1, column=1, sticky="n", padx=(10,0))
        right_frame.grid_propagate(False)

        image_container = tk.Frame(right_frame, width=CARD_WIDTH, height=CARD_HEIGHT)
        image_container.pack(pady=(0,12))
        image_container.pack_propagate(False)

        self.image_label = tk.Label(image_container,text="",anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.show_card_details = tk.Button(
            right_frame,
            font=("Tahoma", 12),
            command= self.open_card_details_window,
            cursor="hand2"
        )
        self.show_card_details.pack(pady=(0,10))
        self.show_card_details.pack_forget()    #Not on refresh UI so that button doesn't disappear when switching language

        self.refresh_ui()
        self.load_cards()

    def on_search_text_changed(self, *args):
        if self._filter_after_id is not None:
            self.after_cancel(self._filter_after_id)

        self._filter_after_id = self.after(250, self.filter_cards)

    def filter_cards(self):
        """Controls the Search Box"""
        self._filter_after_id = None

        name = self.search_bar.get_text()
        language = self.controller.current_language

        if name.strip():
            self.current_cards = self.controller.card_search_service.search(
                text=name,
                language_code=language,
            )
        else:
            self.current_cards = self.controller.card_search_service.get_all_cards(language)

        self.update_gallery(preserve_selection=True)

    def update_gallery(self, preserve_selection=False):
        self.card_gallery.set_cards(self.current_cards, preserve_selection=preserve_selection)

        gallery_selected_id = self.card_gallery.selected_card_id

        if gallery_selected_id is not None:
            self.selected_card_id = gallery_selected_id
        else:
            self.clear_selection()

    def select_card(self, card_id):
        if card_id is None:
            return

        if card_id == self.selected_card_id: #Prevents loading image when its already loaded
            return

        self.selected_card_id = card_id
        self.show_card_details.pack(pady=(0,10))

        self.tk_image = self.image_handler.get_placeholder(CARD_WIDTH, CARD_HEIGHT) #While loading
        self.image_label.config(image=self.tk_image, text="")
        self.image_handler.load_async(self, card_id, self._on_image_loaded)

    def clear_selection(self):
        self.selected_card_id = None
        self.tk_image = None

        self.image_label.config(image="", text=self.controller.t("select_card"))
        self.image_label.image = None
        self.show_card_details.pack_forget()

    def _on_image_loaded(self, card_id, tk_img):
        if not self.winfo_exists():
            return

        if card_id != self.selected_card_id:
            return

        if tk_img is None:
            tk_img = self.image_handler.get_placeholder(CARD_WIDTH, CARD_HEIGHT)

        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")
        self.image_label.image = self.tk_image

    def open_card_by_id(self, card_id):
        if card_id is None:
            return

        self.selected_card_id = card_id
        self.open_card_details_window()

    def open_card_details_window(self):
        if self.selected_card_id is None:
            return

        CardDetailsWindow(self.controller, self.selected_card_id)

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("search_card"))
        self.search_bar.placeholder = self.controller.t("search_for_card")

        if self.search_bar.placeholder_active:
            self.search_bar.set_placeholder()

        self.show_card_details.config(text=self.controller.t("card_details"))

        if self.selected_card_id is None:
            self.image_label.config(text=self.controller.t("select_card"))

    def load_cards(self, preserve_selection=False):
        """Load cards in the list based on the currently selected language. In case user knows the name only in the
        original version, allows to search for the card and preserve selection when returning to their language."""
        language = self.controller.current_language

        self.current_cards = self.controller.card_search_service.get_all_cards(language)
        self.update_gallery(preserve_selection=preserve_selection)