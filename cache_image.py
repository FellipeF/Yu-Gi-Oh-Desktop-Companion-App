import os
import requests

IMG_FOLDER = "images/cards"

def get_card_image(card_id):
    #exist_ok prevents OSError when fetching images
    os.makedirs(IMG_FOLDER, exist_ok = True)

    local_path = os.path.join(IMG_FOLDER, f"{card_id}.jpg")

    if os.path.exists(local_path):
        return local_path

    url = f"https://images.ygoprodeck.com/images/cards_small/{card_id}.jpg"

    response = requests.get(url)
    if response.status_code == 200:
        with open (local_path, "wb") as f:
            f.write(response.content)
        return local_path

    return None
