import tkinter as tk
from tkinter import ttk

class CardGallery(tk.Frame):
    COLUMNS = 4
    PAGE_SIZE = 12
    THUMB_WIDTH = 125
    THUMB_HEIGHT = 182
    CELL_WIDTH = 175
    CELL_HEIGHT = 250

    def __init__(self, parent, image_handler, on_select=None, on_double_click=None):
        super().__init__(parent)

        self.image_handler = image_handler
        self.on_select = on_select
        self.on_double_click = on_double_click

        self.cards = []
        self.current_page = 0
        self.selected_card_id = None
        self.render_generation = 0
        self.card_widgets = {}

        self.gallery_frame = tk.Frame(self)
        self.gallery_frame.pack(side="top", fill="both", expand=True)

        for column in range(self.COLUMNS):
            self.gallery_frame.columnconfigure(column, weight=1, uniform="gallery")

        self.pagination_frame = tk.Frame(self)
        self.pagination_frame.pack(side="bottom", fill="x", pady=(8,10))

        self.prev_button = ttk.Button(self.pagination_frame, text="◀", command=self.previous_page)
        self.prev_button.pack(side="left")

        self.page_label = tk.Label(self.pagination_frame, font=("Tahoma", 11))
        self.page_label.pack(side="left", expand=True)

        self.next_button = ttk.Button(self.pagination_frame, text="▶", command=self.next_page)
        self.next_button.pack(side="right")

        self.render_page()

    def set_cards(self, cards, preserve_selection=False):
        previous_id = (self.selected_card_id if preserve_selection else None)
        self.cards = list(cards)
        self.current_page = 0
        self.selected_card_id = None

        if previous_id is not None:
            for index, card in enumerate(self.cards):
                if card[0] == previous_id:
                    self.selected_card_id = previous_id
                    self.current_page = index // self.PAGE_SIZE
                    break

        self.render_page()

    def get_total_pages(self):
        return max(1, (len(self.cards) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def render_page(self):
        self.render_generation += 1
        generation = self.render_generation

        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        self.card_widgets.clear()
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE

        page_cards = self.cards[start:end]
        for index, card in enumerate(page_cards):
            card_id, card_name = card[:2]

            row = index // self.COLUMNS
            column = index % self.COLUMNS
            self.render_card(card_id, card_name, row, column, generation)

        total_pages = self.get_total_pages()
        self.page_label.config(text=f"{self.current_page + 1} / {total_pages}")
        state = "normal" if total_pages > 1 else "disabled"

        self.prev_button.config(state=state)
        self.next_button.config(state=state)

    def render_card(self, card_id, card_name, row, column, generation):
        cell = tk.Frame(
            self.gallery_frame,
            width=self.CELL_WIDTH,
            height=self.CELL_HEIGHT,
            bg="#e8e8e8",
            highlightbackground="#b0b0b0",
            highlightthickness=2,
            cursor="hand2")

        cell.grid(row=row, column=column, padx=6, pady=5, sticky="n")
        cell.pack_propagate(False)

        image_label = tk.Label(cell, bg="#e8e8e8", cursor="hand2")
        image_label.pack(pady=(5, 3))

        name_label = tk.Label(
            cell,
            text=card_name,
            font=("Tahoma", 11),
            wraplength=self.CELL_WIDTH - 12,
            justify="center",
            bg="#e8e8e8",
            cursor="hand2"
        )
        name_label.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.card_widgets[card_id] = cell

        for widget in (cell, image_label, name_label):
            widget.bind("<Button-1>", lambda event, cid=card_id: self.select_card(cid))
            widget.bind("<Double-Button-1>", lambda event, cid=card_id: self.open_card(cid))

        if card_id == self.selected_card_id:
            self.highlight_card(card_id)

        placeholder = self.image_handler.get_placeholder(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        image_label.config(image=placeholder)
        image_label.image = placeholder

        def on_image_loaded(loaded_id, tk_img):
            if generation != self.render_generation:
                return

            if not image_label.winfo_exists():
                return

            if loaded_id != card_id:
                return

            if tk_img is not None:
                image_label.config(image=tk_img)
                image_label.image = tk_img

        self.image_handler.load_thumbnail_async(self, card_id, self.THUMB_WIDTH, self.THUMB_HEIGHT, on_image_loaded)

    def highlight_card(self, card_id):
        for cid, cell in self.card_widgets.items():
            selected = cid == card_id

            cell.config(bg="#dbeafe" if selected else "#e8e8e8", highlightbackground=("#2563eb" if selected else "#b0b0b0"))

            for child in cell.winfo_children():
                child.config(bg="#dbeafe" if selected else "#e8e8e8")

    def select_card(self, card_id):
        self.selected_card_id = card_id
        self.highlight_card(card_id)

        if self.on_select:
            self.on_select(card_id)

    def open_card(self, card_id):
        self.select_card(card_id)

        if self.on_double_click:
            self.on_double_click(card_id)

    def next_page(self):
        total_pages = self.get_total_pages()
        if total_pages <= 1:
            return

        self.current_page = (self.current_page + 1) % total_pages
        self.render_page()

    def previous_page(self):
        total_pages = self.get_total_pages()
        if total_pages <= 1:
            return

        self.current_page = (self.current_page - 1) % total_pages
        self.render_page()