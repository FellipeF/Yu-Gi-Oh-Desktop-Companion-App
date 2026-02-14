import tkinter as tk
from api_client import load_cards

data = load_cards()
cards = data["data"]

class CardsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="Check Available Cards", font=("Arial", 14)).pack(pady=10)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_cards)

        entry = tk.Entry(self, textvariable=self.search_var, width=40)
        entry.pack()

        self.searchable_list = tk.Listbox(self, width=60, height=20)
        self.searchable_list.pack(pady=10)

        for card in cards:
            self.searchable_list.insert(tk.END, card["name"])

        tk.Button(self, text="Return", command=lambda: controller.show_frame("HomeFrame")).pack(pady=10)

    def filter_cards(self, *args):
        txt = self.search_var.get().lower()
        self.searchable_list.delete(0, tk.END)

        for card in cards:
            if txt in card["name"].lower():
                self.searchable_list.insert(tk.END, card["name"])

