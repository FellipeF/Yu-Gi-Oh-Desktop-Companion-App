import tkinter as tk
from frames.home_frame import HomeFrame
from frames.cards_frame import CardsFrame
from database.database import create_tables
from database.models import populate_cards

#TODO: SOME TODOS BELOW:
#TODO: Disable Resize
#TODO: Add Scroll Bar
#TODO: Limit Results, Implement Pagination
#TODO: Requirements.txt
#TODO: END TODO LIST HERE

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        create_tables()
        populate_cards()

        self.title("Yu-Gi-Oh! Card Database v0.2")
        self.geometry("620x500")

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