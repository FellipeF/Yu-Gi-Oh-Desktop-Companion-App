import tkinter as tk
from tkinter import ttk

class DownloadingDialog(tk.Toplevel):
    def __init__(self, parent, title, status):
        super().__init__(parent)

        self.title(title)
        self.resizable(False, False)

        self.status_label = tk.Label(self, text=status, font=("Tahoma", 11))
        self.status_label.pack(padx=20, pady=(20,0))

        self.progress_var = tk.DoubleVar(value=0)

        self.progress_bar = ttk.Progressbar(
            self,
            variable = self.progress_var,
            maximum=100,
            length=350,
            mode="determinate"
        )
        self.progress_bar.pack(padx=20, pady=(0,8))

        self.percent_label=tk.Label(self, text="0.0%")
        self.percent_label.pack(pady=(0,20))

        self.transient(parent)
        self.grab_set()

        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

    def set_progress(self, progress):
        self.progress_var.set(progress)
        self.percent_label.config(text=f"{progress:.1f}%")
        self.update_idletasks()

    def set_indeterminate(self):
        """Edge case when no content length is informed by server."""
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)
        self.percent_label.config(text="")