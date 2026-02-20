import tkinter as tk
from frames.home_frame import HomeFrame
from frames.cards_frame import CardsFrame
from frames.duelists_frame import DuelistsFrame
from frames.duelist_details_frame import DuelistDetailsFrame
from database.database import create_tables
from database.models import populate_cards
from database.models import populate_duelists
from database.models import populate_decks_and_cards
from database.models import populate_deck_type_translations
from database.models import populate_deck_translations
from ui.translations import translations

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # =========================
        # LANGUAGE
        # =========================

        #TODO: User Start App on his native language, DB is already protected for it. Current OS Language? User chooses first? Leave this as it is?
        self.current_language = "en"
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x")
        self.language_var = tk.StringVar(value="en")
        self.language_label = tk.Label(top_bar)
        self.language_label.pack(side="left", padx=5)

        tk.OptionMenu(
            top_bar,
            self.language_var,
            "en",
            "pt",
            command=self.change_language
        ).pack(side="left")

        #TODO: Button to read the CFF - Card Consistency File in /docs folder

        # =========================
        # DATABASE
        # =========================

        create_tables()
        populate_cards(self.current_language)
        populate_duelists()
        populate_decks_and_cards()
        populate_deck_type_translations()
        populate_deck_translations()

        # =========================
        # MAIN WINDOW
        # =========================

        #TODO: Check if there's a method to generate window on the center of the user screen

        self.title("Yu-Gi-Oh! Card Database v0.6")
        self.geometry("620x500")
        self.resizable(False, False)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        #TODO: Create CardDetailsFrame that is shared between CardsFrame and DuelistDetailsFrame - User can see card details when it is selected.
        for F in (HomeFrame, CardsFrame, DuelistsFrame, DuelistDetailsFrame):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.update_ui_language()
        self.show_frame("HomeFrame")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

    def change_language(self, lang):
        self.current_language = lang
        populate_cards(lang)

        self.update_ui_language()
        #In case user knows the name only in the original version, allow to search for the card and preserve his selection.
        self.frames["CardsFrame"].load_cards(preserve_selection=True)

    def update_ui_language(self):
        self.language_label.config(text=self.t("language"))

        for frame in self.frames.values():
            if hasattr(frame, "refresh_ui"):
                frame.refresh_ui()

            if hasattr(frame, "load_duelist") and frame.current_duelist_id:
                frame.load_duelist()

    def t (self, key):
        return translations[self.current_language][key]

if __name__ == "__main__":
    app = App()
    app.mainloop()