import threading

from PIL import ImageTk, Image
from config import CARD_WIDTH, CARD_HEIGHT
from utils.card_image_loader import load_card_pil_image
from utils.resource_path import resource_path

class ImageHandler:

    _instance = None

    def __new__(cls, width=None, height=None, placeholder=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, width=None, height=None, placeholder=None):
        """Implements Singleton and handles Image processing, loading and caching from memory on the app."""
        if self._initialized:
            return

        self.width = width
        self.height = height
        self.cache = {}
        self.placeholder = None #Prevent Exception: Too early to create image: no default root window on Card Details Window

        self._initialized = True

    def get_placeholder(self, width, height):
        if self.placeholder is None: # Assures that the Tk is already initialized
            img = Image.open(resource_path("images/placeholder.jpg")).resize((width, height))
            self.placeholder = ImageTk.PhotoImage(img)

        return self.placeholder

    def get_card(self, card_id):
        return self.cache.get(card_id)

    def load_async(self, tk_widget, card_id, callback):
        if card_id in self.cache:
            # Loads from memory cache
            tk_widget.after(0, lambda: callback(card_id, self.cache[card_id]))
            return

        def task():
            pil_img = load_card_pil_image(card_id, self.width, self.height)

            tk_widget.after(0, lambda: self._handle_image(card_id, pil_img, callback))

        threading.Thread(target=task, daemon=True).start()

    def _handle_image(self, card_id, pil_img, callback):
        if pil_img is None:
            callback(card_id, None)
            return

        try:
            tk_img = ImageTk.PhotoImage(pil_img)
            self.cache[card_id] = tk_img
            callback(card_id, tk_img)
        except Exception:
            callback(card_id, None)