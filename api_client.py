import requests
import json
import os

URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt"
CACHE = "cards.json"

def download_cards():
    #Message to user here
    print("Downloading data from API...")
    response = requests.get(URL)
    data = response.json()

    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return data

def load_cards():
    if os.path.exists(CACHE):
        #Message to User Here
        print("Opening Cached File...")
        with open(CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return download_cards()