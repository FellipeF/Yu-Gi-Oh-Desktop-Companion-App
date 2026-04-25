import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json

from database.queries import (
    get_all_user_decks,
    create_user_deck,
    delete_user_deck,
    update_user_deck_used_flag,
    add_cards_bulk_import, rename_user_deck, get_user_deck_by_id, get_cards_by_user_deck
)
from utils.treeview_tooltip import TreeviewTooltip

class CustomDecksFrame(tk.Frame):
    def __init__(self, parent, controller):
        """A frame containing a tree that shows all the users imported/created decks, cards quantity and status.
        Allows to import, export, rename, delete and select a deck to edit its contents."""
        super().__init__(parent)

        self.controller = controller
        self.selected_deck_id = None
        self.current_column = None
        self.all_decks = []
        self.search_var = tk.StringVar()
        self.search_placeholder_active = True

        self.title_label = tk.Label(self, font=("Arial", 14))
        self.title_label.pack(pady=10)

        self.tree_style = ttk.Style()
        self.tree_style.configure(
            "Custom.Treeview",
            font=("Tahoma", 12),
            rowheight=28
        )
        self.tree_style.configure(
            "Custom.Treeview.Heading",
            rowheight=26,
            font=("Tahoma", 12, "bold")
        )

        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=(0,5))

        search_container = tk.Frame(search_frame)
        search_container.pack(side="left")

        self.search_label = tk.Label(search_container,text="🔎",font=("Segoe UI Emoji", 12))
        self.search_label.pack(side="left", padx=(0, 5))

        self.search_entry = tk.Entry(search_container,textvariable=self.search_var, font=("Tahoma",12), width=28)
        self.search_entry.pack(side="left")

        self.search_placeholder_text = self.controller.t("search_decks")
        self.search_entry.insert(0, self.search_placeholder_text)
        self.search_entry.config(fg="gray")

        self.search_entry.bind("<FocusIn>", self.clear_search_placeholder)
        self.search_entry.bind("<FocusOut>", self.restore_search_placeholder)
        self.search_entry.bind("<KeyRelease>", self.filter_decks)

        table_container = tk.Frame(self)
        table_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("name", "total_cards", "used", "edit", "rename", "delete")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=15,
            style="Custom.Treeview"
        )

        self.tooltip = TreeviewTooltip(self.tree, {
            "#4": self.controller.t("edit"),
            "#5": self.controller.t("rename_deck"),
            "#6": self.controller.t("delete"),
        })

        self.tree.heading("name", text=self.controller.t("deck_name"))
        self.tree.heading("total_cards", text=self.controller.t("total_cards"))
        self.tree.heading("used", text=self.controller.t("used"))
        self.tree.heading("edit", text="")
        self.tree.heading("rename", text="")
        self.tree.heading("delete", text="")

        self.tree.column("name", width=360, anchor="w")
        self.tree.column("total_cards", width=130, anchor="center")
        self.tree.column("used", width=80, anchor="center")
        self.tree.column("edit", width=28, stretch=False, anchor="center")
        self.tree.column("rename", width=28, stretch=False, anchor="center")
        self.tree.column("delete", width=28, stretch=False, anchor="center")

        self.tree.tag_configure("even", background="#eaeaea")
        self.tree.tag_configure("odd", background="#ffffff")

        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_deck_select)
        self.tree.bind("<Double-1>", self.open_selected_deck)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Motion>", self.on_motion_cursor, add="+") # So that cursor + tooltip both work together

        self.tree_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)

        buttons_frame = tk.Frame(self)
        buttons_frame.pack(fill="x", pady=5)

        buttons_frame.columnconfigure(0, weight=1)

        right_frame = tk.Frame(buttons_frame)
        right_frame.grid(row=0, column=1, sticky="e")

        self.new_button = tk.Button(
            right_frame,
            text="➕",
            font=("Segoe UI Emoji", 12),
            command=self.create_new_deck
        )
        self.new_button.pack(side="left", padx=3)

        self.import_button = tk.Button(
            right_frame,
            text="📥",
            font=("Segoe UI Emoji", 12),
            command=self.import_deck
        )
        self.import_button.pack(side="left", padx=3)

        self.export_button = tk.Button(
            right_frame,
            text="📤",
            font=("Segoe UI Emoji", 12),
            command=self.export_deck
        )
        self.export_button.pack(side="left", padx=3)

        self.add_tooltip(self.new_button, self.controller.t("new_deck"))
        self.add_tooltip(self.import_button, self.controller.t("import_deck"))
        self.add_tooltip(self.export_button, self.controller.t("export_deck"))

        self.return_button = tk.Button(
            self,
            font=("Tahoma", 12),
            command=lambda: self.return_home_screen()
        )
        self.return_button.pack(pady=10)

        self.refresh_ui()

    def clear_search_placeholder(self, event=None):
        if self.search_placeholder_active:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="black")
            self.search_placeholder_active = False

    def restore_search_placeholder(self, event=None):
        if not self.search_entry.get().strip():
            self.search_placeholder_text = self.controller.t("search_decks")
            self.search_entry.insert(0, self.search_placeholder_text)
            self.search_entry.config(fg="gray")
            self.search_placeholder_active = True
            self.render_decks(self.all_decks)

    def add_tooltip(self, widget, text):
        def enter(e):
            widget.tooltip = tk.Toplevel(widget)
            widget.tooltip.wm_overrideredirect(True)
            widget.tooltip.wm_geometry(f"+{e.x_root + 10}+{e.y_root + 10}")

            label = tk.Label(
                widget.tooltip,
                text=text,
                bg="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=("Tahoma", 9),
                padx=6,
                pady=3
            )
            label.pack()

        def leave(e):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def on_motion_cursor(self, event):
        column = self.tree.identify_column(event.x)

        if column in ("#4", "#5", "#6"):
            self.tree.config(cursor="hand2")
        else:
            self.tree.config(cursor="")

    def update_scroll_visibility(self):
        """Hide scrollbar when all items fit in the tree."""
        first, last = self.tree.yview()

        if first <= 0.0 and last >= 1.0:
            if self.tree_scroll.winfo_ismapped():
                self.tree_scroll.pack_forget()
        else:
            if not self.tree_scroll.winfo_ismapped():
                self.tree_scroll.pack(side="right", fill="y")

    def render_decks(self, decks):
        self.tree.delete(*self.tree.get_children())
        self.selected_deck_id = None

        for index, (deck_id, deck_name, is_used, main_count, extra_count) in enumerate(decks):
            used_text = "✅" if is_used else "⬜"
            tag = "even" if index % 2 == 0 else "odd"

            self.tree.insert(
                "",
                tk.END,
                iid=str(deck_id),
                values=(
                    deck_name,
                    f"{main_count} / {extra_count}",
                    used_text,
                    "✏️",
                    "📝",
                    "🗑️"
                ),
                tags=(tag,)
            )

        self.after(50, self.update_scroll_visibility)

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("custom_decks"))

        if self.search_placeholder_active:
            self.search_entry.delete(0, tk.END)
            self.search_placeholder_text = self.controller.t("search_decks")
            self.search_entry.insert(0, self.search_placeholder_text)

        self.tree.heading("name", text=self.controller.t("deck_name"))
        self.tree.heading("total_cards", text=self.controller.t("total_cards"))
        self.tree.heading("used", text=self.controller.t("used"))

        self.tooltip.tooltips = {
            "#4": self.controller.t("edit"),
            "#5": self.controller.t("rename_deck"),
            "#6": self.controller.t("delete"),
        }

        self.add_tooltip(self.new_button, self.controller.t("new_deck"))
        self.add_tooltip(self.import_button, self.controller.t("import_deck"))
        self.add_tooltip(self.export_button, self.controller.t("export_deck"))

        self.return_button.config(text=self.controller.t("return"))

        # For the used column
        self.load_user_decks()

    def load_user_decks(self):
        """Loads all the user decks into Treeview"""
        self.all_decks = get_all_user_decks()
        self.filter_decks()

    def filter_decks(self, event=None):
        if self.search_placeholder_active:
            self.render_decks(self.all_decks)
            return

        search_text = self.search_var.get().strip().lower()

        if not search_text:
            self.render_decks(self.all_decks)
            return

        filtered_decks = [
            deck for deck in self.all_decks
            if search_text in deck[1].lower()
        ]

        self.render_decks(filtered_decks)

    def on_tree_click(self, event):
        """Toggles checkbox when clicking the used column"""
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)

        if region != "cell" or not item_id:
            return

        self.selected_deck_id = int(item_id)
        self.tree.selection_set(item_id)
        self.tree.focus(item_id)

        if column == "#3":
            self.selected_deck_id = int(item_id)
            self.toggle_used_selected_deck()
            return "break"

        elif column == "#4":
            self.open_selected_deck()
            return "break"

        elif column == "#5":
            self.rename_selected_deck()
            return "break"

        elif column == "#6":
            self.delete_selected_deck()
            return "break"

    def on_deck_select(self, event=None):
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
            new_deck_id = create_user_deck(deck_name)

            self.load_user_decks()

            self.tree.selection_set(str(new_deck_id))
            self.tree.focus(str(new_deck_id))
            self.tree.see(str(new_deck_id))
            self.selected_deck_id = new_deck_id

        except Exception as e:
            self.treat_exception(e)

    def toggle_used_selected_deck(self):
        if not self.selected_deck_id:
            return

        item_id = str(self.selected_deck_id)
        item = self.tree.item(item_id)

        current_used_text = item["values"][2]
        current_used = current_used_text == "✅"
        new_used = not current_used

        update_user_deck_used_flag(self.selected_deck_id, new_used)

        values = list(item["values"])
        values[2] = "✅" if new_used else "⬜"
        self.tree.item(item_id, values=values)

    def delete_selected_deck(self):
        if not self.selected_deck_id:
            return

        confirm = messagebox.askyesno(
            self.controller.t("delete_deck"),
            self.controller.t("confirm_delete_deck")
        )

        if not confirm:
            return

        item_id = str(self.selected_deck_id)

        delete_user_deck(self.selected_deck_id)
        self.tree.delete(item_id)
        self.selected_deck_id = None

        self.update_scroll_visibility()

    def rename_selected_deck(self):
        if not self.selected_deck_id:
            return

        item_id = str(self.selected_deck_id)
        item = self.tree.item(item_id)
        current_name = item["values"][0]

        new_name = simpledialog.askstring(
            self.controller.t("rename_deck"),
            self.controller.t("enter_deck_name"),
            initialvalue=current_name,
            parent=self
        )

        if not new_name:
            return

        new_name = new_name.strip()

        if not new_name or new_name == current_name:
            return

        try:
            rename_user_deck(self.selected_deck_id, new_name)

            values = list(item["values"])
            values[0] = new_name
            self.tree.item(item_id, values=values)

        except Exception as e:
            self.treat_exception(e)

    def open_selected_deck(self, event=None):
        if not self.selected_deck_id:
            return

        self.controller.current_user_deck_id = self.selected_deck_id
        # Prevents user deck showing as empty when no refresh is done
        self.controller.frames["CustomDeckEditorFrame"].load_user_deck()
        self.controller.show_frame("CustomDeckEditorFrame")

    def import_deck(self):
        """Import JSON File and check if it's in the right formatting"""
        file_path = filedialog.askopenfilename(
            title=self.controller.t("import_deck"),
            filetypes=[("JSON files", "*.json")]
        )

        # Cancel Option was pressed
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror(
                self.controller.t("error"),
                self.controller.t("could_not_read_deck_file").format(error=str(e))
            )
            return

        # Check if file is in correct formatting of dictionary and object
        if not isinstance(data, dict):
            messagebox.showerror(
                self.controller.t("error"),
                self.controller.t("invalid_deck_file")
            )
            return

        # Check if file has required fields
        required_fields = ["duelist", "deck_name", "cards"]

        if not all(field in data for field in required_fields):
            messagebox.showerror(
                self.controller.t("error"),
                self.controller.t("invalid_deck_file")
            )
            return

        cards = data.get("cards")
        deck_name_from_file = data.get("deck_name")
        duelist_name = data.get("duelist")

        # If cards list is empty, return
        if not isinstance(cards, list) or not cards:
            messagebox.showerror(
                self.controller.t("error"),
                self.controller.t("invalid_deck_file")
            )
            return

        suggested_name = deck_name_from_file or self.controller.t("imported_deck")

        if duelist_name and deck_name_from_file:
            suggested_name = f"{duelist_name} - {deck_name_from_file}"

        new_deck_name = simpledialog.askstring(
            self.controller.t("import_deck"),
            self.controller.t("enter_imported_deck_name"),
            initialvalue=suggested_name,
            parent=self
        )

        if not new_deck_name:
            return

        new_deck_name = new_deck_name.strip()

        # Prevents empty deck names
        if not new_deck_name:
            return

        # Card Validation
        for card in cards:
            if not isinstance(card, dict):
                messagebox.showerror(
                    self.controller.t("error"),
                    self.controller.t("invalid_card_entry")
                )
                return

            if "name" not in card or "quantity" not in card:
                messagebox.showerror(
                    self.controller.t("error"),
                    self.controller.t("invalid_card_entry")
                )
                return

            card_name = card.get("name")
            quantity = card.get("quantity")

            if not isinstance(card_name, str) or not card_name.strip():
                messagebox.showerror(
                    self.controller.t("error"),
                    self.controller.t("invalid_card_entry")
                )
                return

            if not isinstance(quantity, int) or quantity <= 0:
                messagebox.showerror(
                    self.controller.t("error"),
                    self.controller.t("invalid_card_entry")
                )
                return

        new_deck_id = None

        try:
            new_deck_id = create_user_deck(new_deck_name)

            # When everything is validated, add the card to user deck by ID. This allows translation, instead
            # of adding it by name only. If no ID, again this means that it's an exclusive card.
            add_cards_bulk_import(new_deck_id, cards)

            self.load_user_decks()
            self.tree.selection_set(str(new_deck_id))
            self.tree.focus(str(new_deck_id))
            self.tree.see(str(new_deck_id))
            self.selected_deck_id = new_deck_id

            self.update_scroll_visibility()

            messagebox.showinfo(
                self.controller.t("import_deck"),
                self.controller.t("deck_imported_successfully").format(name=new_deck_name)
            )

        except Exception as e:

            # Rollback for in case deck is created, but still fails importing
            if new_deck_id is not None:
                try:
                    delete_user_deck(new_deck_id)
                except Exception:
                    pass

            self.treat_exception(e)

    def export_deck(self):
        """Export selected deck to a JSON file."""
        if not self.selected_deck_id:
            messagebox.showwarning(
                self.controller.t("export_deck"),
                self.controller.t("no_decks_to_export")
            )
            return

        deck = get_user_deck_by_id(self.selected_deck_id)

        if not deck:
            messagebox.showerror(
                self.controller.t("error"),
                self.controller.t("deck_not_found")
            )
            return

        _deck_id, deck_name, is_used = deck

        cards = get_cards_by_user_deck(
            self.selected_deck_id,
            self.controller.current_language
        )

        if not cards:
            messagebox.showwarning(
                self.controller.t("export_deck"),
                self.controller.t("no_deck_to_export")
            )
            return

        export_data = {
            "duelist": "Duelist",
            "deck_name": deck_name,
            "cards": []
        }

        for card_id, card_name, quantity, *_ in cards:
            export_data["cards"].append({
                "id": card_id,
                "name": card_name,
                "quantity": quantity
            })

        default_filename = f"{deck_name}.json".lower().replace(" ", "_")

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
            messagebox.showerror(
                self.controller.t("export_deck"),
                self.controller.t("deck_export_fail").format(error=str(e))
            )

    def return_home_screen(self):
        # This refresh_ui is here to avoid newly added decks not showing up on the count
        self.controller.frames["HomeFrame"].refresh_ui()
        self.controller.show_frame("HomeFrame")

    def treat_exception(self, e):
        """Exceptions when creating decks.
        Also reports to the user when UNIQUE Constraint for deck name is being violated."""
        error_msg = str(e).lower()
        if "unique" in error_msg:
            messagebox.showerror(
                self.controller.t("error"),
                self.controller.t("deck_name_already_exists")
            )
        else:
            messagebox.showerror(
                self.controller.t("error"),
                self.controller.t("deck_import_failed").format(error=str(error_msg))
            )