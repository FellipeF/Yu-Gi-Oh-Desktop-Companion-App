import os
import requests
from config import IMG_FOLDER

def get_card_image(card_id):
    """Fetches currently selected card image from the API"""
    #exist_ok prevents OSError when fetching images
    os.makedirs(IMG_FOLDER, exist_ok = True)

    local_path = os.path.join(IMG_FOLDER, f"{card_id}.jpg")

    if os.path.exists(local_path):
        return local_path

    url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None
    # If offline, could return None
    try:
        with open (local_path, "wb") as f:
            f.write(response.content)
        return local_path
    except Exception:
        return None