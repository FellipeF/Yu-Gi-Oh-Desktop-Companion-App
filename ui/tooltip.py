import tkinter as tk

class Tooltip(tk.Toplevel):
    def __init__(self, widget):
        super().__init__(widget)
        self.withdraw()
        self.overrideredirect(True)
        self.label = tk.Label(self, text="", bg="#ffffe0", relief="solid", borderwidth=1)
        self.label.pack()

    def show(self, text, x, y):
        self.label.config(text=text)
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        self.withdraw()