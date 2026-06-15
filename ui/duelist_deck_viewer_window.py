import tkinter as tk

from frames.duelist_deck_viewer_frame import DuelistDeckViewerFrame

class DuelistDeckViewerWindow(tk.Toplevel):
    def __init__(self, parent, controller, duelist_id, duelist_key, deck_data):
        super().__init__(parent)

        self.controller = controller
        self.title(deck_data["deck_name"])
        self.geometry("950x760")
        self.resizable(False, False)

        content = DuelistDeckViewerFrame(self, controller, duelist_id, duelist_key, deck_data)
        content.pack(fill="both", expand=True)