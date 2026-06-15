import tkinter as tk
from tkinter import ttk

from database.queries import get_decks_by_duelist
from ui.duelist_deck_viewer_window import DuelistDeckViewerWindow
from utils.search_bar import SearchBar


class DuelistDetailsFrame(tk.Frame):
    def __init__(self, parent, controller):
        """Frame that shows a visual deck selection for the selected duelist."""
        super().__init__(parent)

        self.controller = controller
        self.image_handler = controller.image_handler

        self.current_duelist_id = None
        self.current_duelist_key = None
        self.decks_data = []

        self.duelist_decks_label = tk.Label(self, font=("Arial", 16))
        self.duelist_decks_label.pack(pady=10)

        self.all_decks_data = []
        self.filtered_decks_data = []

        self.search_var = tk.StringVar()
        self.last_search_text = ""

        self.search_container = tk.Frame(self)
        self.search_container.pack(anchor="w", padx=20, pady=(0, 5))

        self.search_bar = SearchBar(
            self.search_container,
            textvariable=self.search_var,
            placeholder=self.controller.t("search_decks"),
            on_change=self.filter_decks,
            width=30
        )
        self.search_bar.pack(side="left")

        self.decks_canvas = tk.Canvas(self)
        self.decks_scroll = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.decks_canvas.yview
        )

        self.decks_grid = tk.Frame(self.decks_canvas)

        def update_decks_scrollregion(event=None):
            if not self.decks_canvas.winfo_exists():
                return

            self.decks_canvas.configure(
                scrollregion=self.decks_canvas.bbox("all")
            )

            self.update_decks_scroll_visibility()

        self.decks_grid.bind("<Configure>", update_decks_scrollregion)

        self.decks_canvas_window = self.decks_canvas.create_window(
            (0, 0),
            window=self.decks_grid,
            anchor="n"
        )

        self.decks_canvas.bind("<Configure>", self.on_decks_canvas_configure)

        self.decks_canvas.configure(
            yscrollcommand=self.decks_scroll.set
        )

        self.decks_canvas.pack(
            side="left",
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        self.decks_scroll.pack(side="right", fill="y")

        self.decks_canvas.bind("<Enter>", self._bind_decks_mousewheel)
        self.decks_canvas.bind("<Leave>", self._unbind_decks_mousewheel)

        self.refresh_ui()

    def filter_decks(self, event=None):
        search_text = self.search_bar.get_text().casefold()

        if not search_text:
            self.filtered_decks_data = self.all_decks_data.copy()
        else:
            self.filtered_decks_data = [
                deck for deck in self.all_decks_data
                if search_text in deck["deck_name"].casefold()
            ]

        self.decks_data = self.filtered_decks_data
        self.load_deck_selection_gallery()

    def on_decks_canvas_configure(self, event):
        self.decks_canvas.itemconfig(
            self.decks_canvas_window,
            width=event.width
        )

        if self.decks_data:
            self.load_deck_selection_gallery()

    def set_duelist(self, duelist_id, duelist_key):
        self.current_duelist_id = duelist_id
        self.current_duelist_key = duelist_key

        self.refresh_ui()
        self.load_duelist()

    def load_duelist(self):
        if not self.current_duelist_id:
            return

        for widget in self.decks_grid.winfo_children():
            widget.destroy()

        self.all_decks_data = get_decks_by_duelist(
            self.current_duelist_id,
            self.controller.current_language,
            show_exclusive_cards=True
        )

        self.filtered_decks_data = self.all_decks_data.copy()
        self.decks_data = self.filtered_decks_data

        if not self.decks_data:
            tk.Label(
                self.decks_grid,
                text=self.controller.t("no_decks_found"),
                font=("Tahoma", 12)
            ).grid(row=0, column=0, padx=10, pady=10)

            self.decks_canvas.update_idletasks()
            self.decks_canvas.configure(scrollregion=self.decks_canvas.bbox("all"))
            self.update_decks_scroll_visibility()
            return

        self.load_deck_selection_gallery()

    def load_deck_selection_gallery(self):
        for widget in self.decks_grid.winfo_children():
            widget.destroy()

        deck_width = 250
        horizontal_gap = 30
        available_width = max(self.decks_canvas.winfo_width(), 1)

        columns = max(
            1,
            available_width // (deck_width + horizontal_gap)
        )

        row = 0
        col = 0

        cover_width = 132
        cover_height = 189

        for index, deck in enumerate (self.decks_data, start=1):

            deck_frame = tk.Frame(
                self.decks_grid,
                width=250,
                height=360,
                bg="#f2f2f2",
                highlightbackground="#9a9a9a",
                highlightthickness=1,
                padx=10,
                pady=10,
                cursor="hand2"
            )
            deck_frame.grid(row=row, column=col, padx=18, pady=18, sticky="n")
            deck_frame.pack_propagate(False)

            header_label = tk.Label(
                deck_frame,
                text= f"{self.controller.t('deck')} #{index}",
                bg="#d9d9d9",
                fg="#333333",
                font=("Tahoma", 10),
                anchor="center"
            )
            header_label.pack(fill="x", pady=(0, 8))

            cover_frame = tk.Frame(
                deck_frame,
                width=cover_width,
                height=cover_height,
                bg="#1f1f1f",
                highlightbackground="#000000",
                highlightthickness=2,
                cursor="hand2"
            )
            cover_frame.pack()
            cover_frame.pack_propagate(False)

            cover_label = tk.Label(
                cover_frame,
                text=self.controller.t("loading"),
                bg="#1f1f1f",
                fg="white",
                cursor="hand2"
            )
            cover_label.pack(fill="both", expand=True, padx=3, pady=3)

            name_container = tk.Frame(
                deck_frame,
                height=120,
                bg="#f2f2f2"
            )
            name_container.pack(fill="x", pady=(8, 0))
            name_container.pack_propagate(False)

            total_cards = sum(
                qty for _, _, qty, _ in deck["cards"]
            )

            title_area = tk.Frame(
                name_container,
                height=75,
                bg="#f2f2f2"
            )
            title_area.pack(fill="x")
            title_area.pack_propagate(False)

            name_label = tk.Label(
                title_area,
                text=deck["deck_name"],
                wraplength=220,
                justify="center",
                font=("Tahoma", 12),
                bg="#f2f2f2",
                cursor="hand2"
            )
            name_label.pack(expand=True)

            separator = tk.Frame(
                name_container,
                height=1,
                bg="#c8c8c8"
            )
            separator.pack(fill="x", padx=25, pady=(2, 4))

            cards_count_label = tk.Label(
                name_container,
                text=f"{total_cards} {self.controller.t('cards')}",
                font=("Tahoma", 11, "bold"),
                bg="#f2f2f2",
                cursor="hand2"
            )
            cards_count_label.pack()

            def on_enter(event, frame=deck_frame, header=header_label):
                frame.config(bg="#e8e8e8", highlightbackground="#555555")
                header.config(bg="#cfcfcf")

            def on_leave(event, frame=deck_frame, header=header_label):
                frame.config(bg="#f2f2f2", highlightbackground="#9a9a9a")
                header.config(bg="#d9d9d9")

            for widget in (deck_frame, header_label, cover_frame, cover_label, name_container, name_label):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

            clickable_widgets = (
                deck_frame,
                header_label,
                cover_frame,
                cover_label,
                name_container,
                title_area,
                name_label,
                separator,
                cards_count_label
            )

            for widget in clickable_widgets:
                widget.bind(
                    "<Button-1>",
                    lambda e, d=deck: self.open_deck_viewer(d)
                )
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

            cover_card_id = self.get_deck_cover_card_id(deck)

            self.image_handler.load_thumbnail_async(
                self,
                cover_card_id,
                cover_width,
                cover_height,
                lambda cid, tk_img, label=cover_label:
                self._on_deck_cover_loaded(
                    cid,
                    tk_img,
                    label
                )
            )

            col += 1

            if col >= columns:
                col = 0
                row += 1

        for i in range(columns):
            self.decks_grid.grid_columnconfigure(i, weight=1)

        self.decks_canvas.update_idletasks()
        self.decks_canvas.configure(
            scrollregion=self.decks_canvas.bbox("all")
        )

        self.update_decks_scroll_visibility()

    def get_deck_cover_card_id(self, deck):
        if deck.get("cover_card_id") is not None:
            return deck["cover_card_id"]

        for card_id, card_name, qty, card_type in deck["cards"]:
            if card_id is not None:
                return card_id

        return None

    def _on_deck_cover_loaded(self, card_id, tk_img, label):
        if not label.winfo_exists():
            return

        if tk_img is None:
            tk_img = self.image_handler.get_placeholder(132, 189)

        label.image = tk_img
        label.config(image=tk_img, text="")

    def open_deck_viewer(self, deck):
        DuelistDeckViewerWindow(
            self,
            self.controller,
            self.current_duelist_id,
            self.current_duelist_key,
            deck
        )

    def update_decks_scroll_visibility(self):
        self.decks_canvas.update_idletasks()

        bbox = self.decks_canvas.bbox("all")

        if not bbox:
            self.decks_scroll.pack_forget()
            return

        content_height = bbox[3] - bbox[1]
        canvas_height = self.decks_canvas.winfo_height()

        if content_height <= canvas_height:
            self.decks_scroll.pack_forget()
            self.decks_canvas.yview_moveto(0)
        else:
            self.decks_scroll.pack(side="right", fill="y")

    def _bind_decks_mousewheel(self, event):
        self.decks_canvas.bind_all("<MouseWheel>", self._on_decks_mousewheel)

    def _unbind_decks_mousewheel(self, event):
        self.decks_canvas.unbind_all("<MouseWheel>")

    def _on_decks_mousewheel(self, event):
        bbox = self.decks_canvas.bbox("all")

        if not bbox:
            return "break"

        content_height = bbox[3] - bbox[1]
        canvas_height = self.decks_canvas.winfo_height()

        if content_height <= canvas_height:
            self.decks_canvas.yview_moveto(0)
            return "break"

        self.decks_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

        return "break"

    def refresh_ui(self):
        self.duelist_decks_label.config(
            text=self.controller.t("duelist_decks").format(
                name=self.controller.t(self.current_duelist_key)
            )
        )

        self.search_bar.placeholder = self.controller.t("search_decks")

        if self.search_bar.placeholder_active:
            self.search_bar.set_placeholder()