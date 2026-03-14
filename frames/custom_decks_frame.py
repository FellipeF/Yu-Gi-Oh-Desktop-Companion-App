import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from database.queries import (
    get_all_user_decks,
    create_user_deck,
    delete_user_deck,
    update_user_deck_used_flag,
)


class CustomDecksFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.selected_deck_id = None

        self.title_label = tk.Label(self, font=("Arial", 14))
        self.title_label.pack(pady=10)

        # Table container
        table_container = tk.Frame(self)
        table_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("name", "total_cards", "used")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=15
        )

        self.tree.heading("name", text="Deck Name")
        self.tree.heading("total_cards", text="Total Cards")
        self.tree.heading("used", text="Used")

        self.tree.column("name", width=280, anchor="w")
        self.tree.column("total_cards", width=110, anchor="center")
        self.tree.column("used", width=80, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_deck)
        self.tree.bind("<Double-1>", self.open_selected_deck)

        # Buttons
        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=10)

        self.new_button = tk.Button(
            buttons_frame,
            command=self.create_new_deck
        )
        self.new_button.grid(row=0, column=0, padx=5)

        self.edit_button = tk.Button(
            buttons_frame,
            command=self.open_selected_deck
        )
        self.edit_button.grid(row=0, column=1, padx=5)

        self.toggle_used_button = tk.Button(
            buttons_frame,
            command=self.toggle_used_selected_deck
        )
        self.toggle_used_button.grid(row=0, column=2, padx=5)

        self.delete_button = tk.Button(
            buttons_frame,
            command=self.delete_selected_deck
        )
        self.delete_button.grid(row=0, column=3, padx=5)

        self.return_button = tk.Button(
            self,
            command=lambda: controller.show_frame("HomeFrame")
        )
        self.return_button.pack(pady=10)

        self.refresh_ui()
        self.load_user_decks()

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("custom_decks"))

        self.tree.heading("name", text=self.controller.t("deck_name"))
        self.tree.heading("total_cards", text=self.controller.t("total_cards"))
        self.tree.heading("used", text=self.controller.t("used"))

        self.new_button.config(text=self.controller.t("new_deck"))
        self.edit_button.config(text=self.controller.t("edit"))
        self.toggle_used_button.config(text=self.controller.t("toggle_used"))
        self.delete_button.config(text=self.controller.t("delete"))
        self.return_button.config(text=self.controller.t("return"))

    def load_user_decks(self):
        self.tree.delete(*self.tree.get_children())
        self.selected_deck_id = None

        decks = get_all_user_decks()

        for deck_id, deck_name, is_used, total_cards in decks:
            used_text = self.controller.t("yes") if is_used else self.controller.t("no")

            self.tree.insert(
                "",
                tk.END,
                iid=str(deck_id),
                values=(deck_name, total_cards, used_text)
            )

    def on_select_deck(self, event=None):
        selection = self.tree.selection()

        if not selection:
            self.selected_deck_id = None
            return

        self.selected_deck_id = int(selection[0])

    def create_new_deck(self):
        deck_name = simpledialog.askstring(
            self.controller.t("new_deck"),
            self.controller.t("enter_deck_name"),
            parent=self
        )

        if not deck_name:
            return

        deck_name = deck_name.strip()

        if not deck_name:
            return

        try:
            create_user_deck(deck_name)
            self.load_user_decks()
        except Exception as e:
            messagebox.showerror(
                self.controller.t("error"),
                f"{self.controller.t('could_not_create_deck')}\n{e}"
            )

    def toggle_used_selected_deck(self):
        if not self.selected_deck_id:
            return

        item = self.tree.item(str(self.selected_deck_id))
        current_used_text = item["values"][2]
        current_used = current_used_text == self.controller.t("yes")

        update_user_deck_used_flag(self.selected_deck_id, not current_used)
        self.load_user_decks()

    def delete_selected_deck(self):
        if not self.selected_deck_id:
            return

        confirm = messagebox.askyesno(
            self.controller.t("delete_deck"),
            self.controller.t("confirm_delete_deck")
        )

        if not confirm:
            return

        delete_user_deck(self.selected_deck_id)
        self.load_user_decks()

    def open_selected_deck(self, event=None):
        if not self.selected_deck_id:
            return

        self.controller.current_user_deck_id = self.selected_deck_id
        self.controller.frames["CustomDeckEditorFrame"].load_user_deck()
        self.controller.show_frame("CustomDeckEditorFrame")