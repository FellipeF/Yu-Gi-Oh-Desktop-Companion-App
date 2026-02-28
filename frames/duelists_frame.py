import tkinter as tk
from PIL import Image, ImageTk
from database.models import get_all_duelists
from utils.resource_path import resource_path

class DuelistsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.duelists = get_all_duelists()
        self.current_page = 0
        self.items_per_page = 9

        self.select_duelist_label = tk.Label(self, font=("Arial", 16))
        self.select_duelist_label.pack(pady=10)

        self.container = tk.Frame(self)
        self.container.pack()

        #TODO: Sort by anime

        self.footer = tk.Frame(self)
        self.footer.pack(side="bottom", fill="x")

        self.footer.columnconfigure(0, weight=1)
        self.footer.columnconfigure(1, weight=1)
        self.footer.columnconfigure(2, weight=1)

        self.prev_button = tk.Button(
            self.footer,
            text="←",
            font=("Arial", 12),
            command=self.prev_page
        )
        self.prev_button.grid(row=0, column=0, sticky="w", padx=20)

        self.return_button = tk.Button(
            self.footer,
            command=lambda: controller.show_frame("HomeFrame")
        )
        self.return_button.grid(row=0, column=1)

        self.next_button = tk.Button(
            self.footer,
            text="→",
            font=("Arial", 12),
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
            duelist_id, name, img_path = duelist

            img = Image.open(resource_path(img_path)).resize((150,150))
            tk_img = ImageTk.PhotoImage(img)

            duelist_button = tk.Button(
                self.container,
                image=tk_img,
                text=name,
                font=("Arial",15),
                compound="top",
                command=lambda d=duelist_id, n=name: self.show_duelist_details(d, n)
            )

            duelist_button.image = tk_img
            duelist_button.grid(row=row, column=col, padx=20, pady=20)

            col+=1
            if col == 3:
                col = 0
                row +=1

        self.prev_button.config(state="disabled" if self.current_page == 0 else "normal")
        is_last_page = (self.current_page + 1) * self.items_per_page >= len(self.duelists)
        self.next_button.config(state="disabled" if is_last_page else "normal")

    def next_page(self):

        if (self.current_page + 1) * self.items_per_page < len(self.duelists):
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()


    def show_duelist_details(self, duelist_id, duelist_name):
        detail_frame = self.controller.frames["DuelistDetailsFrame"]
        detail_frame.set_duelist(duelist_id, duelist_name)
        self.controller.show_frame("DuelistDetailsFrame")

    def refresh_ui(self):
        self.select_duelist_label.config(text=self.controller.t("select_duelist"))
        self.return_button.config(text=self.controller.t("return"))