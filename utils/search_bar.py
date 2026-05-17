import tkinter as tk

class SearchBar(tk.Frame):
    def __init__(
            self,
            parent,
            textvariable,
            placeholder,
            on_change,
            width = 40,
            font=("Tahoma", 12),
            icon = "🔎",
    ):
        super().__init__(parent)

        self.textvariable = textvariable
        self.placeholder = placeholder
        self.on_change = on_change
        self.placeholder_active = True

        self.icon_label = tk.Label(self, text=icon, font=("Segoe UI Emoji", 12))
        self.icon_label.pack(side="left", padx=(0,5))

        self.entry = tk.Entry(self, textvariable=self.textvariable, font=font, width=width)
        self.entry.pack(side="left")

        self.set_placeholder()

        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", self.restore_placeholder)
        self.entry.bind("<KeyRelease>", self.handle_change)

    def set_placeholder(self):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg="gray")
        self.placeholder_active = True

    def clear_placeholder(self, event=None):
        if self.placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.config(fg="black")
            self.placeholder_active = False

    def restore_placeholder(self, event=None):
        if not self.entry.get().strip():
            self.set_placeholder()
            self.on_change()

    def handle_change(self, event=None):
        if not self.placeholder_active:
            self.on_change()

    def get_text(self):
        if self.placeholder_active:
            return ""

        return self.textvariable.get().strip()