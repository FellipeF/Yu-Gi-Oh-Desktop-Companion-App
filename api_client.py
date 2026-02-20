import requests
import json
import os

#TODO: Check for Updates

URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"

def get_cache_filename(language):
    return f"cards_{language}.json"

def download_cards(language="en"):
    #TODO: Message to user here
    #print("Downloading data from API...")

    if language == "en":
        response = requests.get(URL)
    else:
        params = {"language": language}
        response = requests.get(URL, params=params)

    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}")

    data = response.json()
    cache = get_cache_filename(language)

    with open(cache, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return data

def load_cards(language="en"):
    cache = get_cache_filename(language)
    if os.path.exists(cache):
        #TODO: Message to User here as well?
        print(f"Opening {language} Cached File...")
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return download_cards(language)