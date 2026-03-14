"""Modal for when user is switching languages."""

import tkinter as tk
from tkinter import ttk

class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, title: str, status: str):
        super().__init__(parent)

        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.label = tk.Label(self, text=status, font=("Arial", 11))
        self.label.pack(padx=20, pady=(20, 10))

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=260)
        self.progress.pack(padx=20, pady=(0, 20))

        self.update_idletasks()
        self.center_over_parent(parent)

    def center_over_parent(self, parent):
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        width = self.winfo_width()
        height = self.winfo_height()

        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

    def start(self):
        self.progress.start(15)

    def stop(self):
        self.progress.stop()

    def set_status(self, text: str):
        self.label.config(text=text)