import tkinter as tk

from frames.duelist_details_frame import DuelistDetailsFrame

class DuelistDetailsWindow(tk.Toplevel):
    def __init__(self, controller, duelist_id, duelist_key, duelist_name):
        super().__init__(controller)

        self.controller = controller
        self.title(f"{duelist_name}")
        self.geometry("900x800")
        self.minsize(800,800)

        content = DuelistDetailsFrame(self, controller)
        content.pack(fill="both", expand=True)
        content.set_duelist(duelist_id, duelist_key, duelist_name)

        self.focus()