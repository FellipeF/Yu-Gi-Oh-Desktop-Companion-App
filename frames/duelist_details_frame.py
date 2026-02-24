import tkinter as tk
from PIL import Image, ImageTk
import threading
import cache_image
from database.models import get_decks_by_duelist
from utils.resource_path import resource_path
from ui.card_details_window import CardDetailsWindow

CARD_WIDTH = 250
CARD_HEIGHT = 420

class DuelistDetailsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.current_duelist_id = None
        self.current_duelist_name = None
        self.tk_image = None
        self.current_deck_index = None
        self.selected_card_id = None
        self.decks_data = []
        self.current_cards = []
        self.placeholder_image = ImageTk.PhotoImage(
            Image.open(resource_path("images/placeholder.jpg")).resize((CARD_WIDTH, CARD_HEIGHT))
        )

        #TODO: Check if Refactor is possible with some of the cards_frame.py code
        #TODO: Add checkbox: Show Complete Decks only
        #TODO: Show current selected deck

        self.duelist_decks_label = tk.Label(self, font=("Arial", 16))
        self.duelist_decks_label.pack(pady=10)

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True)

        #Left side: deck and card list
        left_frame = tk.Frame(main_container)
        left_frame.pack(side="left", padx=10, fill="both", expand=True)

        self.decks_listbox = tk.Listbox(left_frame, height=5)
        self.decks_listbox.pack(fill="x", pady=5)
        self.decks_listbox.bind("<<ListboxSelect>>", self.on_deck_select)

        self.cards_listbox = tk.Listbox(left_frame)
        self.cards_listbox.pack(fill="both", expand=True, pady=5)
        self.cards_listbox.bind("<<ListboxSelect>>", self.show_card_image)

        #Right side: image + card details button
        right_frame = tk.Frame(main_container, width=CARD_WIDTH)
        right_frame.pack(side="right", padx=15, pady=50, fill="y")
        right_frame.pack_propagate(False)

        self.image_label = tk.Label(right_frame, anchor="center")
        self.image_label.pack(side="top", fill="both", expand=True)

        self.show_card_details = tk.Button(
            right_frame,
            command=self.open_card_details_window,
        )

        #Bottom button for exclusive cards
        self.show_exclusive_cards = tk.BooleanVar(value=True)
        self.exclusive_cards_checkbox = tk.Checkbutton(
            self,
            variable=self.show_exclusive_cards,
            command=self.reload_deck_cards
        )

        self.exclusive_cards_checkbox.pack(pady=5)

        self.return_button = tk.Button(
            self,
            command=lambda: controller.show_frame("DuelistsFrame")
        )
        self.return_button.pack(pady=10)

        self.refresh_ui()

    def open_card_details_window(self):
        if not self.selected_card_id:
            return
        CardDetailsWindow(self.controller, self.selected_card_id)

    def set_duelist(self, duelist_id, duelist_name):
        self.current_duelist_id = duelist_id
        self.current_duelist_name = duelist_name

        self.refresh_ui()
        self.load_duelist()

    def load_duelist(self):
        if not self.current_duelist_id:
            return

        self.decks_listbox.delete(0, tk.END)
        self.cards_listbox.delete(0, tk.END)
        self.image_label.config(image="", text=self.controller.t("select_card"))

        self.decks_data = get_decks_by_duelist(self.current_duelist_id,
                                               language=self.controller.current_language,
                                               show_exclusive_cards=self.show_exclusive_cards.get()
                                               )

        #TODO: This is Fallback for empty decks on duelists, but final version should never have empty ones. Currently throws an Out of Index error when accessing empty duelists
        if not self.decks_data:
            self.decks_listbox.insert(tk.END, self.controller.t("no_decks_found"))
            return

        for deck in self.decks_data:
            self.decks_listbox.insert(tk.END, deck["deck_name"])

    def on_deck_select(self, event):
        selection = self.decks_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.current_deck_index = index
        selected_deck = self.decks_data[index]

        self.cards_listbox.delete(0, tk.END)
        self.current_cards = selected_deck["cards"]

        for card_id, card_name, qty in self.current_cards:
            display_name = card_name
            self.cards_listbox.insert(tk.END, f"{qty}x {display_name}")

    def show_card_image(self, event):
        selection = self.cards_listbox.curselection()
        if not selection:
            return

        self.show_card_details.pack()
        card = self.current_cards[selection[0]]
        card_id, name, qty = card
        self.selected_card_id = card_id

        if not card_id:
            self.image_label.config(image=self.placeholder_image)
            self.show_card_details.pack_forget()
            self.image_label.image = self.placeholder_image
            return

        threading.Thread(
            target=self.load_image_async,
            args=(card_id,),
            daemon=True
        ).start()

    def load_image_async(self, card_id):
        img_path = cache_image.get_card_image(card_id)

        img = Image.open(img_path).resize((CARD_WIDTH,CARD_HEIGHT))
        tk_img = ImageTk.PhotoImage(img)

        self.after(0, self.update_image_label, tk_img)

    def update_image_label(self, tk_img):
        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")

    def reload_deck_cards(self):
        if not self.current_duelist_id:
            return

        if self.current_deck_index is None:
            return

        self.decks_data = get_decks_by_duelist(self.current_duelist_id,
                                     language=self.controller.current_language,
                                     show_exclusive_cards = self.show_exclusive_cards.get()
                                     )

        self.decks_listbox.delete(0, tk.END)
        self.cards_listbox.delete(0, tk.END)

        for deck in self.decks_data:
            self.decks_listbox.insert(tk.END, deck["deck_name"])

        if self.current_deck_index < len(self.decks_data):
            self.decks_listbox.select_set(self.current_deck_index)
            self.decks_listbox.event_generate("<<ListboxSelect>>")

    def refresh_ui(self):
        self.exclusive_cards_checkbox.config(text=self.controller.t("show_exclusive_cards"))
        self.image_label.config(text=self.controller.t("select_card"))
        self.return_button.config(text=self.controller.t("return"))
        self.show_card_details.config(text=self.controller.t("card_details"))
        self.show_card_details.pack_forget()
        self.duelist_decks_label.config(text=self.controller.t("duelist_decks_dynamic").format(
            name=self.current_duelist_name))
