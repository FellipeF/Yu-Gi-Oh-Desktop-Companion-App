import tkinter as tk
from PIL import Image, ImageTk
import threading
import cache_image
from database.models import get_decks_by_duelist
from utils.resource_path import resource_path

class DuelistDetailsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        #TODO: Use Duelist Description somewhere or delete it.
        #TODO: Check if Refactor is possible with some of the cards_frame.py code

        self.current_duelist_id = None
        self.current_duelist_name = None
        self.tk_image = None
        self.current_deck_index = None

        self.placeholder_image = ImageTk.PhotoImage(
            Image.open(resource_path("images/placeholder.jpg")).resize((200,290))
        )

        self.decks_data = []
        self.current_cards = []

        self.duelist_decks_label = tk.Label(self, font=("Arial", 16))
        self.duelist_decks_label.pack(pady=10)

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True)

        # LEFT SIDE
        left_frame = tk.Frame(main_container)
        left_frame.pack(side="left", padx=10, fill="both", expand=True)

        self.decks_listbox = tk.Listbox(left_frame, height=5)
        self.decks_listbox.pack(fill="x", pady=5)
        self.decks_listbox.bind("<<ListboxSelect>>", self.on_deck_select)

        self.cards_listbox = tk.Listbox(left_frame)
        self.cards_listbox.pack(fill="both", expand=True, pady=5)
        self.cards_listbox.bind("<<ListboxSelect>>", self.show_card_image)

        # RIGHT SIDE (image)
        right_frame = tk.Frame(main_container, width=220)
        right_frame.pack(side="right", padx=10, fill="y")
        right_frame.pack_propagate(False)

        self.show_anime_cards = tk.BooleanVar(value=True)
        self.anime_checkbox = tk.Checkbutton(
            self,
            text = "Show anime only cards",
            variable=self.show_anime_cards,
            command=self.reload_deck_cards
        )

        self.anime_checkbox.pack(pady=5)

        self.image_label = tk.Label(right_frame)
        self.image_label.pack(expand=True)

        self.stats_label = tk.Label(right_frame, text="")
        self.stats_label.pack(pady=5)

        self.return_button = tk.Button(
            self,
            command=lambda: controller.show_frame("DuelistsFrame")
        )
        self.return_button.pack(pady=10)

        self.refresh_ui()


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
                                               show_anime=self.show_anime_cards.get()
                                               )

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

        for card_id, card_name, atk, defense, qty in self.current_cards:
            display_name = card_name
            self.cards_listbox.insert(tk.END, f"{qty}x {display_name}")

    def show_card_image(self, event):
        selection = self.cards_listbox.curselection()
        if not selection:
            return

        card = self.current_cards[selection[0]]
        card_id, name, atk, defense, qty = card

        if not card_id:
            self.image_label.config(image=self.placeholder_image)
            self.image_label.image = self.placeholder_image

            self.update_stats_label(atk, defense)
            return

        threading.Thread(
            target=self.load_image_async,
            args=(card_id, atk, defense),
            daemon=True
        ).start()

    def load_image_async(self, card_id, atk, defense):
        img_path = cache_image.get_card_image(card_id)

        if not img_path:
            self.after(0, self.update_stats_label, atk, defense)
            return

        img = Image.open(img_path).resize((200, 300))
        tk_img = ImageTk.PhotoImage(img)

        self.after(0, self.update_image_label, tk_img)
        self.after(0, self.update_stats_label, atk, defense)

    def update_image_label(self, tk_img):
        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")

    def update_stats_label(self, atk, defense):
        if atk and defense:
            self.stats_label.config(text=f"ATK: {atk}    DEF: {defense}")
        else:
            self.stats_label.config(text="")

    def reload_deck_cards(self):
        if not self.current_duelist_id:
            return

        if self.current_deck_index is None:
            return

        self.decks_data = get_decks_by_duelist(self.current_duelist_id,
                                     language=self.controller.current_language,
                                     show_anime = self.show_anime_cards.get()
                                     )

        self.decks_listbox.delete(0, tk.END)
        self.cards_listbox.delete(0, tk.END)

        for deck in self.decks_data:
            self.decks_listbox.insert(tk.END, deck["deck_name"])

        if self.current_deck_index < len(self.decks_data):
            self.decks_listbox.select_set(self.current_deck_index)
            self.decks_listbox.event_generate("<<ListboxSelect>>")

    def refresh_ui(self):
        self.anime_checkbox.config(text=self.controller.t("show_anime_only"))
        self.image_label.config(text=self.controller.t("select_card"))
        self.return_button.config(text=self.controller.t("return"))
        self.stats_label.config(text="")

        if self.current_duelist_name:
            self.duelist_decks_label.config(
                text=self.controller.t("duelist_decks_dynamic").format(
                    name=self.current_duelist_name
                )
            )
        else:
            self.duelist_decks_label.config(text=self.controller.t("duelist_decks"))

