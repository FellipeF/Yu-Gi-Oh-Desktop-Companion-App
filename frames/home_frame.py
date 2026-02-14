import tkinter as tk

class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="Welcome to Yu-Gi-Oh! Offline Database", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Check Available Cards", command=lambda: controller.show_frame("CardsFrame")).pack(pady=10)
        #tk.Button(self,text="Duelists").pack(pady=10)
        #tk.Button(self, text="Meus Decks").pack(pady=10)
