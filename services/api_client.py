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
        return os.path.join(self.cache_directory, "cards.info.json")

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
            return None
        try:
            return self._read_json_file(path)
        except Exception:
            return None

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
        today = self._today()

        data: Dict[str, Any] = response.json()
        self._write_json_file(self._cards_cache_path(language), data)

        try:
            db_details = self.get_dataset_details()
            local_info = self.read_info_file()
            info = local_info.copy() if local_info else {}

            info["database_version"] = db_details.get("database_version")
            info["last_checked"] = today
            info["last_update"] = db_details.get("last_update")
            self.write_info_file(info)

        except requests.RequestException:
            pass

        return data

    def load_cards(self, language: str="en", force_refresh: bool = False) -> Dict [str, Any]:
        """Load cards from cache. When force_refresh is enabled, it checks if the YGOPro Database version has changed.
        If the file doesn't exist, it means we're starting the program for the first time or it was deleted.
        In both cases, download the dataset. A new data set version is checked every day"""
        cards_cache_path = self._cards_cache_path(language)

        if force_refresh or not os.path.exists(cards_cache_path):
            return self.download_cards(language)

        local_info = self.read_info_file()
        today = self._today()

        if local_info and local_info.get("last_checked") == today:
            return self._read_json_file(cards_cache_path)

        try:
            online_db_details = self.get_dataset_details()
            online_db_version = online_db_details.get("database_version")

            local_version = local_info.get("database_version") if local_info else None

            info = local_info.copy() if local_info else {}
            info["database_version"] = online_db_version
            info["last_checked"] = today
            self.write_info_file(info)

            if local_version != online_db_version:
                return self.download_cards(language)

        except requests.RequestException:
            pass

        return self._read_json_file(cards_cache_path)