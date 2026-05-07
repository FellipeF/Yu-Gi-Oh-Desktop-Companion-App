import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json
import zipfile
import re

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

        self.search_entry = tk.Entry(search_container,textvariable=self.search_var, font=("Tahoma",12), width=40)
        self.search_entry.pack(side="left")

        self.search_placeholder_text = self.controller.t("search_decks")
        self.search_entry.insert(0, self.search_placeholder_text)
        self.search_entry.config(fg="gray")

        self.search_entry.bind("<FocusIn>", self.clear_search_placeholder)
        self.search_entry.bind("<FocusOut>", self.restore_search_placeholder)
        self.search_entry.bind("<KeyRelease>", self.filter_decks)

        table_container = tk.Frame(self)
        table_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("name", "total_cards", "used", "edit", "rename")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=15,
            style="Custom.Treeview",
            selectmode="extended",
        )

        self.tooltip = TreeviewTooltip(self.tree, {
            "#4": self.controller.t("edit"),
            "#5": self.controller.t("rename_deck"),
        })

        self.tree.heading("name", text=self.controller.t("deck_name"))
        self.tree.heading("total_cards", text=self.controller.t("total_cards"))
        self.tree.heading("used", text=self.controller.t("used"))
        self.tree.heading("edit", text="")
        self.tree.heading("rename", text="")

        self.tree.column("name", width=360, anchor="w")
        self.tree.column("total_cards", width=130, anchor="center")
        self.tree.column("used", width=80, anchor="center")
        self.tree.column("edit", width=28, stretch=False, anchor="center")
        self.tree.column("rename", width=28, stretch=False, anchor="center")

        self.tree.tag_configure("even", background="#eaeaea")
        self.tree.tag_configure("odd", background="#ffffff")

        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_deck_select)
        self.tree.bind("<Double-1>", self.open_selected_deck)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Motion>", self.on_motion_cursor, add="+") # So that cursor + tooltip both work together
        self.tree.bind("<Shift-Button-1>", self.on_shift_click) # Using custom anchor so Shift + Click works properly
        self.tree.bind("<Control-Button-1>", self.on_ctrl_click)
        self.tree.bind("<Delete>", self.on_delete_key)
        self.tree.bind("<F2>", self.on_f2_key)

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

        self.delete_button = tk.Button(
            right_frame,
            text="🗑️",
            font=("Segoe UI Emoji", 12),
            command=self.delete_selected_deck
        )
        self.delete_button.pack(side="left", padx=3)

        self.add_tooltip(self.new_button, self.controller.t("new_deck"))
        self.add_tooltip(self.import_button, self.controller.t("import_deck"))
        self.add_tooltip(self.export_button, self.controller.t("export_deck"))
        self.add_tooltip(self.delete_button, self.controller.t("delete_deck"))

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

        if column in ("#4", "#5"):
            self.tree.config(cursor="hand2")
        else:
            self.tree.config(cursor="")

    def on_shift_click(self, event):
        item_id = self.tree.identify_row(event.y)

        if not item_id:
            return "break"

        children = list(self.tree.get_children())

        if not self.selected_deck_id:
            self.tree.selection_set(item_id)
            self.selected_deck_id = int(item_id)
            return "break"

        start_item = str(self.selected_deck_id)

        if start_item not in children or item_id not in children:
            return "break"

        start_index = children.index(start_item)
        end_index = children.index(item_id)

        if start_index > end_index:
            start_index, end_index = end_index, start_index

        items_to_select = children[start_index:end_index + 1]

        self.tree.selection_set(items_to_select)
        self.tree.focus(item_id)

        return "break"

    def on_ctrl_click(self, event):
        item_id = self.tree.identify_row(event.y)

        if not item_id:
            return "break"

        current_selection = set(self.tree.selection())

        if item_id in current_selection: # Clicked again?
            current_selection.remove(item_id)
        else:
            current_selection.add(item_id)

        self.tree.selection_set(list(current_selection))
        self.tree.focus(item_id)
        self.selected_deck_id = int(item_id)

        return "break"

    def on_delete_key(self, event=None):
        if not self.tree.selection():
            return "break"

        self.delete_selected_deck()
        return "break"

    def on_f2_key(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return "break"

        self.selected_deck_id = int(selection[0])
        self.rename_selected_deck()
        return "break"

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
        }

        self.add_tooltip(self.new_button, self.controller.t("new_deck"))
        self.add_tooltip(self.import_button, self.controller.t("import_deck"))
        self.add_tooltip(self.export_button, self.controller.t("export_deck"))
        self.add_tooltip(self.delete_button, self.controller.t("delete_deck"))

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
        self.tree.focus_set()

        if event.state & 0x0001: # When Shift is being pressed, ignore this to do the on_shift_click method instead
            return

        if event.state & 0x0004: # CTRL key
            return

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
        selection = self.tree.selection()

        if not selection:
            return

        count = len(selection)

        confirm_message = (
            self.controller.t("confirm_delete_deck")
            if count == 1
            else self.controller.t("confirm_delete_decks").format(count=count)
        )

        confirm = messagebox.askyesno(
            self.controller.t("deck_remover"),
            confirm_message
        )

        if not confirm:
            return

        try:
            for item_id in selection:
                delete_user_deck(int(item_id))

            self.load_user_decks()
            self.selected_deck_id = None
            self.update_scroll_visibility()

        except Exception as e:
            self.treat_exception(e)

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

    def build_deck_import_data(self, data, suggested_name = None):
        if not isinstance(data, dict):
            raise ValueError(self.controller.t("invalid_deck_file"))

        required_fields = ["duelist", "deck_name", "cards"]

        if not all(field in data for field in required_fields):
            raise ValueError(self.controller.t("invalid_deck_file"))

        cards = data.get("cards")
        deck_name_from_file = data.get("deck_name")
        duelist_name = data.get("duelist")

        # If cards list is empty, return
        if not isinstance(cards, list) or not cards:
            raise ValueError(self.controller.t("invalid_deck_file"))

        # Card Validation
        for card in cards:
            if not isinstance(card, dict):
                raise ValueError(self.controller.t("invalid_card_entry"))

            if "name" not in card or "quantity" not in card:
                raise ValueError(self.controller.t("invalid_card_entry"))

            card_name = card.get("name")
            quantity = card.get("quantity")

            if not isinstance(card_name, str) or not card_name.strip():
                raise ValueError(self.controller.t("invalid_card_entry"))

            if not isinstance(quantity, int) or quantity <= 0:
                raise ValueError(self.controller.t("invalid_card_entry"))

        if not suggested_name:
            suggested_name = deck_name_from_file

            if duelist_name and deck_name_from_file:
                suggested_name = f"{duelist_name} - {deck_name_from_file}"

        if not suggested_name or not suggested_name.strip():
            raise ValueError(self.controller.t("invalid_deck_file"))

        suggested_name = suggested_name.strip()
        new_deck_id = create_user_deck(suggested_name)
        add_cards_bulk_import(new_deck_id, cards)

        return new_deck_id

    def import_deck(self):
        """Import JSON File and check if it's in the right formatting"""
        file_path = filedialog.askopenfilename(
            title=self.controller.t("import_deck"),
            filetypes=[
                ("Deck files", "*.json *.zip"),
                ("JSON files", "*.json"),
                ("ZIP files", "*.zip"),
            ]
        )

        # Cancel was pressed
        if not file_path:
            return

        new_deck_id = None
        created_decks_ids = [] # For transaction control

        try:
            if file_path.lower().endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                suggested_name = data.get("deck_name", self.controller.t("imported_deck"))

                new_deck_name = simpledialog.askstring(
                    self.controller.t("deck_importer"),
                    self.controller.t("enter_imported_deck_name"),
                    initialvalue=suggested_name,
                    parent=self
                )

                if not new_deck_name:
                    return

                new_deck_id = self.build_deck_import_data(data, new_deck_name.strip())
                created_decks_ids.append(new_deck_id)

            elif file_path.lower().endswith(".zip"):
                imported_count = 0
                last_deck_id = None

                with zipfile.ZipFile(file_path, "r") as zip_file:
                    for filename in zip_file.namelist():
                        if not filename.lower().endswith(".json"):
                            continue

                        with zip_file.open(filename) as f:
                            data = json.loads(f.read().decode("utf-8"))

                        last_deck_id = self.build_deck_import_data(data)
                        created_decks_ids.append(last_deck_id)
                        imported_count +=1

                if imported_count == 0:
                    messagebox.showerror(
                        self.controller.t("error"),
                        self.controller.t("invalid_deck_file")
                    )
                    return

                new_deck_id = last_deck_id

            self.load_user_decks()

            if new_deck_id:
                self.tree.selection_set(str(new_deck_id))
                self.tree.focus(str(new_deck_id))
                self.tree.see(str(new_deck_id))
                self.selected_deck_id = new_deck_id

            if len(created_decks_ids) == 1:
                messagebox.showinfo(
                    self.controller.t("deck_importer"),
                    self.controller.t("deck_import_success")
                )
            else:
                messagebox.showinfo(
                    self.controller.t("deck_importer"),
                    f"{len(created_decks_ids)} {self.controller.t('decks_import_success')}"
                )

        except Exception as e:
            for deck_id in reversed(created_decks_ids): # Rollback
                try:
                    delete_user_deck(deck_id)
                except Exception:
                    pass

            self.load_user_decks()
            self.treat_exception(e)

    def safe_filename(self, name):
        """Replaces invalid characters for the OS file structure"""
        name = re.sub(r'[\\/*?:"<>|]', "_", name)
        return name.strip().lower().replace(" ", "_")

    def build_deck_export_data(self, deck_id):
        deck = get_user_deck_by_id(deck_id)

        if not deck:
            return None

        _deck_id, deck_name, is_used = deck

        cards = get_cards_by_user_deck(deck_id, self.controller.current_language)

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

        return deck_name, export_data

    def export_deck(self):
        """Export selected deck to a JSON file."""
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning(
                self.controller.t("deck_exporter"),
                self.controller.t("no_decks_to_export")
            )
            return

        if len(selected_items) == 1:
            deck_id = int(selected_items[0])
            result = self.build_deck_export_data(deck_id)

            if not result:
                messagebox.showerror(
                    self.controller.t("error"),
                    self.controller.t("deck_not_found")
                )
                return

            deck_name, export_data = result
            default_filename = f"{self.safe_filename(deck_name)}.json"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                initialfile=default_filename,
                title=self.controller.t("deck_exporter")
            )

            if not file_path:
                return

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=4)

                messagebox.showinfo(
                    self.controller.t("deck_exporter"),
                    self.controller.t("deck_export_success").format(path=file_path)
                )

            except Exception as e:
                messagebox.showerror(
                    self.controller.t("deck_exporter"),
                    self.controller.t("deck_export_fail").format(error=str(e))
                )

            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile="custom_decks_export.zip",
            title=self.controller.t("export_deck")
        )

        if not file_path:
            return

        try:
            exported_count = 0

            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for item_id in selected_items:
                    deck_id = int(item_id)
                    result = self.build_deck_export_data(deck_id)

                    if not result:
                        continue

                    deck_name, export_data = result
                    filename = f"{self.safe_filename(deck_name)}.json"

                    zip_file.writestr(filename, json.dumps(export_data, ensure_ascii=False, indent=4))

                    exported_count +=1

            messagebox.showinfo(
                self.controller.t("deck_exporter"),
                f"{exported_count} {self.controller.t('decks_export_success')}\n{file_path}"
            )

        except Exception as e:
            messagebox.showerror(
                self.controller.t("deck_exporter"),
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