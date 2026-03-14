import tkinter as tk
from PIL import Image, ImageTk
import threading
from utils import cache_image
from database.queries import get_card_details

"""Controls window that is displayed when "show cards details" button is pressed. Since the button is disabled when
there's no TCG correspondence, no need to check here if card exists in the API or not."""

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

        self.description_label = tk.Label(self, wraplength=520, justify="left", font=("Tahoma", 12))
        self.description_label.pack(padx=12, pady=(0, 12), fill="x")

        self.refresh_ui()

        self.after(10, self.center_on_screen)

    def _translate_card_type(self, card_type: str) -> str:
        """Translate card_type label on the UI"""
        card_type = card_type

        if "Spell" in card_type:
            return self.controller.t("spell_card")

        if "Trap" in card_type:
            return self.controller.t("trap_card")

        return card_type

    def _format_stats(self, card_type: str, atk: int | None, defense: int | None) -> str:
        """Format stats according to card type."""
        # Magic/Trap don't have ATK or DEF
        # Link don't have DEF
        # Some Egyptian Gods have ??? as ATK and DEF, this is already normalized when seeding cards

        card_type = card_type

        is_spell = "Spell" in card_type
        is_trap = "Trap" in card_type
        is_link = "Link" in card_type

        if is_spell or is_trap:
            return self._translate_card_type(card_type)

        atk_text = "???" if atk is None else str(atk)

        if is_link:
            return f"ATK: {atk_text}"

        def_text = "???" if defense is None else str(defense)
        return f"ATK: {atk_text} | DEF: {def_text}"

    def refresh_ui(self):
        lang = self.controller.current_language
        row = get_card_details(self.card_id, lang)

        card_id, name, description, atk, defense, card_type = row
        self.name_label.config(text=name)
        self.title(name)
        self.stats_label.config(text=self._format_stats(card_type, atk, defense))
        self.description_label.config(text=description)

        self.image_label.config(image="")
        threading.Thread(
            target=self.load_image_async,
            args=(self.card_id,),
            daemon=True).start()

    def load_image_async(self, card_id: int):
        img_path = cache_image.get_card_image(card_id)

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