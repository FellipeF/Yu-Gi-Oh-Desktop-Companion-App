from PIL import Image, ImageTk
from utils import cache_image

def load_card_pil_image(card_id, width, height):
    """Returns resized PIL of card_image."""

    img_path = cache_image.get_card_image(card_id)

    if not img_path:
        return None

    return Image.open(img_path).resize((width, height))
