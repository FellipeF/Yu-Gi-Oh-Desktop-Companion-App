import tkinter as tk


class TreeviewTooltip:
    def __init__(self, tree, tooltips):
        self.tree = tree
        self.tooltips = tooltips
        self.tipwindow = None
        self.current_column = None

        self.tree.bind("<Motion>", self.on_motion, add="+")
        self.tree.bind("<Leave>", self.hide_tooltip, add="+")

    def on_motion(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        if region != "cell" or not row or column not in self.tooltips:
            self.current_column = None
            self.hide_tooltip()
            return

        if column == self.current_column:
            return

        self.current_column = column
        self.show_tooltip(event.x_root, event.y_root, self.tooltips[column])

    def show_tooltip(self, x, y, text):
        self.hide_tooltip()

        self.tipwindow = tk.Toplevel(self.tree)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x + 12}+{y + 12}")

        label = tk.Label(
            self.tipwindow,
            text=text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Tahoma", 9),
            padx=6,
            pady=3
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None