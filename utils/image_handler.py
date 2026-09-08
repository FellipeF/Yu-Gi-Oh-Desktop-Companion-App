from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from PIL import ImageTk, Image
from utils.card_image_loader import load_card_pil_image
from utils.resource_path import resource_path

class ImageHandler:

    MAX_CARD_CACHE = 60
    MAX_THUMBNAIL_CACHE = 60

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
        self.cache = OrderedDict()
        self.thumbnail_cache = OrderedDict() # For duelist details image miniatures
        self.placeholder_cache = {}

        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="image-loader")

        self._initialized = True

    def get_placeholder(self, width, height):
        cache_key = (width, height)

        if cache_key not in self.placeholder_cache:
            img = Image.open(resource_path("images/card_placeholder.jpg")).resize((width, height))
            self.placeholder_cache[cache_key] = ImageTk.PhotoImage(img)

        return self.placeholder_cache[cache_key]

    def get_card(self, card_id):
        if card_id not in self.cache:
            return None

        self.cache.move_to_end(card_id)

        return self.cache[card_id]

    def load_async(self, tk_widget, card_id, callback):
        if card_id in self.cache:
            self.cache.move_to_end(card_id)
            # Loads from memory cache
            tk_widget.after(0, lambda: callback(card_id, self.cache[card_id]))
            return

        def task():
            pil_img = load_card_pil_image(card_id, self.width, self.height)

            tk_widget.after(0, lambda: self._handle_image(card_id, pil_img, callback))

        self.executor.submit(task)

    def _handle_image(self, card_id, pil_img, callback):
        if pil_img is None:
            callback(card_id, None)
            return

        try:
            tk_img = ImageTk.PhotoImage(pil_img)
            self.cache[card_id] = tk_img
            self.cache.move_to_end(card_id)
            while len(self.cache) > self.MAX_CARD_CACHE:
                self.cache.popitem(last=False)

            callback(card_id, tk_img)

        except Exception:
            callback(card_id, None)

    def load_thumbnail_async(self, tk_widget, card_id, width, height, callback):
        cache_key = (card_id, width, height)

        if cache_key in self.thumbnail_cache:
            self.thumbnail_cache.move_to_end(cache_key)
            tk_widget.after(0, lambda: callback(card_id, self.thumbnail_cache[cache_key]))
            return

        def task():
            pil_img = load_card_pil_image(card_id, width, height)

            if not tk_widget.winfo_exists():
                return

            tk_widget.after(
                0,
                lambda: self._handle_thumbnail_image(cache_key, card_id, pil_img, callback)
            )

        self.executor.submit(task)

    def _handle_thumbnail_image(self, cache_key, card_id, pil_img, callback):
        if pil_img is None:
            callback(card_id, None)
            return

        try:
            tk_img = ImageTk.PhotoImage(pil_img)
            self.thumbnail_cache[cache_key] = tk_img
            self.thumbnail_cache.move_to_end(cache_key)
            while len(self.thumbnail_cache) > self.MAX_THUMBNAIL_CACHE:
                self.thumbnail_cache.popitem(last=False)

            callback(card_id, tk_img)

        except Exception:
            callback(card_id, None)