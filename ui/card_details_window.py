import tkinter as tk
from PIL import Image, ImageTk
import threading
import cache_image
from database.models import get_card_details

class CardDetailsWindow(tk.Toplevel):
    def __init__(self, controller, card_id: int):
        super().__init__()

        self.controller = controller
        self.card_id = card_id
        self.tk_image = None
        self.resizable(False, False)

        self.name_label = tk.Label(self, font=("Arial", 16, "bold"))
        self.name_label.pack(pady=(10, 6), padx=12)

        img_container = tk.Frame(self, width=200, height=290)
        img_container.pack(pady=(0, 8))
        img_container.pack_propagate(False)

        self.image_label = tk.Label(img_container, text="", anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.stats_label = tk.Label(self, font=("Arial", 12))
        self.stats_label.pack(pady=(0, 8), padx=12)

        self.description_label = tk.Label(self, wraplength=520, justify="left")
        self.description_label.pack(padx=12, pady=(0, 12), fill="x")

        self.refresh_ui()

        self.after(10, self.center_on_screen)

    def refresh_ui(self):
        lang = self.controller.current_language
        row = get_card_details(self.card_id, language=lang)

        card_id, name, description, atk, defense, type = row
        self.name_label.config(text=name)
        self.title(name)

        #Magic/Trap cards
        if atk is None and defense is None:
            self.stats_label.config(text=type or "")
        else:
            #LINK, no DEF
            self.stats_label.config(
                text=f"ATK: {atk if atk is not None else '-'} | DEF: {defense if defense is not None else '-'}"
            )

        self.description_label.config(text=description)

        self.image_label.config(image="")
        threading.Thread(
            target=self.load_image_async,
            args=(self.card_id,),
            daemon=True).start()

    def load_image_async(self, card_id: int):
        img_path = cache_image.get_card_image(card_id)
        #Window is only available for TCG cards, so no need to check if Image exists to put a placeholder.

        img = Image.open(img_path).resize((200, 300))
        tk_img = ImageTk.PhotoImage(img)
        self.after(0, self.set_image, tk_img)

    def set_image(self, tk_img):
        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")

    def center_on_screen(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")