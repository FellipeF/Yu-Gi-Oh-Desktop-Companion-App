import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

from ui.card_details_window import CardDetailsWindow
from config import CARD_HEIGHT, CARD_WIDTH, EXTRA_TYPES


class DuelistDeckViewerFrame(tk.Frame):
    def __init__(self, parent, controller, duelist_id, duelist_key, deck_data):
        super().__init__(parent)

        self.controller = controller
        self.image_handler = controller.image_handler

        self.current_duelist_id = duelist_id
        self.current_duelist_key = duelist_key
        self.deck_data = deck_data

        self.tk_image = None
        self.selected_card_id = None
        self.current_cards = []
        self.displayed_cards = []

        self.title_label = tk.Label(self, font=("Arial", 16))
        self.title_label.pack(pady=10)

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=10)

        left_frame = tk.Frame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

        top_buttons_frame = tk.Frame(left_frame)
        top_buttons_frame.pack(fill="x", pady=(0, 8))

        self.export_deck_button = tk.Button(
            top_buttons_frame,
            width=16,
            command=self.export_selected_deck
        )
        self.export_deck_button.pack(anchor="e")

        self.cards_notebook = ttk.Notebook(left_frame)
        self.cards_notebook.pack(fill="both", expand=True)

        self.text_view_frame = tk.Frame(self.cards_notebook)
        self.gallery_view_frame = tk.Frame(self.cards_notebook)

        self.cards_notebook.add(self.text_view_frame, text=self.controller.t("text_view"))
        self.cards_notebook.add(self.gallery_view_frame, text=self.controller.t("gallery_view"))

        cards_container = tk.Frame(self.text_view_frame)
        cards_container.pack(fill="both", expand=True)

        self.cards_listbox = tk.Listbox(
            cards_container,
            exportselection=False,
            height=18,
            font=("Tahoma", 12)
        )
        self.cards_listbox.pack(side="left", fill="both", expand=True)

        self.cards_scroll = ttk.Scrollbar(
            cards_container,
            orient="vertical",
            command=self.cards_listbox.yview
        )
        self.cards_scroll.pack(side="right", fill="y")

        self.cards_listbox.config(yscrollcommand=self.cards_scroll.set)

        self.cards_listbox.bind("<<ListboxSelect>>", self.show_card_image)
        self.cards_listbox.bind("<Up>", self.on_cards_arrow_key)
        self.cards_listbox.bind("<Down>", self.on_cards_arrow_key)
        self.cards_listbox.bind("<ButtonRelease-1>", self.on_cards_mouse_release)

        self.gallery_canvas = tk.Canvas(self.gallery_view_frame)
        self.gallery_scroll = ttk.Scrollbar(
            self.gallery_view_frame,
            orient="vertical",
            command=self.gallery_canvas.yview
        )

        self.gallery_inner = tk.Frame(self.gallery_canvas)

        def update_gallery_scrollregion(event=None):
            if not self.gallery_canvas.winfo_exists():
                return

            self.gallery_canvas.configure(
                scrollregion=self.gallery_canvas.bbox("all")
            )

            self.update_gallery_scroll_visibility()

        self.gallery_inner.bind("<Configure>", update_gallery_scrollregion)

        self.gallery_canvas.create_window((0, 0), window=self.gallery_inner, anchor="nw")
        self.gallery_canvas.configure(yscrollcommand=self.gallery_scroll.set)

        self.gallery_canvas.pack(side="left", fill="both", expand=True)
        self.gallery_scroll.pack(side="right", fill="y")

        self.gallery_canvas.bind("<Enter>", self._bind_gallery_mousewheel)
        self.gallery_canvas.bind("<Leave>", self._unbind_gallery_mousewheel)

        # ===== RIGHT PANEL =====
        right_frame = tk.Frame(main_container, width=CARD_WIDTH + 90)
        right_frame.pack(side="right", fill="y", pady=25)
        right_frame.pack_propagate(False)

        self.deck_status_label = tk.Label(
            right_frame,
            font=("Arial", 12, "bold"),
            wraplength=CARD_WIDTH + 90,
            justify="center"
        )
        self.deck_status_label.pack(pady=(0, 9))

        self.image_container = tk.Frame(right_frame, width=CARD_WIDTH, height=CARD_HEIGHT)
        self.image_container.pack(pady=(0, 8))
        self.image_container.pack_propagate(False)

        self.image_label = tk.Label(
            self.image_container,
            text=self.controller.t("select_card"),
            anchor="center"
        )
        self.image_label.pack(fill="both", expand=True)

        self.show_card_details = tk.Button(
            right_frame,
            command=self.open_card_details_window
        )
        self.show_card_details.pack()
        self.show_card_details.pack_forget()

        self.show_exclusive_cards = tk.BooleanVar(value=True)

        self.exclusive_cards_checkbox = tk.Checkbutton(
            self,
            font=("Tahoma", 12),
            variable=self.show_exclusive_cards,
            command=self.reload_deck_cards
        )
        self.exclusive_cards_checkbox.pack(side="bottom", pady=5)

        self.refresh_ui()
        self.load_deck_cards()

    def reload_deck_cards(self):
        from database.queries import get_decks_by_duelist

        decks_data = get_decks_by_duelist(
            self.current_duelist_id,
            self.controller.current_language,
            show_exclusive_cards=self.show_exclusive_cards.get()
        )

        selected_deck = next(
            (
                deck for deck in decks_data
                if deck["deck_id"] == self.deck_data["deck_id"]
            ),
            None
        )

        if selected_deck is None:
            return

        previous_card_id = self.selected_card_id

        self.deck_data = selected_deck
        self.load_deck_cards()
        self.restore_selected_card(previous_card_id)

    def restore_selected_card(self, previous_card_id):
        if not previous_card_id:
            self.clear_card_selection()
            return

        for index, card in enumerate(self.displayed_cards):
            if card is None:
                continue

            card_id, card_name, qty, card_type = card

            if card_id == previous_card_id:
                self.selected_card_id = card_id
                self.cards_listbox.selection_clear(0, tk.END)
                self.cards_listbox.select_set(index)
                self.cards_listbox.activate(index)
                self.cards_listbox.see(index)
                self.show_card_image(None)
                return

        self.clear_card_selection()

    def refresh_ui(self):
        self.title_label.config(
            text=f"{self.controller.t(self.current_duelist_key)} - {self.deck_data['deck_name']}"
        )

        self.export_deck_button.config(text=self.controller.t("export_individual_deck"))
        self.show_card_details.config(text=self.controller.t("card_details"))

        self.cards_notebook.tab(0, text=self.controller.t("text_view"))
        self.cards_notebook.tab(1, text=self.controller.t("gallery_view"))

        if self.tk_image is None and self.image_label.cget("image") == "":
            self.image_label.config(text=self.controller.t("select_card"))

        self.exclusive_cards_checkbox.config(
            text=self.controller.t("show_exclusive_cards")
        )

    def load_deck_cards(self):
        self.cards_listbox.delete(0, tk.END)

        for widget in self.gallery_inner.winfo_children():
            widget.destroy()

        self.current_cards = self.deck_data["cards"]
        self.displayed_cards = []

        current_section = None
        current_group = None

        for card_id, card_name, qty, card_type in self.current_cards:
            is_extra = self.is_extra_deck(card_type)
            deck_section = "extra" if is_extra else "main"

            if deck_section != current_section:
                section_label = (
                    self.controller.t("main_deck")
                    if deck_section == "main"
                    else self.controller.t("extra_deck")
                )

                self.cards_listbox.insert(tk.END, f"=== {section_label.upper()} ===")
                self.displayed_cards.append(None)

                current_section = deck_section
                current_group = None

            group_label = self._card_group_label(card_id, card_type, deck_section)

            if group_label and group_label != current_group:
                self.cards_listbox.insert(tk.END, f"━━━ {group_label.upper()} ━━━")

                index = self.cards_listbox.size() - 1
                color = self._get_group_color(group_label)
                self.cards_listbox.itemconfig(index, fg=color)

                self.displayed_cards.append(None)
                current_group = group_label

            self.cards_listbox.insert(tk.END, f"{qty}x {card_name}")
            self.displayed_cards.append((card_id, card_name, qty, card_type))

        self.update_scroll_visibility(self.cards_listbox, self.cards_scroll)
        self.update_deck_status()
        self.load_gallery_view()

    def load_gallery_view(self):
        for widget in self.gallery_inner.winfo_children():
            widget.destroy()

        columns = 4
        row = 0
        col = 0

        thumbnail_width = 120
        thumbnail_height = 171

        for card in self.displayed_cards:
            if card is None:
                continue

            card_id, card_name, qty, card_type = card

            card_frame = tk.Frame(self.gallery_inner, padx=6, pady=6)
            card_frame.grid(row=row, column=col, sticky="n")

            thumb_frame = tk.Frame(
                card_frame,
                width=thumbnail_width,
                height=thumbnail_height,
                relief="ridge",
                borderwidth=1,
                cursor="hand2"
            )
            thumb_frame.pack()
            thumb_frame.pack_propagate(False)

            img_label = tk.Label(
                thumb_frame,
                text=self.controller.t("loading"),
                cursor="hand2"
            )
            img_label.pack(fill="both", expand=True)

            name_label = tk.Label(
                card_frame,
                text=f"{qty}x {card_name}",
                wraplength=125,
                justify="center",
                font=("Tahoma", 10),
                cursor="hand2"
            )
            name_label.pack(pady=(3, 0))

            thumb_frame.bind("<Button-1>", lambda e, cid=card_id: self.select_card_by_id(cid))
            img_label.bind("<Button-1>", lambda e, cid=card_id: self.select_card_by_id(cid))
            name_label.bind("<Button-1>", lambda e, cid=card_id: self.select_card_by_id(cid))

            self.image_handler.load_thumbnail_async(
                self,
                card_id,
                thumbnail_width,
                thumbnail_height,
                lambda cid, tk_img, label=img_label: self._on_gallery_image_loaded(cid, tk_img, label)
            )

            col += 1

            if col >= columns:
                col = 0
                row += 1

        self.gallery_canvas.update_idletasks()
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))
        self.update_gallery_scroll_visibility()

    def _on_gallery_image_loaded(self, card_id, tk_img, label):
        if not label.winfo_exists():
            return

        if tk_img is None:
            tk_img = self.image_handler.get_placeholder(120, 171)

        label.image = tk_img
        label.config(image=tk_img, text="")

    def select_card_by_id(self, card_id):
        self.selected_card_id = card_id

        if card_id is None:
            self.show_card_details.pack_forget()
        else:
            self.show_card_details.pack()

        self.image_handler.load_async(
            self,
            card_id,
            self._on_image_loaded
        )

    def show_card_image(self, event):
        selection = self.cards_listbox.curselection()

        if not selection:
            return

        card = self.displayed_cards[selection[0]]

        if card is None:
            return

        card_id, *_ = card
        self.select_card_by_id(card_id)

    def _on_image_loaded(self, card_id, tk_img):
        if card_id != self.selected_card_id:
            return

        if tk_img is None:
            tk_img = self.image_handler.get_placeholder(CARD_WIDTH, CARD_HEIGHT)

        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")

    def open_card_details_window(self):
        if not self.selected_card_id:
            return

        CardDetailsWindow(self.controller, self.selected_card_id)

    def export_selected_deck(self):
        deck_key = self.deck_data["deck_key"]
        deck_name = self.deck_data["deck_name"]

        export_data = {
            "duelist": self.controller.t(self.current_duelist_key),
            "deck_name": deck_name,
            "cards": []
        }

        for card_id, card_name, qty, _ in self.deck_data["cards"]:
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
            title=self.controller.t("export_individual_deck")
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

    def update_deck_status(self):
        total_cards_main_deck = sum(
            qty for _, _, qty, card_type in self.current_cards
            if not self.is_extra_deck(card_type)
        )

        if total_cards_main_deck >= 40:
            self.deck_status_label.config(
                text=self.controller.t("complete_deck"),
                fg="green"
            )
        else:
            self.deck_status_label.config(
                text=self.controller.t("incomplete_deck"),
                fg="red"
            )

    def update_gallery_scroll_visibility(self):
        self.gallery_canvas.update_idletasks()

        bbox = self.gallery_canvas.bbox("all")

        if not bbox:
            self.gallery_scroll.pack_forget()
            return

        content_height = bbox[3] - bbox[1]
        canvas_height = self.gallery_canvas.winfo_height()

        if content_height <= canvas_height:
            self.gallery_scroll.pack_forget()
            self.gallery_canvas.yview_moveto(0)
        else:
            self.gallery_scroll.pack(side="right", fill="y")

    def _bind_gallery_mousewheel(self, event):
        self.gallery_canvas.bind_all("<MouseWheel>", self._on_gallery_mousewheel)

    def _unbind_gallery_mousewheel(self, event):
        self.gallery_canvas.unbind_all("<MouseWheel>")

    def _on_gallery_mousewheel(self, event):
        bbox = self.gallery_canvas.bbox("all")

        if not bbox:
            return "break"

        content_height = bbox[3] - bbox[1]
        canvas_height = self.gallery_canvas.winfo_height()

        if content_height <= canvas_height:
            self.gallery_canvas.yview_moveto(0)
            return "break"

        self.gallery_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def update_scroll_visibility(self, listbox, scrollbar):
        listbox.update_idletasks()
        first, last = listbox.yview()

        if first <= 0.0 and last >= 1.0:
            scrollbar.pack_forget()
        else:
            scrollbar.pack(side="right", fill="y")

    def clear_card_selection(self):
        self.selected_card_id = None
        self.tk_image = None
        self.cards_listbox.selection_clear(0, tk.END)
        self.image_label.image = None
        self.image_label.config(image="", text=self.controller.t("select_card"))
        self.show_card_details.pack_forget()

    def is_valid_card_index(self, index):
        return 0 <= index < len(self.displayed_cards) and self.displayed_cards[index] is not None

    def select_card_index(self, index):
        self.cards_listbox.selection_clear(0, tk.END)
        self.cards_listbox.select_set(index)
        self.cards_listbox.activate(index)
        self.cards_listbox.see(index)
        self.show_card_image(None)

    def find_next_valid_card_index(self, start_index, direction):
        index = start_index

        while 0 <= index < len(self.displayed_cards):
            if self.is_valid_card_index(index):
                return index

            index += direction

        return None

    def on_cards_arrow_key(self, event):
        selection = self.cards_listbox.curselection()

        if selection:
            current_index = selection[0]
        else:
            current_index = self.cards_listbox.index(tk.ACTIVE)

        direction = -1 if event.keysym == "Up" else 1

        next_index = self.find_next_valid_card_index(
            current_index + direction,
            direction
        )

        if next_index is not None:
            self.select_card_index(next_index)

        return "break"

    def on_cards_mouse_release(self, event):
        selection = self.cards_listbox.curselection()

        if not selection:
            return "break"

        index = selection[0]

        if self.is_valid_card_index(index):
            return

        next_index = self.find_next_valid_card_index(index + 1, 1)

        if next_index is None:
            next_index = self.find_next_valid_card_index(index - 1, -1)

        if next_index is not None:
            self.select_card_index(next_index)
        else:
            self.cards_listbox.selection_clear(0, tk.END)

        return "break"

    def is_extra_deck(self, card_type: str | None) -> bool:
        if not card_type:
            return False

        return any(x in card_type for x in EXTRA_TYPES)

    def _card_group_label(self, card_id: int | None, card_type: str | None, deck_section: str) -> str | None:
        if card_id is None:
            return self.controller.t("exclusive_cards")

        if not card_type:
            return self.controller.t("other_cards")

        if "Token" in card_type:
            return self.controller.t("other_cards")

        if deck_section == "extra":
            if "Fusion" in card_type and "Pendulum" in card_type:
                return self.controller.t("fusion_pendulum_monsters")
            if "Fusion" in card_type:
                return self.controller.t("fusion_monsters")
            if "Synchro" in card_type and "Pendulum" in card_type:
                return self.controller.t("synchro_pendulum_monsters")
            if "Synchro" in card_type:
                return self.controller.t("synchro_monsters")
            if "XYZ" in card_type and "Pendulum" in card_type:
                return self.controller.t("xyz_pendulum_monsters")
            if "XYZ" in card_type:
                return self.controller.t("xyz_monsters")
            if "Link" in card_type:
                return self.controller.t("link_monsters")

            return self.controller.t("extra_deck")

        if "Ritual" in card_type:
            return self.controller.t("ritual_monsters")
        if "Pendulum" in card_type:
            return self.controller.t("pendulum_monsters")
        if card_type == "Normal Monster":
            return self.controller.t("normal_monsters")
        if "Monster" in card_type:
            return self.controller.t("effect_monsters")
        if card_type == "Spell Card":
            return self.controller.t("spells")
        if card_type == "Trap Card":
            return self.controller.t("traps")

        return self.controller.t("other_cards")

    def _get_group_color(self, group_label: str) -> str:
        colors = {
            self.controller.t("normal_monsters"): "#C8B070",
            self.controller.t("effect_monsters"): "#B86B2B",
            self.controller.t("ritual_monsters"): "#4A8DC7",
            self.controller.t("pendulum_monsters"): "#2F8C72",

            self.controller.t("fusion_monsters"): "#7B5BA7",
            self.controller.t("fusion_pendulum_monsters"): "#6A4C93",

            self.controller.t("synchro_monsters"): "#9A9A9A",
            self.controller.t("synchro_pendulum_monsters"): "#6F8F8F",

            self.controller.t("xyz_monsters"): "#303030",
            self.controller.t("xyz_pendulum_monsters"): "#1E4F4F",

            self.controller.t("link_monsters"): "#2563EB",

            self.controller.t("spells"): "#1D8F6A",
            self.controller.t("traps"): "#8E44AD",
        }

        return colors.get(group_label, "black")