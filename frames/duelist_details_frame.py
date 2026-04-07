import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import json

from database.queries import get_decks_by_duelist
from utils.card_image_loader import load_card_pil_image
from utils.resource_path import resource_path
from ui.card_details_window import CardDetailsWindow
from config import CARD_HEIGHT, CARD_WIDTH

class DuelistDetailsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.current_duelist_id = None
        self.current_duelist_key = None
        self.tk_image = None
        self.current_deck_index = None
        self.selected_card_id = None
        self.decks_data = []
        self.current_cards = []
        self.placeholder_image = ImageTk.PhotoImage(
            Image.open(resource_path("images/placeholder.jpg")).resize((CARD_WIDTH, CARD_HEIGHT))
        )

        # TODO: Add checkbox: Show Complete Decks only

        self.duelist_decks_label = tk.Label(self, font=("Arial", 16))
        self.duelist_decks_label.pack(pady=10)

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True)

        # Left side: deck and card list
        left_frame = tk.Frame(main_container)
        left_frame.pack(side="left", padx=10, fill="both", expand=True)

        decks_container = tk.Frame(left_frame)
        decks_container.pack(fill="x", pady=5)

        self.decks_listbox = tk.Listbox(decks_container, height=5, exportselection=False)
        self.decks_listbox.pack(side="left", fill="x", expand=True)
        self.decks_listbox.bind("<<ListboxSelect>>", self.on_deck_select)

        self.decks_scroll = ttk.Scrollbar(
            decks_container,
            orient="vertical",
            command=self.decks_listbox.yview
        )
        self.decks_scroll.pack(side="right", fill="y")
        self.decks_listbox.config(yscrollcommand=self.decks_scroll.set, font=("Tahoma", 12))

        self.export_deck_button = tk.Button(
            left_frame,
            width=14,
            command = self.export_selected_deck
        )
        self.export_deck_button.pack(anchor="e", pady=(0, 8), padx=10)
        self.export_deck_button.pack_forget()

        cards_container = tk.Frame(left_frame)
        cards_container.pack(fill="both", expand=True, pady=5)

        self.cards_listbox = tk.Listbox(cards_container, exportselection=False, height=18)
        self.cards_listbox.pack(side="left", fill="both", expand=True)
        self.cards_listbox.bind("<<ListboxSelect>>", self.show_card_image)

        self.cards_scroll = ttk.Scrollbar(
            cards_container,
            orient="vertical",
            command=self.cards_listbox.yview
        )
        self.cards_scroll.pack(side="right", fill="y")
        self.cards_listbox.config(yscrollcommand=self.cards_scroll.set, font=("Tahoma", 12))
        self.cards_listbox.pack_forget()
        self.cards_scroll.pack_forget()

        # Right side: deck status + image + card details button
        right_frame = tk.Frame(main_container, width=CARD_WIDTH + 90)
        right_frame.pack(side="right", padx=15, pady=25, fill="y")
        right_frame.pack_propagate(False)

        self.deck_status_label = tk.Label(
            right_frame,
            font=("Arial", 12, "bold"),
            text="",
            wraplength=CARD_WIDTH + 90,
            justify="center",
            anchor="center"
        )
        self.deck_status_label.pack(pady=(0, 9))

        image_container = tk.Frame(right_frame, width=CARD_WIDTH, height=CARD_HEIGHT)
        image_container.pack(pady=(0, 8))
        image_container.pack_propagate(False)

        self.image_label = tk.Label(image_container, anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.show_card_details = tk.Button(
            right_frame,
            command=self.open_card_details_window,
        )
        self.show_card_details.pack()
        self.show_card_details.pack_forget()

        # Bottom checkbox for exclusive cards
        self.show_exclusive_cards = tk.BooleanVar(value=True)
        self.exclusive_cards_checkbox = tk.Checkbutton(
            self,
            font=("Tahoma", 12),
            variable=self.show_exclusive_cards,
            command=self.reload_deck_cards
        )
        self.exclusive_cards_checkbox.pack(pady=5)

        self.refresh_ui()

    def export_selected_deck(self):
        """Exports selected deck to a .json file."""

        # Since button is not available when a deck is not selected, no need for checking this:

        #if self.current_deck_index is None:
        #    messagebox.showwarning(self.controller.t("export_deck"),self.controller.t("select_deck_first"))
        #    return

        if not self.decks_data or self.current_deck_index >= len(self.decks_data):
            messagebox.showwarning(self.controller.t("export_deck"), self.controller.t("no_deck_to_export"))
            return

        selected_deck = self.decks_data[self.current_deck_index]
        # Using deck key to suggest name of the file when exporting alongside Duelist Name
        deck_key = selected_deck["deck_key"]
        # Deck name is used to suggest name of the file when importing alongside Duelist Name
        deck_name = selected_deck["deck_name"]

        export_data = {
            "duelist": self.controller.t(self.current_duelist_key),
            "deck_name": deck_name,
            "cards": []
        }

        for card_id, card_name, qty in selected_deck["cards"]:
            export_data["cards"].append({
                "id": card_id,
                "name": card_name,
                "quantity": qty
            })

        default_filename = f"{self.current_duelist_key}_{deck_key}.json".lower().replace(" ", "_")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=default_filename,
            title=self.controller.t("export_deck")
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)

            messagebox.showinfo(
                self.controller.t("export_deck"),
                self.controller.t("deck_export_success").format(path=file_path)
            )
        except Exception as e:
            messagebox.showerror(self.controller.t("export_deck"),
                                 self.controller.t("deck_export_fail").format(error=str(e))
            )

    def clear_right_panel(self):
        """Prevents Image, Status and card details button to show up when changing duelist"""
        self.selected_card_id = None
        self.tk_image = None
        self.image_label.image = None
        self.image_label.config(image="", text=self.controller.t("select_card"))
        self.deck_status_label.config(text="", fg="black")
        self.show_card_details.pack_forget()

    def update_scroll_visibility(self, listbox, scrollbar):
        """Hide scrollbar when all items fit in the listbox."""
        listbox.update_idletasks()
        first, last = listbox.yview()

        if first <= 0.0 and last >= 1.0:
            scrollbar.pack_forget()
        else:
            scrollbar.pack(side="right", fill="y")

    def open_card_details_window(self):
        if not self.selected_card_id:
            return
        CardDetailsWindow(self.controller, self.selected_card_id)

    def set_duelist(self, duelist_id, duelist_key):
        self.current_duelist_id = duelist_id
        self.current_duelist_key = duelist_key

        self.refresh_ui()
        self.load_duelist()

    def load_duelist(self):
        """Load duelist name and cards for currently selected deck"""
        if not self.current_duelist_id:
            return

        self.current_deck_index = None
        self.current_cards = []
        self.selected_card_id = None

        self.decks_listbox.delete(0, tk.END)
        self.cards_listbox.delete(0, tk.END)
        self.decks_listbox.selection_clear(0, tk.END)
        self.cards_listbox.selection_clear(0, tk.END)

        self.cards_listbox.pack_forget()
        self.cards_scroll.pack_forget()
        self.export_deck_button.pack_forget()

        self.clear_right_panel()

        self.decks_data = get_decks_by_duelist(
            self.current_duelist_id,
            self.controller.current_language,
            show_exclusive_cards=self.show_exclusive_cards.get()
        )

        if not self.decks_data:
            self.decks_listbox.insert(tk.END, self.controller.t("no_decks_found"))
            self.update_scroll_visibility(self.decks_listbox, self.decks_scroll)
            return

        for deck in self.decks_data:
            self.decks_listbox.insert(tk.END, deck["deck_name"])

        self.update_scroll_visibility(self.decks_listbox, self.decks_scroll)

    def load_selected_deck_cards(self):
        """Load cards from deck that is currently selected"""
        if self.current_deck_index is None:
            return

        selected_deck = self.decks_data[self.current_deck_index]
        self.cards_listbox.delete(0, tk.END)
        self.current_cards = selected_deck["cards"]

        for card_id, card_name, qty in self.current_cards:
            self.cards_listbox.insert(tk.END, f"{qty}x {card_name}")

        self.cards_listbox.pack(side="left", fill="both", expand=True)
        self.update_scroll_visibility(self.cards_listbox, self.cards_scroll)
        self.update_deck_status()

    def clear_card_selection(self):
        """Clear details when other deck is selected"""
        self.selected_card_id = None
        self.tk_image = None
        self.cards_listbox.selection_clear(0, tk.END)
        self.image_label.image = None
        self.image_label.config(image="", text=self.controller.t("select_card"))
        self.show_card_details.pack_forget()

    def restore_selected_card(self, previous_card_id):
        """Preserves card selection only if it's not an exclusive card, so to not have inconsistent details
        being passed when the show exclusive cards checkbox is checked"""
        if not previous_card_id:
            self.clear_card_selection()
            return

        for index, (card_id, card_name, qty) in enumerate(self.current_cards):
            if card_id == previous_card_id:
                self.selected_card_id = card_id
                self.cards_listbox.selection_clear(0, tk.END)
                self.cards_listbox.select_set(index)
                self.cards_listbox.activate(index)
                self.cards_listbox.see(index)
                self.show_card_image(None)
                return

        self.clear_card_selection()

    def on_deck_select(self, event):
        selection = self.decks_listbox.curselection()
        if not selection:
            return

        self.current_deck_index = selection[0]
        self.export_deck_button.pack(anchor="e", pady=(0, 8), padx=10)
        self.load_selected_deck_cards()
        self.clear_card_selection()

    def update_deck_status(self):
        """Controls label to show decks status. Since it counts the total of shown items instead of doing a
        SELECT COUNT(*) for each deck on the database, when the checkbox exclusive cards is marked,
        this status may change. May need to investigate this further."""
        total_cards = sum(qty for _, _, qty in self.current_cards)

        if total_cards >= 40:
            self.deck_status_label.config(
                text=self.controller.t("complete_deck"),
                fg="green"
            )
        else:
            self.deck_status_label.config(
                text=self.controller.t("incomplete_deck"),
                fg="red"
            )

    def show_card_image(self, event):
        """Shows card image invoking async function. If no card is found in the API, shows a placeholder instead"""
        selection = self.cards_listbox.curselection()
        if not selection:
            return

        card = self.current_cards[selection[0]]
        card_id, card_name, qty = card
        self.selected_card_id = card_id

        if not card_id:
            self.tk_image = None
            self.image_label.config(image=self.placeholder_image, text="")
            self.image_label.image = self.placeholder_image
            self.show_card_details.pack_forget()
            return

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
        self.image_label.image = self.tk_image
        self.image_label.config(image=self.tk_image, text="")
        self.show_card_details.pack()

    def reload_deck_cards(self):
        """Load deck contents again for this particular duelist to show/hide non-TCG/OCG Cards"""
        if not self.current_duelist_id:
            return

        if self.current_deck_index is None:
            return

        previous_index = self.current_deck_index
        previous_scroll = self.decks_listbox.yview()
        previous_card_id = self.selected_card_id

        self.decks_data = get_decks_by_duelist(
            self.current_duelist_id,
            self.controller.current_language,
            show_exclusive_cards=self.show_exclusive_cards.get()
        )

        self.decks_listbox.delete(0, tk.END)

        for deck in self.decks_data:
            self.decks_listbox.insert(tk.END, deck["deck_name"])

        self.update_scroll_visibility(self.decks_listbox, self.decks_scroll)

        if previous_index < len(self.decks_data):
            self.current_deck_index = previous_index

            self.decks_listbox.selection_clear(0, tk.END)
            self.decks_listbox.select_set(previous_index)
            self.decks_listbox.activate(previous_index)
            self.decks_listbox.see(previous_index)

            if previous_scroll:
                self.decks_listbox.yview_moveto(previous_scroll[0])

            self.load_selected_deck_cards()
            self.restore_selected_card(previous_card_id)
        else:
            self.current_deck_index = None
            self.current_cards = []
            self.cards_listbox.delete(0, tk.END)
            self.clear_right_panel()

    def refresh_ui(self):
        self.exclusive_cards_checkbox.config(text=self.controller.t("show_exclusive_cards"))
        self.show_card_details.config(text=self.controller.t("card_details"))
        self.export_deck_button.config(text=self.controller.t("export_deck"))
        self.duelist_decks_label.config(
            text=self.controller.t("duelist_decks").format(name=self.controller.t(self.current_duelist_key))
        )

        if self.tk_image is None and self.image_label.cget("image") == "":
            self.image_label.config(text=self.controller.t("select_card"))