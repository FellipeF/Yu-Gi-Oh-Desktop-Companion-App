"""Loading Screen Frame for when the API is checking for cards"""

import tkinter as tk
from tkinter import ttk

class LoadingFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.title_label = tk.Label(self, font=("Arial", 18, "bold"))
        self.title_label.pack(pady=(80,10))

        self.status_label = tk.Label(self, font=("Arial", 11))
        self.status_label.pack(pady=(0,20))

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=320)
        self.progress.pack(pady=10)

        self.tip_label = tk.Label(self, font=("Arial", 9))
        self.tip_label.pack(pady=(10,0))

        self.refresh_ui()

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("loading_title"))
        self.status_label.config(text=self.controller.t("loading_cards"))
        self.tip_label.config(text=self.controller.t("loading_tip"))

    def start(self):
        self.progress.start(12)

    def stop(self):
        self.progress.stop()

    def set_status(self, text:str):
        self.status_label.config(text=text)