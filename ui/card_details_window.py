import tkinter as tk

from config import CARD_WIDTH, CARD_HEIGHT
from database.queries import get_card_details

class CardDetailsWindow(tk.Toplevel):
    def __init__(self, controller, card_id: int):
        """Controls window that is displayed when "show cards details" button is pressed. Since the button is disabled when
        there's no TCG correspondence, no need to check here if card exists in the API or not."""
        super().__init__()
        self.withdraw()

        self.controller = controller
        self.card_id = card_id
        self.tk_image = None
        self.image_handler = controller.image_handler
        self.resizable(False, False)

        self.name_label = tk.Label(self, font=("Arial", 16, "bold"))
        self.name_label.pack(pady=(10, 6), padx=12)

        self.subtitle_label = tk.Label(self, font=("Tahoma", 11))
        self.subtitle_label.pack(pady=(0, 6))

        img_container = tk.Frame(self, width=CARD_WIDTH, height=CARD_HEIGHT)
        img_container.pack(pady=(0, 8))
        img_container.pack_propagate(False)

        self.image_label = tk.Label(img_container, text="", anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.type_label = tk.Label(self, font=("Tahoma", 11, "bold"), anchor="w", justify="left")
        self.type_label.pack(fill="x", padx=12, pady=(0,4))

        self.description_label = tk.Label(self, wraplength=520, justify="left", anchor="w", font=("Tahoma", 12))
        self.description_label.pack(padx=12, pady=(0, 12), fill="x")

        self.stats_label = tk.Label(self, font=("Arial", 12, "bold"), anchor="e", justify="right")
        self.stats_label.pack(fill="x", padx=12, pady=(0,10))

        self.refresh_ui()
        self.update_idletasks()
        self.center_on_screen()
        self.deiconify()

    def _format_type_line(self, card_type, race):

        if "Spell" in card_type or "Trap" in card_type:
            return ""

        subtype = card_type.replace("Monster", "").strip()

        parts = []

        if race:
            parts.append(self.controller.t(race))

        if subtype:
            parts.append(self.controller.t(subtype))

        return f"[{'/'.join(parts)}]"

    def _format_stats(self, card_type: str, atk: int | None, defense: int | None, linkval = None) -> str:
        """Format stats according to card type."""
        # Magic/Trap/Skill cards don't have ATK or DEF
        # Link cards don't have DEF
        # Some Egyptian Gods cards have ??? as ATK and DEF, this is already normalized when seeding cards

        if not card_type:
            return ""

        is_spell = "Spell" in card_type
        is_trap = "Trap" in card_type
        is_link = "Link" in card_type
        is_skill = "Skill Card" in card_type

        if is_spell or is_trap or is_skill:
            return ""

        atk_text = "???" if atk is None else str(atk)

        if is_link:
            return f"ATK: {atk_text} | LINK-{linkval}" if linkval else f"ATK: {atk_text}"

        def_text = "???" if defense is None else str(defense)
        return f"ATK: {atk_text} | DEF: {def_text}"

    def refresh_ui(self):
        lang = self.controller.current_language
        row = get_card_details(self.card_id, lang)

        #TODO: Link Markers and Pendulum Scales

        (
            card_id,
            name,
            description,
            card_type,
            readable_type,
            race,
            attribute,
            atk,
            defense,
            level,
            scale,
            linkval,
            linkmarkers
        ) = row

        self.title(name)

        self.name_label.config(text=name)

        subtitle = self._format_subtitle(attribute, level, card_type, race)
        self.subtitle_label.config(text=subtitle)

        self.image_label.config(image="")
        self.image_handler.load_async(
            self,
            card_id,
            self._on_image_loaded
        )

        type_line = self._format_type_line(card_type, race)
        self.type_label.config(text=type_line)

        self.description_label.config(text=description)

        stats = self._format_stats(card_type, atk, defense, linkval)
        self.stats_label.config(text=stats)

    def _format_subtitle(self, attribute, level, card_type, race):
        parts = []

        if attribute:
            parts.append(self.controller.t(attribute))

        if level:
            parts.append(f"{level}⭐") #TODO: Different stars for the XYZ monsters

        if "Spell" in card_type or "Trap" in card_type or "Skill Card" in card_type:
            parts.append(self.controller.t(card_type))
            parts.append(self.controller.t(race)) #Continuous, quick-play, etc.

        return " | ".join(parts)

    def _on_image_loaded(self, card_id, tk_img):
        if card_id != self.card_id:
            return

        if tk_img is None:
            tk_img = self.image_handler.get_placeholder(CARD_WIDTH, CARD_HEIGHT)

        self.tk_image = tk_img
        self.image_label.config(image=self.tk_image, text="")
        self.image_label.image = self.tk_image

    def center_on_screen(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")