import tkinter as tk
from PIL import Image, ImageTk
from database.queries import get_all_duelists
from ui.duelist_details_window import DuelistDetailsWindow
from utils.resource_path import resource_path

class DuelistsFrame(tk.Frame):
    def __init__(self, parent, controller):
        """List of all duelists by alphabetical order based on their display name available on the ui_text.py file"""
        super().__init__(parent)
        self.controller = controller

        self.duelists = get_all_duelists()
        self.sort_duelists()
        self.current_page = 0
        self.items_per_page = 8

        self.select_duelist_label = tk.Label(self, font=("Arial", 16))
        self.select_duelist_label.pack(pady=10)

        self.container = tk.Frame(self, width=self.controller.app_width, height=505)
        self.container.pack(fill="both", expand=True)
        self.container.pack_propagate(False)

        for c in range (4):
            self.container.columnconfigure(c, weight=1, uniform="col")

        #TODO: Order by anime

        self.footer = tk.Frame(self)
        self.footer.pack(side="bottom", fill="x")

        self.footer.columnconfigure(0, weight=1)
        self.footer.columnconfigure(1, weight=1)
        self.footer.columnconfigure(2, weight=1)

        self.prev_button = tk.Button(
            self.footer,
            text="←",
            font=("Tahoma", 12),
            command=self.prev_page
        )
        self.prev_button.grid(row=0, column=0, sticky="w", padx=20)

        self.return_button = tk.Button(
            self.footer,
            font=("Tahoma", 12),
            command=lambda: controller.show_frame("HomeFrame")
        )
        self.return_button.grid(row=0, column=1, pady=2)

        self.next_button = tk.Button(
            self.footer,
            text="→",
            font=("Tahoma", 12),
            command=self.next_page
        )
        self.next_button.grid(row=0, column=2, sticky="e", padx=20)

        self.render_page()
        self.refresh_ui()

    def render_page(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_duelists = self.duelists[start:end]

        row = 0
        col = 0

        for duelist in page_duelists:
            duelist_id, duelist_key, img_path, media, deck_count = duelist

            img = Image.open(resource_path(img_path)).resize((200,200))
            tk_img = ImageTk.PhotoImage(img)

            cell = tk.Frame(self.container, width=210, height=250)
            cell.grid(row=row,column=col,padx=25, pady=25, sticky="n")
            cell.grid_propagate(False)

            duelist_button = tk.Button(
                cell,
                image=tk_img,
                text=f"{self.truncate(self.controller.t(duelist_key), 14)}\n({deck_count})",
                font=("Arial",15),
                compound="top",
                wraplength=160,
                command=lambda d=duelist_id, k=duelist_key: self.show_duelist_details(d,k)
            )

            duelist_button.image = tk_img
            duelist_button.pack(fill="both", expand=True)

            col+=1
            if col == 4:
                col = 0
                row +=1

        self.prev_button.config(state="disabled" if self.current_page == 0 else "normal")
        is_last_page = (self.current_page + 1) * self.items_per_page >= len(self.duelists)
        self.next_button.config(state="disabled" if is_last_page else "normal")

    def truncate(self, text, max_chars):
        """Truncate character names if it exceeds certain limit"""
        return text if len(text) <= max_chars else text[:max_chars - 1] + "..."

    def next_page(self):
        # Calculates how many duelists are there to see if there's still a next page
        # Disables button if it's the last page
        if (self.current_page + 1) * self.items_per_page < len(self.duelists):
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        # Disables button if it's the first page
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def sort_duelists(self):
        """Sorts duelist by Display name that is handled by the translation file."""
        self.duelists.sort(
            key = lambda d: self.controller.t(d[1]).casefold()
        )

    def show_duelist_details(self, duelist_id, duelist_key):
        DuelistDetailsWindow(self.controller, duelist_id, duelist_key)

    def refresh_ui(self):
        self.select_duelist_label.config(text=self.controller.t("select_duelist"))
        self.return_button.config(text=self.controller.t("return"))
        self.sort_duelists()
        self.render_page()
