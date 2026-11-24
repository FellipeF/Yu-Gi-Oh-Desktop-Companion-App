import logging

from PIL import Image
from utils import cache_image

logger = logging.getLogger(__name__)

def load_card_pil_image(card_id, width, height) ->Image.Image | None:
    """Loads and resize a card image"""

    img_path = cache_image.get_card_image(card_id)

    if not img_path:
        return None

    try:
        with Image.open(img_path) as img:
            return img.resize((width, height))

    except (OSError, ValueError) as exc:
        logger.warning("Could not process card image %s: %s", card_id, exc)
        return None
