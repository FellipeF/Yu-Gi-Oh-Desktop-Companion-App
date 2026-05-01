import tkinter as tk
import random

from tkinter import ttk, messagebox
from collections import Counter

class DuelMonstersDeckWindow(tk.Toplevel):
    def __init__(self, master, controller, selected_deck, original_selected_deck, card_pool):
        super().__init__(master)

        self.controller = controller
        self.selected_deck = selected_deck
        self.original_selected_deck = original_selected_deck
        self.card_pool = card_pool
        self.current_deck = None

        try:
            self.current_deck = self.generate_deck(self.card_pool)
        except ValueError as error:
            messagebox.showerror(self.controller.t("generate_deck"), str(error))
            self.destroy()
            return

        self.title(self.controller.t("deck_generator"))
        self.geometry("420x600")
        self.resizable(False, False)

        title_label = tk.Label(
            self,
            text=self.controller.t("generated_deck"),
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)

        self.generate_button = tk.Button(
            self,
            text=self.controller.t("generate_another_deck"),
            command=self.generate
        )
        self.generate_button.pack(pady=5)

        list_container = tk.Frame(self)
        list_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.deck_listbox = tk.Listbox(
            list_container,
            font=("Tahoma", 12),
            exportselection=False
        )
        self.deck_listbox.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=self.deck_listbox.yview
        )
        self.scrollbar.pack(side="right", fill="y")

        self.deck_listbox.config(yscrollcommand=self.scrollbar.set)

        self.status_label = tk.Label(self, font=("Arial", 11))
        self.status_label.pack(pady=5)

        self.show_deck()

    def build_card_lookup(self):
        """Builds a lookup with the English name as a key and translated card data as the value. The ID bridges
        both the probability pool and the Database"""
        lookup = {}

        translated_by_id = {
            card_id: {
                "id": card_id,
                "name": card_name,
                "type": card_type
            }
            for card_id, card_name, _qty, card_type in self.selected_deck["cards"]
        }

        for card_id, original_name, _qty, card_type in self.original_selected_deck["cards"]:
            card_data = translated_by_id.get(card_id)

            if card_data is None:
                continue

            lookup[original_name.lower()] = card_data

        return lookup

    def generate(self):
        try:
            self.current_deck = self.generate_deck(self.card_pool)
            self.show_deck()
        except ValueError as error:
            messagebox.showerror(self.controller.t("generate_deck"), str(error))

    def show_deck(self):
        self.deck_listbox.delete(0, tk.END)

        for (card_id, card_name, card_type), quantity in sorted(
                self.current_deck.items(),
                key=lambda item: item[0][1].lower()
        ):
            self.deck_listbox.insert(tk.END, f"{quantity}x {card_name}")

        total_cards = sum(self.current_deck.values())
        self.status_label.config(text=f"Total: {total_cards} {self.controller.t('cards')}")

    def generate_deck(self, card_pool, deck_size=40, max_copies=3):

        lookup = self.build_card_lookup()

        available_pool = []

        for card_name, weight in card_pool:
            card_data = lookup.get(card_name.lower())

            if card_data is not None:
                available_pool.append((card_data, weight))

        if len(available_pool) * max_copies < deck_size:
            raise ValueError(self.controller.t("not_enough_cards"))

        deck = Counter()

        cards = [card_data for card_data, _weight in available_pool]
        weights = [weight for _card_data, weight in available_pool]

        while sum(deck.values()) < deck_size:
            selected_card = random.choices(cards, weights=weights, k=1)[0]

            card_id = selected_card["id"]
            card_name = selected_card["name"]
            card_type = selected_card["type"]

            key = (card_id, card_name, card_type)

            if deck[key] < max_copies:
                deck[key] += 1

        return deck