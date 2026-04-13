"""Fetches cards and their details from the YGOProDeck Dataset and checks Database version from endpoint."""
import requests
import json
import os
from typing import Any, Dict, Optional
from datetime import date, datetime

URL_CARDS = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
URL_VERSION = "https://db.ygoprodeck.com/api/v7/checkDBVer.php"

#----------------------------------------------------- IMPORTANT -------------------------------------------------------
# The checkDBVer endpoint is written as follows:                                                                       #
#[                                                                                                                     #
#    {                                                                                                                 #
#        "database_version": "144.17",                                                                                 #
#        "last_update": "2026-03-04 09:22:52"                                                                          #
#    }                                                                                                                 #
#]                                                                                                                     #
# As to not mix things up between the actual database being modeled on this app, I refer to that as a *dataset*        #
# instead,but still call database_version whenever I'm referring to this file in particular.                           #
#-----------------------------------------------------------------------------------------------------------------------

def _check_created_dir(path:str) -> None:
    """Create directory if it doesn't already exist"""
    os.makedirs(path, exist_ok = True)

class ApiClient:
    def __init__(self, cache_directory: str = "cache") -> None:
        self.cache_directory = cache_directory
        _check_created_dir(self.cache_directory)

    def _cards_cache_path(self, language: str) -> str:
        """Returns cards dataset JSON file location. This takes a language as a parameter since each language on the
        dataset has its own URL with a JSON."""
        return os.path.join(self.cache_directory, f"cards_{language}.json")

    def _info_file_path(self) -> str:
        """Returns database info file location. Contrary to previous method, we don't take language since
        the dataset updates whenever any language is updated."""
        return os.path.join(self.cache_directory, "cards_info.json")

    def _write_json_file(self, path: str, data: Dict[str, Any], indent: Optional[int] = None) -> None:
        """Helper to write JSON File"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    def _read_json_file(self, path: str) -> Dict[str, Any]:
        """Helper to read JSON File"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_info_file(self, meta: Dict[str, Any]) -> None:
        """Writes current dataset_version on a JSON File."""
        self._write_json_file(self._info_file_path(), meta, indent=2)

    def read_info_file(self) -> Optional[Dict[str, Any]]:
        """Reads the current version of the dataset info file. In case it's missing, we return None"""
        path = self._info_file_path()
        if not os.path.exists(path):
            return {}   # Prevents attribute error. Do this instead of None
        try:
            return self._read_json_file(path)
        except Exception:
            return {}

    def _today(self) -> str:
        return date.today().isoformat()

    def get_dataset_details(self) -> Dict[str, Any]:
        """Gets dataset details from Endpoint"""
        r = requests.get(URL_VERSION, timeout = 20)
        r.raise_for_status()
        data = r.json()[0]
        last_update = data.get("last_update")

        if last_update:
            try:
                dt = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
                data["last_update"] = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return data

    def download_cards(self, language:str="en") -> Dict[str,Any]:
        """Downloads cards dataset for a given language (defaults english) and updates local cache. There's no parameter
        for the english version URL of the dataset."""
        params = {} if language == "en" else {"language": language}
        response = requests.get(URL_CARDS, params=params, timeout=60)
        response.raise_for_status()

        data: Dict[str, Any] = response.json()
        self._write_json_file(self._cards_cache_path(language), data)

        return data

    def load_cards(self, language: str="en") -> Dict [str, Any]:
        """Load cards from cache.If the file doesn't exist, it means we're starting the program for the first time
        or it was deleted. In both cases, download the dataset. A new data set version is checked every day"""
        cards_cache_path = self._cards_cache_path(language)

        all_info = self.read_info_file()
        all_info = self._normalize_info_schema(all_info)

        if "new_cards" not in all_info:
            all_info["new_cards"] = []

        lang_info = all_info.get(language, {})
        today = self._today()

        if not os.path.exists(cards_cache_path):
            new_data = self.download_cards(language)
            db_details = self.get_dataset_details()

            all_info[language] = {
                "database_version": db_details.get("database_version"),
                "last_checked": today,
                "last_update": db_details.get("last_update"),
                "database_offline_version": None
            }

            all_info.setdefault("new_cards", [])

            self.write_info_file(all_info)

            return new_data

        if lang_info.get("last_checked") == today and lang_info.get("database_version"):
            return self._read_json_file(cards_cache_path)

        try:
            db_details = self.get_dataset_details()
            online_version = db_details.get("database_version")
            local_version = lang_info.get("database_version") or all_info.get("database_version")

            if local_version != online_version:
                old_data = self._read_json_file(cards_cache_path)
                new_data = self.download_cards(language)

                new_cards = self.get_new_cards(old_data, new_data)
                new_cards_ids = [card["id"] for card in new_cards]

                # When changing language, assures that new cards from current language don't overwrite new ones from
                # previous language
                existing = set(all_info.get("new_cards", []))
                existing.update(new_cards_ids)
                all_info["new_cards"] = list(existing)
            else:
                new_data = self._read_json_file(cards_cache_path)

            all_info[language] = {
                "database_version": online_version,
                "last_checked": today,
                "last_update": db_details.get("last_update"),
                "database_offline_version": lang_info.get("database_offline_version")
            }

            self.write_info_file(all_info)

            return new_data

        except requests.RequestException:
            return self._read_json_file(cards_cache_path)

    def _normalize_info_schema(self, all_info: Dict[str, Any]) -> Dict[str, Any]:
        """Migrates schema from old .json cards_info to the new expected one"""
        # Already normalized, grants that new_cards key exists in case anything goes wrong.
        if "en" in all_info:
            all_info.setdefault("new_cards", [])
            return all_info

        # Are we in the old version still?
        if "database_version" in all_info:
            all_info["en"] = {
                "database_version": all_info.get("database_version"),
                "last_checked": all_info.get("last_checked"),
                "last_update": all_info.get("last_update"),
                "database_offline_version": all_info.get("database_offline_version")
            }

        for key in ["database_version", "last_checked", "last_update", "database_offline_version"]:
            all_info.pop(key, None)

        all_info.setdefault("new_cards", [])

        return all_info

    def get_new_cards(self, old_data:dict, new_data: dict) -> list [dict]:
        "Checks what are the new cards on the online dataset"
        old_ids = {card["id"] for card in old_data.get("data", [])}
        new_cards = []

        for card in new_data.get("data", []):
            if card["id"] not in old_ids:
                new_cards.append(card)

        return new_cards