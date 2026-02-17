import tkinter as tk

class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.title_label = tk.Label(self, font=("Arial", 16))
        self.title_label.pack(pady=20)

        self.cards_button = tk.Button(
            self,
            command=lambda: controller.show_frame("CardsFrame")
        )
        self.cards_button.pack(pady=10)

        self.duelists_button = tk.Button(
            self,
            command=lambda: controller.show_frame("DuelistsFrame")
        )
        self.duelists_button.pack(pady=10)

        self.refresh_ui()

        #TODO: My Decks btn and Frame. This Frame allow user to create and check their created decks, with the option to export it as a .json File.

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("home_title"))
        self.cards_button.config(text=self.controller.t("check_cards"))
        self.duelists_button.config(text=self.controller.t("duelists"))
