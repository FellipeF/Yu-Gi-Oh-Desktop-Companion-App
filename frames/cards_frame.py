import tkinter as tk

from tkinter import ttk
from ui.card_details_window import CardDetailsWindow
from config import CARD_WIDTH, CARD_HEIGHT

class CardsFrame(tk.Frame):
    def __init__(self, parent, controller):
        """Frame where user can search for all available cards fetched from the API and stored in the Database"""
        super().__init__(parent)

        #TODO: Add Filters and Order by different parameters

        self.current_cards = []
        self.controller = controller
        self.tk_image = None
        self.selected_card_id = None
        self.image_handler = controller.image_handler

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=5, pady=10)

        main_container.columnconfigure(0, weight=0)
        main_container.columnconfigure(1, weight=0)
        main_container.rowconfigure(0, weight=0)
        main_container.rowconfigure(1, weight=1)

        #Left Side - Title and Search Box
        left_header = tk.Frame(main_container, width=640)
        left_header.grid(row=0, column=0, sticky="w", padx=(0, 20), pady=(0, 10))
        left_header.grid_propagate(False)

        self.title_label = tk.Label(left_header, font=("Arial", 14))
        self.title_label.pack(anchor="w", pady=(0, 5))

        self.search_var = tk.StringVar()
        # Implementing debounce
        self._filter_after_id = None
        self.search_var.trace_add("write", self.on_search_text_changed)

        self.search_entry = tk.Entry(left_header, textvariable=self.search_var, width=50)
        self.search_entry.pack(anchor="w")

        # Left Side - Card List
        cards_container = tk.Frame(main_container, width=640, height=660)
        cards_container.grid(row=1, column=0, sticky="nsew", padx=(0,20))
        cards_container.grid_propagate(False)

        self.searchable_list = tk.Listbox(
            cards_container,
            width=50,
            font=("Tahoma", 12)
        )
        self.searchable_list.pack(side="left",fill="both", expand = True)

        self.cards_scroll = ttk.Scrollbar(cards_container, orient="vertical",)
        self.cards_scroll.pack(side="right", fill="y")

        self.searchable_list.config(yscrollcommand=self.cards_scroll.set)
        self.cards_scroll.config(command=self.searchable_list.yview)

        self.searchable_list.bind("<<ListboxSelect>>", self.show_card_image)

        #Right Side - Image and Button for Card Details
        right_frame = tk.Frame(main_container, width=300)
        right_frame.grid(row=1, column=1, sticky="n", padx=(10,0))
        right_frame.grid_propagate(False)

        image_container = tk.Frame(right_frame, width=CARD_WIDTH, height=CARD_HEIGHT)
        image_container.pack(pady=(0,10))
        image_container.pack_propagate(False)

        self.image_label = tk.Label(image_container,text="",anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.show_card_details = tk.Button(
            right_frame,
            font=("Tahoma", 12),
            command= self.open_card_details_window
        )
        self.show_card_details.pack(pady=(0,10))
        self.show_card_details.pack_forget()    #Not on refresh UI so that button doesn't disappear when switching language

        self.return_button = tk.Button(
            self,
            font=("Tahoma", 12),
            command=lambda: controller.show_frame("HomeFrame")
        )
        self.return_button.pack(pady=10)

        self.refresh_ui()
        self.load_cards()

    def on_search_text_changed(self, *args):
        if self._filter_after_id is not None:
            self.after_cancel(self._filter_after_id)

        self._filter_after_id = self.after(250, self.filter_cards)

    def filter_cards(self):
        """Controls the Search Box"""
        self._filter_after_id = None

        name = self.search_var.get()
        language = self.controller.current_language

        previous_card_id = self.selected_card_id

        if name.strip():
            self.current_cards = self.controller.card_search_service.search(
                text=name,
                language_code=language,
            )
        else:
            self.current_cards = self.controller.card_search_service.get_all_cards(language)

        self.searchable_list.delete(0, tk.END)

        new_index = None

        for index, card in enumerate(self.current_cards):
            self.searchable_list.insert(tk.END, card[1])

            if previous_card_id and card[0] == previous_card_id:
                new_index = index

        if new_index is not None:
            self.searchable_list.selection_clear(0, tk.END)
            self.searchable_list.selection_set(new_index)
            self.searchable_list.activate(new_index)
            self.searchable_list.see(new_index)

    def show_card_image(self, event):
        selection = self.searchable_list.curselection()
        if not selection:
            return

        card = self.current_cards[selection[0]]
        card_id = card[0]

        self.selected_card_id = card_id
        self.show_card_details.pack(pady=(0,10))

        self.image_handler.load_async(
            self,
            card_id,
            self._on_image_loaded
        )

    def _on_image_loaded(self, card_id, tk_img):
        if card_id != self.selected_card_id:
            return

        if tk_img is None:
            self.tk_image = self.image_handler.get_placeholder(CARD_WIDTH, CARD_HEIGHT)
            self.image_label.config(image=self.tk_image, text="")
            return

        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")
        self.image_label.image = self.tk_image # Avoids losing reference

    def open_card_details_window(self):
        if not self.selected_card_id:
            return
        CardDetailsWindow(self.controller, self.selected_card_id)

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("search_card"))
        self.image_label.config(text=self.controller.t("select_card"))
        self.show_card_details.config(text=self.controller.t("card_details"))
        self.return_button.config(text=self.controller.t("return"))

    def load_cards(self, preserve_selection=False):
        """Load cards in the list based on the currently selected language. In case user knows the name only in the
        original version, allows to search for the card and preserve selection when returning to their language."""
        language = self.controller.current_language
        selected_card_id = None

        if preserve_selection:
            selection = self.searchable_list.curselection()
            if selection:
                selected_card_id = self.current_cards[selection[0]][0]

        self.current_cards = self.controller.card_search_service.get_all_cards(language)
        self.searchable_list.delete(0, tk.END)

        new_index = None

        for index, card in enumerate(self.current_cards):
            self.searchable_list.insert(tk.END, card[1])

            if preserve_selection and card[0] == selected_card_id:
                new_index = index

        if new_index is not None:
            self.searchable_list.selection_set(new_index)
            self.searchable_list.see(new_index)