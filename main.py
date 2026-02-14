import tkinter as tk
from frames.home_frame import HomeFrame
from frames.cards_frame import CardsFrame

#TODO: SOME TODOS BELOW:
#TODO: Disable Resize
#TODO: Add Scroll Bar
#TODO: Limit Results, Implement Pagination
#TODO: END TODO LIST HERE

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yu-Gi-Oh! Card Database v0.1")
        self.geometry("600x500")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        for F in (HomeFrame, CardsFrame):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomeFrame")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()