import tkinter as tk
from PIL import Image, ImageTk
from database.models import get_all_duelists
from utils.resource_path import resource_path

class DuelistsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self.select_duelist_label = tk.Label(self, font=("Arial", 16))
        self.select_duelist_label.pack(pady=10)

        container = tk.Frame(self)
        container.pack()

        duelists = get_all_duelists()
        #TODO: Sort by anime

        row = 0
        col = 0

        for duelist in duelists:
            duelist_id, name, img_path = duelist

            img = Image.open(resource_path(img_path)).resize((150,150))
            tk_img = ImageTk.PhotoImage(img)

            duelist_button = tk.Button(
                container,
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

        self.return_button = tk.Button(
            self,
            command=lambda: controller.show_frame("HomeFrame")
        )
        self.return_button.pack()

        self.refresh_ui()

    def show_duelist_details(self, duelist_id, duelist_name):
        detail_frame = self.controller.frames["DuelistDetailsFrame"]
        detail_frame.set_duelist(duelist_id, duelist_name)
        self.controller.show_frame("DuelistDetailsFrame")

    def refresh_ui(self):
        self.select_duelist_label.config(text=self.controller.t("select_duelist"))
        self.return_button.config(text=self.controller.t("return"))